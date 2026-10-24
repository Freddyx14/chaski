from rimay.hechos import Hechos, Medicamento, comparar


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
