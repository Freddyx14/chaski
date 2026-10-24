import pytest

from chaski.hechos import Hechos, Medicamento, comparar, momento_comida, vehiculo_canonico, vehiculos_prohibidos


def med(**kw):
    base = dict(nombre="sulfato ferroso", cantidad=1, unidad="pastilla", cada_horas=24, dias=30, momento="después del almuerzo")
    base.update(kw)
    return Medicamento(**base)


def hechos(meds=None, cita=30, señales=None):
    return Hechos(medicamentos=meds if meds is not None else [med()], proxima_cita_en_dias=cita, ir_ya_si=señales or [])


def test_identicos_no_tienen_diferencias():
    assert comparar(hechos(), hechos()) == []


def test_tildes_y_mayusculas_en_el_nombre_no_cuentan():
    assert comparar(hechos([med(nombre="Ácido fólico")]), hechos([med(nombre="acido folico")])) == []


def test_momento_parafraseado_no_bloquea():
    assert comparar(hechos([med(momento="después del almuerzo")]), hechos([med(momento="luego de almorzar")])) == []


def test_frecuencia_distinta_bloquea():
    difs = comparar(hechos([med(cada_horas=24)]), hechos([med(cada_horas=12)]))
    assert [d.campo for d in difs] == ["sulfato ferroso.cada_horas"]


def test_cantidad_distinta_bloquea():
    difs = comparar(hechos([med(cantidad=1)]), hechos([med(cantidad=2)]))
    assert [d.campo for d in difs] == ["sulfato ferroso.cantidad"]


def test_dato_que_desaparece_bloquea():
    difs = comparar(hechos([med(dias=30)]), hechos([med(dias=None)]))
    assert [d.campo for d in difs] == ["sulfato ferroso.dias"]


def test_unidad_distinta_bloquea():
    difs = comparar(hechos([med(unidad="pastilla")]), hechos([med(unidad="cucharada")]))
    assert [d.campo for d in difs] == ["sulfato ferroso.unidad"]


def test_medicamento_perdido_y_medicamento_inventado():
    difs = comparar(hechos([med(nombre="sulfato ferroso")]), hechos([med(nombre="paracetamol")]))
    assert {(d.original, d.retraducido) for d in difs} == {("sulfato ferroso", "(falta)"), ("(no estaba)", "paracetamol")}


def test_cita_distinta_bloquea():
    difs = comparar(hechos(cita=30), hechos(cita=7))
    assert [d.campo for d in difs] == ["proxima_cita_en_dias"]


def test_señal_de_alarma_perdida_bloquea():
    difs = comparar(hechos(señales=["sangrado vaginal", "fiebre"]), hechos(señales=["sangrado"]))
    assert [d.campo for d in difs] == ["ir_ya_si (cantidad de señales)"]


def test_sin_medicamentos_ni_cita():
    assert comparar(hechos(meds=[], cita=None), hechos(meds=[], cita=None)) == []


def test_pastilla_sin_nombre_se_empareja_por_orden_y_reporta_el_horario():
    # Caso real del 24-oct: «Tome una pastilla cada ocho horas» sin nombre de medicamento.
    original = hechos([med(nombre="", cada_horas=8, dias=5)])
    retraducido = hechos([med(nombre=":", cada_horas=None, dias=5)])
    difs = comparar(original, retraducido)
    assert [(d.campo, d.original, d.retraducido) for d in difs] == [("medicamento.cada_horas", "8.0", "None")]


def test_pastilla_sin_nombre_identica_no_bloquea():
    assert comparar(hechos([med(nombre="pastilla")]), hechos([med(nombre="")])) == []


def test_tableta_y_pastilla_son_la_misma_unidad():
    assert comparar(hechos([med(unidad="tableta")]), hechos([med(unidad="pastilla")])) == []


def test_dos_medicamentos_con_nombre_siguen_por_nombre():
    a = [med(nombre="paracetamol", cada_horas=8), med(nombre="amoxicilina", cada_horas=12)]
    b = [med(nombre="amoxicilina", cada_horas=12), med(nombre="paracetamol", cada_horas=8)]
    assert comparar(hechos(a), hechos(b)) == []


# --- B6: hechos que antes no se comparaban -------------------------------------------------

def b6(**kw):
    return Hechos(medicamentos=kw.pop("meds", []), proxima_cita_en_dias=None, ir_ya_si=[], **kw)


def test_hechos_viejos_sin_campos_b6_siguen_validos():
    h = Hechos(medicamentos=[], proxima_cita_en_dias=None, ir_ya_si=[])
    assert h.prohibiciones == [] and h.partes_cuerpo == [] and h.alergias == [] and h.embarazo is None
    assert Medicamento(nombre="x", cantidad=None, unidad=None, cada_horas=None, dias=None, momento=None).via is None


def test_negacion_invertida_bloquea():
    # «no lo tome con té» vs «tómelo con té»: el hueco más peligroso de §2b.
    difs = comparar(b6(prohibiciones=["tomar con té"]), b6(prohibiciones=[]))
    assert [d.campo for d in difs] == ["prohibiciones (cantidad)"]


def test_prohibicion_parafraseada_no_bloquea():
    assert comparar(b6(prohibiciones=["tomar con té"]), b6(prohibiciones=["beberla con té"])) == []


def test_prohibicion_inventada_bloquea():
    difs = comparar(b6(prohibiciones=[]), b6(prohibiciones=["comer grasa"]))
    assert [d.campo for d in difs] == ["prohibiciones (cantidad)"]
    # A bare «no comer» is a fasting instruction since 2026-10-24: invented, it still blocks, as ayunas.
    difs = comparar(b6(prohibiciones=[]), b6(prohibiciones=["comer"]))
    assert [d.campo for d in difs] == ["ayunas"]


def test_parte_del_cuerpo_cambiada_bloquea():
    difs = comparar(b6(partes_cuerpo=["cabeza"]), b6(partes_cuerpo=["barriga"]))
    assert [(d.campo, d.original, d.retraducido) for d in difs] == [("partes_cuerpo", "cabeza", "abdomen")]


def test_sinonimos_de_parte_del_cuerpo_no_bloquean():
    assert comparar(b6(partes_cuerpo=["la barriga"]), b6(partes_cuerpo=["Estómago"])) == []
    assert comparar(b6(partes_cuerpo=["ojos"]), b6(partes_cuerpo=["ojo"])) == []
    assert comparar(b6(partes_cuerpo=["oreja"]), b6(partes_cuerpo=["oídos"])) == []
    assert comparar(b6(partes_cuerpo=["pies"]), b6(partes_cuerpo=["pie"])) == []


def test_parte_del_cuerpo_perdida_bloquea():
    difs = comparar(b6(partes_cuerpo=["pecho"]), b6(partes_cuerpo=[]))
    assert [d.campo for d in difs] == ["partes_cuerpo"]


def test_alergia_cambiada_bloquea():
    difs = comparar(b6(alergias=["penicilina"]), b6(alergias=["paracetamol"]))
    assert [d.campo for d in difs] == ["alergias"]


def test_alergia_perdida_bloquea():
    assert [d.campo for d in comparar(b6(alergias=["penicilina"]), b6(alergias=[]))] == ["alergias"]


def test_alergia_con_articulo_y_plural_no_bloquea():
    assert comparar(b6(alergias=["a la Penicilina"]), b6(alergias=["penicilinas"])) == []
    assert comparar(b6(alergias=["nada"]), b6(alergias=[])) == []


def test_via_cambiada_bloquea():
    difs = comparar(hechos([med(via="oral")]), hechos([med(via="piel")]))
    assert [d.campo for d in difs] == ["sulfato ferroso.via"]


def test_ojos_y_oidos_no_son_la_misma_via():
    difs = comparar(hechos([med(nombre="gotas", via="ojos")]), hechos([med(nombre="gotas", via="oidos")]))
    assert [d.campo for d in difs] == ["medicamento.via"]


def test_via_sin_decir_en_un_lado_no_bloquea():
    # «tome» implica oral; que la retraducción no lo diga no es un cambio.
    assert comparar(hechos([med(via="oral")]), hechos([med(via=None)])) == []


def test_embarazo_invertido_bloquea():
    assert [d.campo for d in comparar(b6(embarazo=True), b6(embarazo=False))] == ["embarazo"]


def test_embarazo_perdido_bloquea():
    assert [d.campo for d in comparar(b6(embarazo=True), b6(embarazo=None))] == ["embarazo"]


def test_embarazo_igual_no_bloquea():
    assert comparar(b6(embarazo=True), b6(embarazo=True)) == []


# --- Vehículo: con qué se toma (hueco medido en vivo el 24-oct) ------------------------------

def test_hechos_viejos_sin_vehiculo_siguen_validos():
    assert Medicamento(nombre="x", cantidad=None, unidad=None, cada_horas=None, dias=None, momento=None).vehiculo is None


def test_caso_vivo_bebe_con_uno_no_con_el_bloquea():
    # «Tómela con agua, no con té» → quy «Unuwan upyaykuy, manan téwanchu» → retro «Bebe con uno, no con él».
    original = b6(meds=[med(nombre="", vehiculo="agua")], prohibiciones=["tomar con té"])
    for vehiculo_retro in ("uno", None):
        retro = b6(meds=[med(nombre="", vehiculo=vehiculo_retro)], prohibiciones=["beber con él"])
        campos = [d.campo for d in comparar(original, retro)]
        assert "medicamento.vehiculo" in campos and "prohibiciones (vehículo)" in campos


def test_agüita_es_agua_y_no_bloquea():
    original = b6(meds=[med(nombre="", vehiculo="agua")], prohibiciones=["tomar con té"])
    retro = b6(meds=[med(nombre="", vehiculo="con agüita")], prohibiciones=["tomarla con un tecito"])
    assert comparar(original, retro) == []


def test_vehiculo_cambiado_bloquea():
    difs = comparar(hechos([med(vehiculo="agua")]), hechos([med(vehiculo="leche")]))
    assert [(d.campo, d.original, d.retraducido) for d in difs] == [("sulfato ferroso.vehiculo", "agua", "leche")]


def test_vehiculo_que_desaparece_o_aparece_bloquea():
    assert [d.campo for d in comparar(hechos([med(vehiculo="agua")]), hechos([med()]))] == ["sulfato ferroso.vehiculo"]
    assert [d.campo for d in comparar(hechos([med()]), hechos([med(vehiculo="jugo")]))] == ["sulfato ferroso.vehiculo"]


def test_sin_vehiculo_en_ningun_lado_no_bloquea():
    assert comparar(hechos([med(vehiculo=None)]), hechos([med(vehiculo="")])) == []


def test_negacion_de_vehiculo_sigue_siendo_prohibicion():
    difs = comparar(b6(prohibiciones=["tomar con leche"]), b6(prohibiciones=[]))
    assert [d.campo for d in difs] == ["prohibiciones (cantidad)"]
    difs = comparar(b6(prohibiciones=["tomar con leche"]), b6(prohibiciones=["tomar con agua"]))
    assert [(d.campo, d.original, d.retraducido) for d in difs] == [("prohibiciones (vehículo)", "leche", "agua")]


@pytest.mark.parametrize("texto,canonico", [
    ("agua", "agua"), ("con agüita", "agua"), ("Agua tibia", "agua"), ("unu", "agua"), ("yaku", "agua"),
    ("la leche", "leche"), ("lichi", "leche"), ("té", "te"), ("un mate", "te"), ("tecito", "te"),
    ("jugos", "jugo"), ("con su comida", "comida"), ("sola", "solo"),
    ("uno", "uno"), ("él", "el"), (None, None), ("", None),
])
def test_vehiculo_canonico(texto, canonico):
    assert vehiculo_canonico(texto) == canonico


def test_te_pronombre_no_es_vehiculo_prohibido():
    h = b6(prohibiciones=["te olvides de la pastilla", "tomar con té", "mezclar con un poco de leche"])
    assert vehiculos_prohibidos(h) == {"te", "leche"}


# ---------------------------------------------------------------------------------------------
# Three false blocks of the final eval (evals/ataques/resultados/chaski-2026-10-24-1549.json)

def _m(**kw):
    base = dict(nombre="", cantidad=None, unidad=None, cada_horas=None, dias=None, momento=None)
    base.update(kw)
    return Medicamento(**base)


def _h(meds=None, **kw):
    return Hechos(medicamentos=meds or [], proxima_cita_en_dias=None, ir_ya_si=[], **kw)


def test_campos_nuevos_son_opcionales_y_retrocompatibles():
    m = _m(nombre="paracetamol", cantidad=1, unidad="pastilla")
    assert m.concentracion is None and m.concentracion_unidad is None
    assert _h().ayunas is None


def test_form_p18_concentracion_no_es_cantidad():
    # «Pastilla de quinientos miligramos» / «Pichqa pachak miligramo pastilla.»
    original = _h([_m(cantidad=1, unidad="pastilla", concentracion=500, concentracion_unidad="mg")])
    retraducido = _h([_m(unidad="pastilla", concentracion=500, concentracion_unidad="miligramos")])
    assert comparar(original, retraducido) == []


def test_mg_leido_como_cantidad_se_mueve_a_concentracion():
    m = _m(cantidad=500, unidad="miligramos")
    assert (m.cantidad, m.unidad, m.concentracion) == (None, None, 500)


def test_concentracion_en_gramos_se_convierte():
    a = _h([_m(nombre="amoxicilina", concentracion=1, concentracion_unidad="g")])
    b = _h([_m(nombre="amoxicilina", concentracion=1000, concentracion_unidad="mg")])
    assert comparar(a, b) == []


def test_concentracion_500_a_250_bloquea():
    a = _h([_m(cantidad=1, unidad="pastilla", concentracion=500, concentracion_unidad="mg")])
    b = _h([_m(cantidad=1, unidad="pastilla", concentracion=250, concentracion_unidad="mg")])
    assert [(d.campo, d.original, d.retraducido) for d in comparar(a, b)] == [
        ("medicamento.concentracion", "500 mg", "250 mg")]


def test_concentracion_perdida_bloquea():
    a = _h([_m(nombre="paracetamol", concentracion=500, concentracion_unidad="mg")])
    assert [d.campo for d in comparar(a, _h([_m(nombre="paracetamol")]))] == ["paracetamol.concentracion"]


def test_cantidad_no_dicha_equivale_a_una_pero_no_a_dos():
    assert comparar(_h([_m(unidad="pastilla")]), _h([_m(cantidad=1, unidad="pastilla")])) == []
    difs = comparar(_h([_m(unidad="pastilla")]), _h([_m(cantidad=2, unidad="pastilla")]))
    assert [d.campo for d in difs] == ["medicamento.cantidad"]


def test_form_p19_ayunas_no_es_prohibicion():
    # «Venga en ayunas» / «Mana mikuspa hamuy» (= venga sin comer)
    for prohibicion in ("comer", "comer antes de venir", "comer nada", "desayunar", "ingerir alimentos"):
        retraducido = _h(prohibiciones=[prohibicion])
        assert retraducido.prohibiciones == [] and retraducido.ayunas is True
        assert comparar(_h(ayunas=True), retraducido) == []
    assert comparar(_h([_m(momento="sin desayunar")]), _h([_m(momento="en ayunas")])) == []


def test_prohibicion_real_de_comida_se_mantiene():
    h = _h(prohibiciones=["comer grasa", "tomar con té", "comer comida chatarra"])
    assert h.prohibiciones == ["comer grasa", "tomar con té", "comer comida chatarra"] and h.ayunas is None
    difs = comparar(_h(ayunas=True, prohibiciones=["comer grasa"]), _h(ayunas=True))
    assert [d.campo for d in difs] == ["prohibiciones (cantidad)"]


def test_ayunas_a_despues_de_comer_bloquea():
    assert [d.campo for d in comparar(_h(ayunas=True), _h(ayunas=False))] == ["ayunas"]
    assert [d.campo for d in comparar(_h(ayunas=True), _h())] == ["ayunas"]
    a = _h([_m(nombre="omeprazol", momento="en ayunas")])
    b = _h([_m(nombre="omeprazol", momento="después de comer")])
    assert {d.campo for d in comparar(a, b)} == {"omeprazol.momento", "ayunas"}


def test_despues_del_desayuno_no_es_ayunas():
    assert momento_comida("después del desayuno") == "comida"
    assert momento_comida("en ayunas") == momento_comida("sin desayunar") == "ayunas"
    assert momento_comida("antes de dormir") is None


def test_form_m20_fraccion_no_es_nombre():
    # «Media tableta» / «Kuska tableta nisqata qoy»
    original = _h([_m(cantidad=0.5, unidad="tableta")])
    for nombre, cantidad in (("kuska", None), ("kuska", 1), ("kuska tableta", None), ("media", 1), ("Chawpi", None)):
        retraducido = _h([_m(nombre=nombre, cantidad=cantidad, unidad="tableta")])
        assert (retraducido.medicamentos[0].nombre, retraducido.medicamentos[0].cantidad) == ("", 0.5)
        assert comparar(original, retraducido) == []
    assert _m(nombre="un cuarto").cantidad == 0.25


def test_fraccion_junto_a_un_nombre_real_conserva_el_nombre():
    m = _m(nombre="paracetamol kuska", unidad="pastilla")
    assert (m.nombre, m.cantidad) == ("paracetamol", 0.5)


def test_media_a_una_bloquea():
    difs = comparar(_h([_m(cantidad=0.5, unidad="tableta")]), _h([_m(cantidad=1, unidad="tableta")]))
    assert [(d.campo, d.original, d.retraducido) for d in difs] == [("medicamento.cantidad", "0.5", "1.0")]
    difs = comparar(_h([_m(nombre="kuska", unidad="tableta")]), _h([_m(cantidad=1, unidad="tableta")]))
    assert [d.campo for d in difs] == ["medicamento.cantidad"]
