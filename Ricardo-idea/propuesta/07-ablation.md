# Ablation study: qué features y qué modelo, probado y no supuesto

> Lo pidió Ricardo: *"me gustaría hacer un ablation study de diferentes modelos y encontrar los mejores
> features que hagan cross entre la data que tenemos y otro tipo de data"*.
> Esto es lo que convierte el proyecto en algo evaluable en vez de un dashboard con un modelo adentro.
> Objetivo y partición vienen de `02-diseno-tecnico.md`; las métricas vienen de `05-estado-del-arte.md` §5.

## La pregunta que responde el ablation

**¿Cuánto aporta cada bloque de información, por encima de lo que ya sabe el corredor por su propio
pasado?** No "cuál es el mejor modelo", que es la pregunta de Kaggle y a nadie le importa, sino **qué
información nueva vale la pena cruzar**. Esa es la diapositiva que gana la parte técnica del pitch.

## Bloques de features

| Bloque | Qué contiene | De dónde sale |
|---|---|---|
| **A · Persistencia** | Extorsión en el corredor, lags 1, 2, 4, 8, 12 semanas | Denuncias PNP |
| **B · Difusión en el grafo** | Extorsión en vecinos a 1 y 2 saltos, lags 1, 2, 4; distancia al corredor activo más cercano | PNP + grafo OSM |
| **C · Contagio cruzado** | Violencia previa en el corredor y en vecinos: `LESIONES POR PAF`, `MUERTE POR ARMA DE FUEGO`, `DAÑOS`, lags 4 y 12 | PNP |
| **D · Estructura del corredor** | Longitud, jerarquía de vía, grado de intersección, centralidad *betweenness*, distancia a vía principal | Grafo OSM |
| **E · Exposición y denominador** | Negocios por corredor (OSM, y padrón RUC si entra), mercados, colegios, rutas de transporte | OSM, SUNAT, INEI, ATU |
| **F · Satelital** | Densidad construida y su cambio (Open Buildings), nivel y cambio de luces nocturnas (VIIRS) | Earth Engine |
| **G · Temporal** | Semana del año, tendencia, feriados, turno predominante del corredor | Calendario y PNP |
| **H · Delito de fondo** | Robo, hurto y faltas en el corredor, lag 4 | PNP |

`02-diseno-tecnico.md` §1.1 define la etiqueta. Recordatorio: **predecimos violencia armada, no
extorsión**, porque la extorsión está subregistrada entre 75% y 90% y la violencia con arma deja herido,
disparo o destrozo (ver `05-estado-del-arte.md` §7).

## Familias de modelos

| # | Modelo | Por qué está |
|---|---|---|
| 0 | **Baseline de persistencia**: ranquear corredores por extorsión en las últimas 4 semanas | Es lo que haría cualquiera sin modelo. Si no le ganamos, no hay proyecto |
| 1 | **Regresión logística regularizada** | Piso interpretable. Si empata con todo lo demás, es la respuesta honesta |
| 2 | **Random Forest** | No lineal, barato, robusto |
| 3 | **Gradient boosting** (`HistGradientBoostingClassifier`, o LightGBM si está) | El caballo de batalla para datos tabulares. Lo más probable es que gane |
| 4 | **Auto-excitante discreto**: intensidad con kernel exponencial sobre tiempo y saltos del grafo | La versión computable del Hawkes de Mohler et al. 2011. Pocos parámetros, muy defendible |
| 5 | **GNN temporal** (`torch_geometric`, GraphSAGE + GRU o A3T-GCN) | El estado del arte de Gu & Sui 2024. Solo si el sábado rinde |

**Regla de honestidad:** si el modelo 3 le gana al 5, se reporta que le gana. Un GNN que pierde contra
gradient boosting y aun así se presenta como el núcleo es exactamente lo que un jurado técnico detecta.

## Protocolo

1. **Partición temporal, nunca aleatoria.**
   - Entrenamiento y validación: 2018-01 a 2024-12, con **origen móvil**: entrenar hasta la semana *t*,
     validar las 8 semanas siguientes, avanzar, repetir. Los hiperparámetros se eligen **solo** aquí.
   - **Prueba final: 2025-01-01 a 2025-06-30. Se toca una sola vez, al final.** Si se mira antes, el
     número deja de valer.
2. **Desbalance.** La clase positiva es rara. Se reporta la prevalencia real y se usan curvas
   precisión-recall. Nada de accuracy.
3. **Semillas.** Tres semillas para los modelos estocásticos; se reporta media y desviación.
4. **Presupuesto de cómputo.** Cada configuración debe correr en menos de 5 minutos sobre los tres
   distritos. La GNN que pase de 20 minutos se descarta por reloj, y se dice en el README que se descartó
   por reloj y no por calidad.

## Métricas

| Métrica | Qué responde | Para quién |
|---|---|---|
| **AUC-PR** | Calidad global con clases desbalanceadas | Jurado técnico |
| **PAI@k** = (n/N)/(a/A) | Cuánto se concentra el delito en lo que marcamos. Estándar del campo | Funcionario |
| **PEI@k** | PAI dividido por el PAI máximo alcanzable. Dice qué tan lejos estamos del techo | Jurado técnico |
| **Recall@top-k corredores** | De los hechos violentos de 2025, cuántos cayeron en los k corredores marcados | Todos |
| **Calibración (Brier, curva)** | Si decimos 30%, ¿pasa el 30% de las veces? | **Ético**: le mostramos una probabilidad a una persona asustada |
| **Tiempo de anticipación** | Cuántas semanas antes del hecho entró el corredor al top-k | Es el valor del producto |

k se fija como el 1%, 5% y 10% de la longitud total de vía, no como un número de corredores, porque los
corredores tienen largos distintos.

## Las dos tablas que van al README y a la lámina

**Tabla 1 — Aporte de cada bloque (acumulativo), con el mejor modelo:**

| Features | AUC-PR | PAI@5% | Recall@5% | Δ vs anterior |
|---|---|---|---|---|
| Baseline de persistencia (sin modelo) | | | | — |
| A | | | | |
| A+B | | | | |
| A+B+C | | | | |
| A+B+C+D | | | | |
| A+B+C+D+E | | | | |
| A+B+C+D+E+F (satélite) | | | | |
| Todo + G + H | | | | |

**Tabla 2 — Dejar uno fuera, sobre el modelo completo.** Dice qué bloque es imprescindible y cuál es
decorativo. Es la tabla que responde en serio la pregunta de qué cruce sirve.

**Decisión que se toma con la tabla 1:** si F (satélite) aporta menos de 0.01 de AUC-PR, **se saca del
producto y se dice en el pitch que se probó y no aportó**. Eso es mejor ciencia y mejor pitch que
arrastrar una capa satelital inútil para que la lámina se vea bonita.

## Pruebas de robustez, que son las que dan credibilidad

1. **Por distrito.** ¿Funciona solo en SJL o también en Comas y SMP? Si solo funciona en uno, se dice.
2. **Corredores en frío.** Rendimiento en corredores **sin ninguna denuncia previa de extorsión**. Es el
   caso del subregistro: la cuadra donde cobran pero nadie denunció. Si el modelo solo sabe predecir donde
   ya hubo denuncias, eso es exactamente lo que advierten Lum & Isaac (2016), y hay que medirlo, no
   esconderlo.
3. **Sensibilidad al snap.** Repetir con umbrales de 50, 80 y 120 metros. Si los resultados cambian mucho,
   la unidad de análisis es frágil.
4. **Quiebre de 2022.** La extorsión pasa de 1,336 a 7,525 denuncias entre 2021 y 2022. Entrenar solo con
   2022–2024 y comparar contra entrenar con 2018–2024. Puede que los años viejos estorben.
5. **Estabilidad de la explicación.** ¿Las features que SHAP pone arriba son las mismas entre semillas? Si
   bailan, la frase que Claude le dice al bodeguero no es confiable y hay que decirlo.

## Qué produce, en concreto

```
pipeline/reports/
├── ablation.md            # las dos tablas, generadas, no escritas a mano
├── ablation.csv           # una fila por (modelo, bloques, semilla, métrica)
├── curvas_pr.png
├── calibracion.png
└── shap_top_features.json # lo que consume Claude para explicar
```

## Reloj

Esto **no** se hace antes del modelo base. El orden es: tabla corredor-semana → baseline → gradient
boosting con el bloque A → API funcionando → y recién entonces el ablation, mientras Freddy conecta la
interfaz. Un ablation precioso con una demo rota pierde el hackathon.

Si a las 21:00 del sábado solo alcanzó para las filas A, A+B y A+B+C de la tabla 1, **eso ya es un
ablation presentable**. Se reporta lo que se corrió y se dice qué faltó.
