# CL Beta plan 30d — revisión del trading plan

Análisis de las **97 operaciones reales** registradas en
`B20x50 - CL Beta plan 30d 22-10.xlsx` (cuenta real, 22/10/2025 → 26/06/2026),
contrastadas con las reglas de `Trading Plan Personal.docx`.

## Resultado en una línea

El winrate fue **idéntico (35,4 %) en las dos mitades del período**, pero la primera
ganó $525 y la segunda perdió $2.074. Lo que se rompió no fue la lectura del mercado
sino el ratio riesgo/beneficio: **el R cayó de 2,04 a 1,10** cuando el stop empezó a
ensancharse con la volatilidad mientras el objetivo seguía anclado a pivotes que no se
mueven con el ATR.

| | |
|---|---:|
| Capital | $10.000 → $8.584,52 (−14,15 %) |
| Winrate | 36,1 % |
| R real | 1,51 · **equilibrio 39,8 %** |
| Profit factor | 0,853 |
| Máximo drawdown | −$2.321 (23 %) |

Faltan 3,7 puntos de winrate, o 0,27 puntos de R.

## Documentos

| Archivo | Contenido |
|---|---|
| [`01-DIAGNOSTICO.md`](01-DIAGNOSTICO.md) | Por qué pierde: el corte por mitades, la causa medida, qué resiste el test estadístico y qué no |
| [`02-PLAN-CORREGIDO.md`](02-PLAN-CORREGIDO.md) | Las siete correcciones (C1–C7), ninguna toca la lógica de entrada |
| `informe.html` | Resumen visual |

## Las dos correcciones principales

- **C1 — ratio mínimo 2:1 verificado antes de entrar.** El plan ya pide que «el pivote
  permita el recorrido hasta el target», pero sin número, y por eso no filtra nada.
- **C2 — si el stop se ensancha por volatilidad, el objetivo también.** No es «no operar
  MCL»: el winrate en MCL fue del 38,5 %, mejor que el 33,3 % de CL. Lo que hay que
  descartar no son los días volátiles, son las operaciones mal proporcionadas.

## Pendiente

**MFE y MAE están vacíos en 96 de las 97 operaciones.** El R *realizado* se reconstruyó
a partir de los ticks de salida, y con eso alcanzó para el diagnóstico. Para calibrar el
target hace falta el R *disponible*: saber si el precio llegó a rozar el objetivo y
volvió, o si nunca se acercó. Las capturas de pantalla de las sesiones permitirían
reconstruirlo hacia atrás.

## Reproducir el análisis

Los scripts de `analisis/` leen el `.xlsx` directamente (requieren `openpyxl`).
Hay que apuntar la ruta del archivo al principio de `beta_load.py`, que genera el
`beta.json` que consumen los demás.

| Script | Qué hace |
|---|---|
| `beta_load.py` | Extrae las 97 operaciones de la pestaña «Entrada de Datos» |
| `beta_an.py` | Winrate, profit factor, R, cortes por set up / instrumento / hora / día / mes |
| `beta_deep.py` | Hora relativa a la apertura cash, set up × dirección, pérdidas grandes |
| `beta_valid.py` | Test exacto de Fisher, estabilidad temporal, validación fuera de muestra |
| `beta_size.py` | Qué cambió entre las dos mitades: tamaño, instrumento, contratos |
| `beta_r.py` | Stop y target en ticks por contrato — el cálculo que aísla la causa |
| `beta_reglas.py` | Cumplimiento de las reglas del plan y atribución de la pérdida |
| `beta_oos.py` | Efecto de cada corrección y tabla de esperanza |
