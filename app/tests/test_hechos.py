from chaski.hechos import Hechos, Medicamento, comparar


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
    difs = comparar(b6(prohibiciones=[]), b6(prohibiciones=["comer"]))
    assert [d.campo for d in difs] == ["prohibiciones (cantidad)"]


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
