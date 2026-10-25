"""Pure-code guards B1-B4 and fail_closed. No network."""
import pytest

from chaski.guardas import (NO_PUDE_VERIFICAR, Veredicto, fail_closed, numeros_castellano, numeros_quechua,
                            oido_confiable, pasa, pulido_conserva_hechos, pulido_sin_terminos_nuevos,
                            terminos_fijos)
from chaski.hechos import Hechos, Medicamento


def med(**kw):
    base = dict(nombre="paracetamol", cantidad=1, unidad="pastilla", cada_horas=8, dias=7, momento=None)
    base.update(kw)
    return Medicamento(**base)


def h(meds=(), **kw):
    return Hechos(medicamentos=list(meds), proxima_cita_en_dias=kw.pop("cita", None), ir_ya_si=kw.pop("ir_ya_si", []), **kw)


# --- tabla de números -----------------------------------------------------------------------

@pytest.mark.parametrize("texto,esperado", [
    ("Huk pastillata upyay, sapa pusaq horaspi", [1, 8]),
    ("sapa pusac pacha", [8]),
    ("Upyay pastillata pusacc horapi", [8]),
    ("Pastillata upyay, sapa chunka iskayniyuq horaspim.", [12]),
    ("Kimsachunka isqunniyuq fiebre.", [39]),
    ("Pichqa pachak miligramo pastilla.", [500]),
    ("Kimsa sututa churay.", [3]),
    ("Qanchis p'unchawmi hampikuy.", [7]),
    ("Pisq'a milímetro", [5]),
    ("Allichu, huktawan niway", [1]),  # «otra vez», no 1 y 4
    ("Tome 2 pastillas", [2]),
])
def test_numeros_quechua(texto, esperado):
    assert numeros_quechua(texto) == esperado


@pytest.mark.parametrize("texto,esperado", [
    ("Tome una pastilla cada ocho horas, por siete días", [1, 8, 7]),
    ("Tiene treinta y nueve de fiebre", [39]),
    ("Pastilla de quinientos miligramos", [500]),
    ("Tome 10 gotas", [10]),
])
def test_numeros_castellano(texto, esperado):
    assert numeros_castellano(texto) == esperado


# --- B4 términos fijos ----------------------------------------------------------------------

def test_b4_traduccion_correcta_pasa():
    v = terminos_fijos("Tome una pastilla de paracetamol cada ocho horas", "Paracetamol pastillata upyay, sapa pusaq horapi",
                       h([med()]))
    assert v.ok, v.detalle


def test_b4_numero_cambiado_bloquea():
    v = terminos_fijos("Tome una pastilla cada ocho horas", "Huk pastillata upyay, sapa suqta horaspi")
    assert not v.ok and any("8" in d for d in v.detalle) and any("6" in d for d in v.detalle)


def test_b4_numero_que_falta_bloquea():
    v = terminos_fijos("Son siete días de tratamiento", "Hampikuyqa punchawmi")
    assert not v.ok and "7" in v.motivo


def test_b4_variantes_de_ortografia_pasan():
    assert terminos_fijos("Tome una pastilla cada ocho horas", "Upiayco uq hampita sapa pusac pacha").ok
    assert terminos_fijos("Tiene treinta y nueve de fiebre", "Kimsachunka isqunniyuq fiebre.").ok


def test_b4_semana_dicha_como_siete_dias_pasa():
    assert terminos_fijos("Vuelva en una semana", "Qanchis phunchawmanta kutimuy").ok


def test_b4_numero_de_los_hechos_es_permitido():
    # «una vez al día» → cada_horas 24 en los hechos; si el quechua lo dice como 24 horas no es un dato nuevo.
    assert terminos_fijos("Tómela una vez al día", "Sapa iskay chunka tawayuq horapi upyay", h([med(nombre="pastilla", cada_horas=24)])).ok


def test_b4_contar_del_uno_al_diez_pasa():
    assert terminos_fijos("Cuente del uno al diez", "Uk, iskay, kinsa, tawa, pischqa, soqta, qanchis, pusak, esq'on y chunka").ok


def test_b4_medicamento_cambiado_bloquea():
    v = terminos_fijos("Tome paracetamol", "Ibuprofenota upyay.")
    assert not v.ok
    assert any("paracetamol" in d for d in v.detalle) and any("ibuprofeno" in d for d in v.detalle)


def test_b4_medicamento_con_sufijo_quechua_pasa():
    assert terminos_fijos("Tome sulfato ferroso", "Sulfatoferrosuta uphyay").ok
    assert terminos_fijos("Dele suero oral", "Sueruta uphyachiy").ok


def test_b4_medicamento_de_los_hechos_debe_aparecer():
    v = terminos_fijos("Tome su pastilla", "Pastillata upyay", h([med(nombre="cotrimoxazol")]))
    assert not v.ok and "cotrimoxazol" in v.motivo


def test_b4_negacion_quitada_bloquea():
    v = terminos_fijos("Tómela con agua, no con té", "Yakuwan upyay, tewan upyay.")
    assert not v.ok and "negación" in v.motivo


def test_b4_negacion_presente_pasa():
    assert terminos_fijos("Tómela con agua, no con té", "Yakuwan upyay, ama tewan upyaychu.").ok
    assert terminos_fijos("Tómela con agua, no con té", "Yakuwan upyay manan tehawan").ok


def test_b4_prohibicion_de_los_hechos_pide_negacion():
    v = terminos_fijos("Evite el té", "Tewan upyay", h(prohibiciones=["tomar té"]))
    assert not v.ok


def test_b4_expresion_fija_no_cuenta_como_negacion():
    assert terminos_fijos("No hay de qué", "Imamanta").ok


def test_b4_unidad_cambiada_bloquea():
    v = terminos_fijos("Una cucharadita de jarabe", "Huk pastillata jarabeta upyay")
    assert not v.ok and "pastilla" in v.motivo


def test_b4_unidad_nativa_equivalente_pasa():
    assert terminos_fijos("Póngale tres gotas", "Kimsa sututa churay.").ok
    assert terminos_fijos("Una cucharadita de jarabe", "Huk uchuy wisllachapi jarabeta upyay.").ok


def test_b4_entrada_rota_falla_cerrada():
    v = terminos_fijos(None, 42)
    assert not v.ok and v.motivo == NO_PUDE_VERIFICAR


# --- B2 / B3 el pulido ----------------------------------------------------------------------

def test_pulido_igual_pasa():
    assert pulido_conserva_hechos(h([med()]), h([med()])).ok


def test_pulido_que_solo_quita_relleno_pasa():
    # Los hechos son los mismos aunque el texto pulido sea más corto; «momento» parafraseado no cuenta.
    assert pulido_conserva_hechos(h([med(momento="después de comer")]), h([med(momento="luego de comer")])).ok


def test_pulido_que_cambia_una_dosis_bloquea_b2():
    v = pulido_conserva_hechos(h([med(cada_horas=8)]), h([med(cada_horas=6)]))
    assert not v.ok and v.capa.startswith("B2") and "cada_horas" in v.motivo


def test_pulido_que_agrega_un_medicamento_bloquea_b3():
    v = pulido_conserva_hechos(h([med()]), h([med(), med(nombre="ibuprofeno")]))
    assert not v.ok and v.capa.startswith("B3") and "ibuprofeno" in v.motivo


def test_pulido_que_agrega_dias_bloquea_b3():
    v = pulido_conserva_hechos(h([med(dias=None)]), h([med(dias=7)]))
    assert not v.ok and v.capa.startswith("B3")


def test_pulido_que_inventa_el_momento_bloquea_b3():
    # §2b: el pulido agrega «después de comer» que nadie dijo.
    v = pulido_conserva_hechos(h([med(momento=None)]), h([med(momento="después de comer")]))
    assert not v.ok and v.capa.startswith("B3") and "momento" in v.motivo


def test_pulido_que_agrega_una_prohibicion_bloquea_b3():
    v = pulido_conserva_hechos(h(), h(prohibiciones=["comer grasa"]))
    assert not v.ok and v.capa.startswith("B3")


def test_pulido_que_quita_una_negacion_bloquea():
    v = pulido_conserva_hechos(h(prohibiciones=["tomar con té"]), h())
    assert not v.ok and v.capa.startswith("B2")


def test_pulido_en_codigo_quitar_relleno_pasa():
    assert pulido_sin_terminos_nuevos("Eh, este, tome la pastilla cada ocho horas, ¿ya?",
                                      "Tome la pastilla cada ocho horas").ok


def test_pulido_en_codigo_numero_nuevo_bloquea():
    v = pulido_sin_terminos_nuevos("Tome la pastilla", "Tome la pastilla por cinco días")
    assert not v.ok and "5" in v.motivo


def test_pulido_en_codigo_medicamento_nuevo_bloquea():
    assert not pulido_sin_terminos_nuevos("Tome paracetamol", "Tome paracetamol e ibuprofeno").ok


def test_pulido_en_codigo_negacion_quitada_bloquea():
    assert not pulido_sin_terminos_nuevos("No la tome con té", "Tómela con té").ok


def test_pulido_mal_formado_falla_cerrado():
    v = pulido_conserva_hechos(None, h())
    assert not v.ok and v.motivo == NO_PUDE_VERIFICAR


# --- B1 lo que se oyó ------------------------------------------------------------------------

def w(texto, confianza):
    return {"texto": texto, "confianza": confianza}


def test_b1_todo_claro_pasa():
    assert oido_confiable([w("tome", 0.9), w("ocho", 0.95), w("pastillas", 0.9)], umbral=0.6).ok


def test_b1_numero_dudoso_bloquea():
    v = oido_confiable([w("cada", 0.9), w("ocho", 0.3), w("horas", 0.9)], umbral=0.6)
    assert not v.ok and "ocho" in v.motivo


def test_b1_numero_quechua_dudoso_bloquea():
    assert not oido_confiable([w("sapa", 0.9), w("pusaq", 0.2), w("horapi", 0.9)], umbral=0.6).ok


def test_b1_medicamento_dudoso_bloquea():
    assert not oido_confiable([w("tome", 0.9), w("paracetamol", 0.4)], umbral=0.6).ok


def test_b1_parte_del_cuerpo_dudosa_bloquea():
    assert not oido_confiable([w("me", 0.9), w("duele", 0.9), w("barriga", 0.3)], umbral=0.6).ok
    assert not oido_confiable([w("Umaymi", 0.3), w("nanan", 0.9)], umbral=0.6).ok


def test_b1_palabra_comun_dudosa_no_bloquea():
    assert oido_confiable([w("por", 0.2), w("favor", 0.3), w("siéntese", 0.9)], umbral=0.6).ok


def test_b1_silencio_bloquea():
    assert not oido_confiable([], umbral=0.6).ok


def test_b1_entrada_mal_formada_falla_cerrada():
    assert oido_confiable([{"texto": "ocho"}], umbral=0.6).motivo == NO_PUDE_VERIFICAR
    assert not oido_confiable([w("ocho", 7.0)], umbral=0.6).ok


# --- fail_closed ------------------------------------------------------------------------------

def test_fail_closed_excepcion_es_bloqueo():
    @fail_closed
    def revienta():
        raise TimeoutError("se agotó el tiempo")

    v = revienta()
    assert isinstance(v, Veredicto) and not v.ok and v.motivo == NO_PUDE_VERIFICAR and "TimeoutError" in v.detalle[0]


def test_fail_closed_salida_mal_formada_es_bloqueo():
    @fail_closed
    def devuelve_true():
        return True

    assert devuelve_true().ok is False


def test_fail_closed_deja_pasar_un_veredicto_valido():
    @fail_closed
    def bien():
        return pasa("x")

    assert bien().ok is True


# --- B4 vehículo: con qué se toma (caso vivo del 24-oct) ------------------------------------

ES_AGUA_TE = "Tómela con agua, no con té"


@pytest.mark.parametrize("quy", [
    "Unuwan upyaykuy, manan téwanchu",          # caso vivo, versión correcta
    "Yakuwan upyay manan tehawan",              # formulario p15
    "Upyay yacuta manan tehuancho",             # formulario p16
    "Yakuwan upyay, ama tewan upyaychu.",       # formulario p18
    "Yakuwan upyay mana tiwanchu",              # formulario p19
])
def test_b4_vehiculo_correcto_pasa(quy):
    v = terminos_fijos(ES_AGUA_TE, quy)
    assert v.ok, v.detalle


@pytest.mark.parametrize("quy,falta", [
    ("Upyaykuy, manan téwanchu", "agua"),        # caso vivo sin la palabra del agua
    ("Lechewan upyaykuy, manan téwanchu", "agua"),
    ("Unuwan upyaykuy, manan lechewanchu", "te"),
])
def test_b4_vehiculo_perdido_o_cambiado_bloquea(quy, falta):
    v = terminos_fijos(ES_AGUA_TE, quy)
    assert not v.ok and any(f"con {falta}" in d for d in v.detalle), v.detalle


def test_b4_vehiculo_cambiado_nombra_el_intruso():
    v = terminos_fijos("Mézclelo con leche", "Lichiwan chaqruy")
    assert v.ok, v.detalle
    v = terminos_fijos("Mézclelo con leche", "Yakuwan chaqruy")
    assert not v.ok and any("«agua»" in d for d in v.detalle) and any("con leche" in d for d in v.detalle)


def test_b4_sin_vehiculo_en_castellano_no_exige_nada():
    assert terminos_fijos("Tome la pastilla", "Pastillata upyay").ok


def test_vehiculos_detectados():
    from chaski.guardas import vehiculos_castellano, vehiculos_quechua
    assert vehiculos_castellano("Tómela con un poco de agüita, no con mate") == {"agua", "te"}
    assert vehiculos_castellano("No te olvides la pastilla") == set()
    assert vehiculos_quechua("Unuwan upyaykuy, manan téwanchu") == {"agua", "te"}
    assert vehiculos_quechua("Tiyay, tawa pastillata upyay") == set()


def test_b3_frena_una_negacion_agregada_en_el_pulido():
    from chaski import guardas as g
    v = g.pulido_sin_terminos_nuevos("tómelo con leche", "no lo tome con leche")
    assert not v.ok and "agregó una negación" in v.motivo
