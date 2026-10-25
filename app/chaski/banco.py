"""The verified-phrase bank: hybrid retrieval (embeddings + lexical) and emergency mode.

What it is for (plan/arquitectura-interprete.md §4, barrier B7):
  - The interpreter gets the ~20 bank phrases closest to what the staff member said and, only when one has
    the SAME intent, answers `usar_frase_banco` with its id. Code proposes candidates; the model decides.
  - Emergency mode shows the `emergencia` phrases as buttons: tap and it plays. No model in the loop.

How retrieval works:
  - Embeddings: a small multilingual sentence model run locally through fastembed (ONNX, CPU, no paid API):
    `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384 dims, ~220 MB. It was trained on
    paraphrase pairs, which is exactly the job (a nurse's colloquial wording vs. the manual's wording), and it
    needs no "query:"/"passage:" prefixes. Only the Spanish side (`es`) is embedded.
  - Lexical: BM25-lite over accent-free, stopword-free, prefix-stemmed tokens, scaled to [0, 1] by the
    best score the query could get against itself.
  - Hybrid: PESO_EMBEDDING * coseno + PESO_LEXICO * lexico. The embedding carries the paraphrase signal;
    the lexical term breaks ties toward items that share the clinical keyword (cabeza vs. abdomen), which
    the embedding sometimes blurs. Weights were set before running the eval (0.7 / 0.3), not tuned on it.
  - Vectors: numpy cosine over a few hundred rows. No vector database; the bank is small.

Bank embeddings are cached in `banco.emb.npz` next to `banco.json`, keyed by a fingerprint of the model name
and every `es` string, so an edited bank invalidates the cache by itself.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Protocol

import numpy as np

AQUI = Path(__file__).resolve().parent
BANCO = AQUI / "banco.json"
CACHE_EMBEDDINGS = AQUI / "banco.emb.npz"

MODELO_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CARPETA_MODELOS = Path(os.environ.get("CHASKI_MODELOS", Path.home() / ".cache" / "chaski" / "fastembed"))

PESO_EMBEDDING = 0.7
PESO_LEXICO = 0.3

# Hybrid score at or above which a bank phrase is PROPOSED as "same intent". Below it, `mejor()` abstains.
# Calibrated on the dev half of evals/banco/paraphrases.jsonl (see evals/banco/correr.py); the interpreter
# still makes the final call, so this only decides whether a candidate is worth surfacing as a match.
UMBRAL_MISMA_INTENCION = 0.56

CLAVES_APP = ("id", "es", "quy", "audio", "tags")

STOPWORDS = frozenset(
    """a al algo algun alguna alguno ante con de del el ella ello en entre es esa ese eso esta este esto
    la las le les lo los me mi mis o para pero por que se si sin su sus te ti tu tus u un una uno unos y ya
    usted ud mamita papito mamay taytay senor senora joven senorita a ver oiga bueno pues ahi aqui""".split()
)


class Codificador(Protocol):
    """Anything that turns texts into vectors. The real one is fastembed; tests inject a fake."""

    def __call__(self, textos: list[str]) -> np.ndarray: ...


# ---------- text ----------

def normalizar(texto: str) -> str:
    """Lowercase, strip accents and punctuation, collapse spaces. Used for the leakage rule and lexical search."""
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    solo_letras = re.sub(r"[^a-z0-9 ]+", " ", sin_tildes)  # NFKD already split ñ into n + combining tilde
    return re.sub(r"\s+", " ", solo_letras).strip()


def tokens(texto: str) -> list[str]:
    """Content tokens, prefix-stemmed to 5 chars so duele/dolor stay apart but duele/duelen meet."""
    return [t[:5] for t in normalizar(texto).split() if t not in STOPWORDS and len(t) > 1]


# ---------- lexical ----------

class Lexico:
    """BM25-lite (k1=1.2, b=0.75) over bank `es` tokens, scores scaled to [0, 1]."""

    K1 = 1.2
    B = 0.75

    def __init__(self, textos: list[str]):
        self.docs = [Counter(tokens(t)) for t in textos]
        self.largos = [sum(d.values()) for d in self.docs]
        self.largo_medio = (sum(self.largos) / len(self.largos)) if self.largos else 1.0
        n = len(self.docs)
        df: Counter = Counter()
        for d in self.docs:
            df.update(d.keys())
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def puntajes(self, consulta: str) -> np.ndarray:
        q = tokens(consulta)
        salida = np.zeros(len(self.docs), dtype=np.float32)
        if not q:
            return salida
        for i, (d, largo) in enumerate(zip(self.docs, self.largos)):
            s = 0.0
            for t in q:
                f = d.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.K1 + 1) / (f + self.K1 * (1 - self.B + self.B * largo / self.largo_medio))
            salida[i] = s
        # Ceiling: every query token matched once in an average-length doc. Keeps scores comparable across queries.
        techo = sum(self.idf.get(t, max(self.idf.values(), default=1.0)) for t in q)
        return np.clip(salida / techo, 0.0, 1.0) if techo > 0 else salida


# ---------- embeddings ----------

def codificador_fastembed(modelo: str = MODELO_EMBEDDING) -> Codificador:
    """Load the ONNX model once (downloads ~220 MB on first use into CARPETA_MODELOS)."""
    from fastembed import TextEmbedding

    motor = TextEmbedding(modelo, cache_dir=str(CARPETA_MODELOS))

    def codificar(textos: list[str]) -> np.ndarray:
        return np.asarray(list(motor.embed(textos)), dtype=np.float32)

    return codificar


def _unitarios(m: np.ndarray) -> np.ndarray:
    normas = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.where(normas == 0, 1, normas)


def huella(textos: Iterable[str], modelo: str = MODELO_EMBEDDING) -> str:
    h = hashlib.sha256(modelo.encode())
    for t in textos:
        h.update(b"\x00" + t.encode("utf-8"))
    return h.hexdigest()[:16]


# ---------- the bank ----------

def cargar_items(ruta: Path = BANCO) -> list[dict]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def para_app(item: dict) -> dict:
    """Exactly the keys the iOS app reads."""
    return {k: item.get(k) for k in CLAVES_APP}


class Banco:
    """Retrieval over the bank. Build once; `buscar` is ~a few ms after the model is loaded."""

    def __init__(
        self,
        items: list[dict],
        codificador: Codificador | None = None,
        cache: Path | None = None,
        modelo: str = MODELO_EMBEDDING,
    ):
        self.items = items
        self.textos = [it["es"] for it in items]
        self.lexico = Lexico(self.textos)
        self._codificador = codificador
        self._modelo = modelo
        self._cache = cache
        self._vectores: np.ndarray | None = None
        self._lock = threading.Lock()

    @classmethod
    def desde_archivo(cls, ruta: Path = BANCO, **kw) -> "Banco":
        kw.setdefault("cache", CACHE_EMBEDDINGS if ruta == BANCO else None)
        return cls(cargar_items(ruta), **kw)

    # -- embeddings, lazily --

    @property
    def codificador(self) -> Codificador:
        if self._codificador is None:
            self._codificador = codificador_fastembed(self._modelo)
        return self._codificador

    def vectores(self) -> np.ndarray:
        with self._lock:
            if self._vectores is None:
                self._vectores = self._cargar_o_calcular()
            return self._vectores

    def _cargar_o_calcular(self) -> np.ndarray:
        h = huella(self.textos, self._modelo)
        if self._cache and self._cache.exists():
            datos = np.load(self._cache)
            if str(datos["huella"]) == h and datos["vectores"].shape[0] == len(self.textos):
                return datos["vectores"]
        v = _unitarios(self.codificador(self.textos)) if self.textos else np.zeros((0, 1), np.float32)
        if self._cache:
            np.savez_compressed(self._cache, vectores=v, huella=np.array(h))
        return v

    # -- scoring --

    def puntajes(self, texto_es: str, modo: str = "hibrido") -> np.ndarray:
        """One score per bank item. modo: 'hibrido' | 'embedding' | 'lexico'."""
        if modo == "lexico":
            return self.lexico.puntajes(texto_es)
        q = _unitarios(self.codificador([texto_es]))[0]
        coseno = np.clip(self.vectores() @ q, 0.0, 1.0)
        if modo == "embedding":
            return coseno
        if modo == "hibrido":
            return PESO_EMBEDDING * coseno + PESO_LEXICO * self.lexico.puntajes(texto_es)
        raise ValueError(f"modo desconocido: {modo}")

    def _filtro(self, tag: str | None, solo_con_quechua: bool) -> np.ndarray:
        return np.array(
            [(tag is None or tag in it.get("tags", [])) and (not solo_con_quechua or bool(it.get("quy")))
             for it in self.items],
            dtype=bool,
        )

    def buscar(
        self, texto_es: str, k: int = 5, tag: str | None = None, solo_con_quechua: bool = False, modo: str = "hibrido"
    ) -> list[tuple[dict, float]]:
        """Top-k bank items for a Spanish utterance, best first, as (item, score)."""
        if not texto_es.strip() or not self.items:
            return []
        s = self.puntajes(texto_es, modo).astype(np.float64)
        s[~self._filtro(tag, solo_con_quechua)] = -1.0
        orden = np.argsort(-s, kind="stable")[:k]
        return [(self.items[i], float(s[i])) for i in orden if s[i] >= 0]

    def mejor(self, texto_es: str, umbral: float = UMBRAL_MISMA_INTENCION, **kw) -> tuple[dict, float] | None:
        """The single best item if it clears the same-intent threshold, else None (abstain)."""
        top = self.buscar(texto_es, k=1, **kw)
        return top[0] if top and top[0][1] >= umbral else None

    def candidatos(self, texto_es: str, k: int = 20, solo_con_quechua: bool = True) -> list[dict]:
        """What goes in the interpreter prompt: [{id, es}]. By default only phrases that can actually be said."""
        return [{"id": it["id"], "es": it["es"]} for it, _ in self.buscar(texto_es, k=k, solo_con_quechua=solo_con_quechua)]

    def por_tag(self, tag: str, solo_con_quechua: bool = False) -> list[dict]:
        """Every item with the tag, in bank order (emergency mode)."""
        return [it for it, ok in zip(self.items, self._filtro(tag, solo_con_quechua)) if ok]

    def por_id(self, id_: str) -> dict | None:
        return next((it for it in self.items if it["id"] == id_), None)


# ---------- module-level lazy singleton ----------

_banco: Banco | None = None
_banco_lock = threading.Lock()


def banco() -> Banco:
    """The shared bank, built on first use so the model loads once per process."""
    global _banco
    with _banco_lock:
        if _banco is None:
            _banco = Banco.desde_archivo()
        return _banco


def buscar(texto_es: str, k: int = 5, tag: str | None = None) -> list[tuple[dict, float]]:
    return banco().buscar(texto_es, k=k, tag=tag)


def candidatos(texto_es: str, k: int = 20) -> list[dict]:
    return banco().candidatos(texto_es, k=k)


def por_tag(tag: str) -> list[dict]:
    return banco().por_tag(tag)


_revisados: dict[str, Banco] = {}
EJEMPLOS_K = 5


def ejemplos_revisados(texto: str, idioma: str, k: int = EJEMPLOS_K) -> list[dict]:
    """The k reviewed pairs (revisado: true, with Quechua) closest to `texto`, as [{es, quy}], for the translator.

    Moat step 1 (evals/moat/ejemplos.py, 24-oct 23:55): with the nurse's reviewed phrases as examples the product
    translator went 52.6 → 56.0 chrF++ es→qu and 49.1 → 56.0 qu→es on the families' 62 unseen phrases. They teach the
    region's Quechua more than the content, so no similarity threshold (one measured worse). `idioma` is the language of
    `texto`: Spanish searches the Spanish side, Quechua the Quechua side.
    """
    from chaski import memoria  # approved automatic memory joins the reviewed phrases (D44)

    lado = "es" if idioma == "spa" else "quy"
    extra = memoria.aprobadas() if memoria.activa() else []
    llave = f"{lado}:{len(extra)}"  # rebuilt only when something new was approved
    with _banco_lock:
        if llave not in _revisados:
            items = [it for it in cargar_items() if it.get("revisado") is True and str(it.get("quy", "")).strip()]
            items += [{"id": f"mem-{i}", "es": x["es"], "quy": x["quy"]} for i, x in enumerate(extra)]
            _revisados[llave] = Banco([{**it, "es": it[lado], "_es": it["es"]} for it in items])
        idx = _revisados[llave]
    return [{"es": it["_es"], "quy": it["quy"]} for it, _ in idx.buscar(texto, k=k)]


def precargar() -> None:
    """Call at server start so the first real query doesn't pay the model load."""
    banco().vectores()
    banco().puntajes("hola")
