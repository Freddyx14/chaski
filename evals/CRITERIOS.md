# Criterios para elegir la configuración del crítico (sáb 24-oct, 17:00 PT)

> Pedido de Freddy (16:51): *«establish your criteria, which gives the most accurate result in terms of getting these
> wrong cases … blocking them from going to the client … criteria with weights … accuracy and also time … at the top
> of $30»*. Cada configuración (modelos por paso, paralelismo, prompts) se puntúa igual, sobre el **mismo** banco
> auditado y la **misma** muestra.

## 1 · Compuertas (si falla una, la configuración queda descartada sin importar el puntaje)

| Compuerta | Umbral | Por qué |
|---|---|---|
| G1 · Errores críticos atrapados | **100 %** en número, días, negación, medicamento, unidad, vehículo, concentración | Un error de dosis o de «no» que pasa puede dañar a un paciente |
| G2 · Bloqueos falsos | ≤ 20 % de las frases correctas | Por encima, la enfermera deja de usarlo |
| G3 · Falla cerrada | 0 casos donde un error del sistema deje pasar algo | Si no pudo verificar, no habla |

## 2 · Puntaje (sobre 100) para elegir entre las que pasan las compuertas

| Peso | Criterio | Cómo se mide |
|---|---|---|
| **40** | Errores de contenido atrapados (consejo, diagnóstico, dato agregado al pulir) | % atrapados en `agrega_consejo`, `agrega_diagnostico`, `pulido_agrega` |
| **25** | Frases correctas que pasan | 100 − % de bloqueos falsos en `limpio` y `pulido_limpio` |
| **25** | Tiempo del crítico | p50 ≤ 3 s = 25 puntos; ≥ 12 s = 0; lineal entre medio. Se resta hasta 5 puntos si p95 > 15 s |
| **10** | Costo por turno | ≤ $0,01 = 10 puntos; ≥ $0,05 = 0; lineal |

La precisión pesa 65 y la velocidad 25 porque en una posta un error cuesta más que una espera, pero una espera de
40 s hace que la enfermera deje de usarlo.

## 3 · Presupuesto

- Tope total pedido: **$30** en mediciones con la API.
- **Antes de seguir gastando**: cada corrida registra tokens y costo reales desde `response.usage` (hoy no lo hace, así
  que lo gastado hasta ahora es una estimación).
- Corridas de ajuste con `--limite 10` (≈ 110 casos); la corrida final con `--limite 20`.

## 4 · Primero, auditar el banco

Un banco con etiquetas mal puestas da números que mienten. Antes de optimizar se revisa (sin costo de API):
- que cada mutación cambie de verdad el significado (y que una frase «limpia» sea de verdad correcta);
- las traducciones flojas de la familia, que deben bloquearse, pasan a su propia categoría en vez de contar como
  «bloqueo falso»;
- duplicados, cobertura por tipo, y que ningún caso venga de las 100 frases reservadas para medir la traducción.
