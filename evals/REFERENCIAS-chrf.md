# chrF++: dónde estamos frente a lo publicado (sáb 24-oct, 23:10)

> Pedido de Freddy (22:50): una tabla para saber qué es «bueno». Cada número tiene su fuente primaria. **Los puntajes
> solo se comparan en el mismo set de prueba:** los nuestros (30 y 62 frases propias) no son números de FLORES.

| Sistema | Dirección | Set | Puntaje | Fuente |
|---|---|---|---|---|
| NLLB-200 600M | spa→quy · eng→quy · quy→eng | FLORES-200 devtest | chrF++ 23,9 · 24,1 · 30,9 | [metrics.csv de Meta](https://dl.fbaipublicfiles.com/large_objects/nllb/models/nllb_200_dense_distill_600m/metrics.csv) |
| NLLB-200 1.3B | spa→quy · eng→quy · quy→eng | FLORES-200 devtest | 25,4 · 25,9 · 32,7 | [metrics.csv](https://dl.fbaipublicfiles.com/large_objects/nllb/models/nllb_200_dense_distill_1b/metrics.csv) |
| NLLB-200 3.3B | spa→quy · eng→quy · quy→eng | FLORES-200 devtest | 27,1 · 26,7 · 33,9 | [metrics.csv](https://dl.fbaipublicfiles.com/large_objects/nllb/models/nllb_200_dense_3b/metrics.csv) |
| **Google Translate** | eng→quy | FLORES-200 devtest | **34,0** | [Robinson et al. 2023](https://aclanthology.org/2023.wmt-1.40.pdf), tabla 11 |
| ChatGPT (gpt-3.5) | eng→quy | FLORES-200 devtest | 9,3 | misma, tabla 11 |
| AmericasNLP 2021: base → mejor | spa→quy (chanka) | AmericasNLI test, 1.003 frases | chrF 30,4 → 39,4 | [Findings 2021](https://aclanthology.org/2021.americasnlp-1.23.pdf), tablas 3 y 5 |
| AmericasNLP 2023: mejor | spa→quy | mismo | chrF 39,52 | [Findings 2023](https://aclanthology.org/2023.americasnlp-1.23.pdf), tabla 4 |
| AmericasNLP 2024: mejor (NLLB-1.3B + LoRA) | spa→quy | mismo | chrF++ 38,21 | [Findings 2024](https://aclanthology.org/2024.americasnlp-1.28.pdf), tabla 4 |
| Idioma con muchos datos: NLLB 3.3B | eng→spa · spa→eng · eng→deu | FLORES-200 devtest | 54,2 · 59,1 · 62,8 | 3.3B metrics.csv |
| Idioma con muchos datos: Google | eng→spa · eng→deu | FLORES-200 devtest | 55,5 · 66,5 | Robinson et al., tabla 11 |

**Lo nuestro (sets propios, no comparables con lo de arriba):** Claude Sonnet 5 pensando 51,8 (30 pares) · Claude
sin pensar 42,3–44,6 · NLLB-1.3B 34,7 · NLLB-600M 28,6 (`evals/HISTORIA.md`, `ricardo-artifacts/reports/`).

## Cómo leerlo
- **Las bandas «0–20 mal, 20–40 idea general, 40–60 decente, 60+ casi humano» no tienen fuente revisada por pares.**
  Solo aparecen en una página de un proveedor sin citas. No las usamos en el pitch.
- **Lo que sí está publicado es cuánta diferencia nota una persona:** con ≥ 3,05 puntos de chrF, el 90 % de los
  humanos coincide en cuál sistema es mejor ([Kocmi et al. 2024](https://aclanthology.org/2024.acl-long.110.pdf), tabla 2).
  Claude le saca ~17 a NLLB-1.3B en nuestro set: una diferencia que se nota.
- **El techo humano no está medido** para quechua (cuánto saca un segundo traductor contra la referencia).
- Nuestro NLLB saca 9 puntos más en nuestro set que en FLORES (34,7 vs 25,4): nuestro set es más fácil o más cercano al
  dominio. Hay que esperar que todo se vea más alto acá.
- Para un número que se pueda poner al lado de Google (34,0) o de AmericasNLP (~39), hay que correr los sistemas sobre
  **FLORES-200 devtest spa→quy** o el test de AmericasNLI.
