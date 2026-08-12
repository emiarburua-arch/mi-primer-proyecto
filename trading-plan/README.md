# CL Beta plan 30d — revisión del trading plan

Análisis de las **97 operaciones reales** registradas en
`B20x50 - CL Beta plan 30d 22-10.xlsx` (cuenta real, 22/10/2025 → 26/06/2026),
contrastadas con las reglas de `Trading Plan Personal.docx`.

## Resultado en una línea

El winrate fue **idéntico (35,4 %) en las dos mitades del período**, pero la primera
ganó $525 y la segunda perdió $2.074. Lo que se rompió no fue la lectura del mercado
sino el ratio riesgo/beneficio: **el R cayó de 2,04 a 1,10**.

El ratio 2:1 se respetó en cada operación. Lo que no se mantuvo constante fue el riesgo
en dólares: **$121,63 de media cuando la operación ganó y $155,79 cuando perdió**, un
28 % más. Eso solo lleva el R de 2,00 a 1,56, y el medido fue 1,53 — no hace falta ningún
otro factor para explicar la pérdida del año. El origen es la dispersión del stop: en MCL
el más ancho fue 18 veces el más estrecho, y el tamaño de la posición no compensó.

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

- **C1 — tres escenarios de stop fijo según el ATR, todos con el mismo riesgo en
  dólares** ($150). Los números salen redondos: 15 tk × CL 1c = 30 tk × MCL 5c =
  50 tk × MCL 3c = 75 tk × MCL 2c = $150 exactos. Es aritmética pura y no tiene
  contrapartida: no reduce operaciones ni exige acertar más.
- **C2 — el ratio se queda en 2:1.** Una versión anterior recomendaba 2,5:1; las capturas
  de 2026 lo desmienten. De cuatro ganadoras medidas el precio llegó a 2,11R, 2,28R, 2,42R
  y 3,05R: sólo una habría alcanzado un objetivo a 2,5R, y las otras tres habrían vuelto
  hasta el stop. Haría falta que el 81 % llegara; la muestra dice 25 %.
- **C4 — la ventana operativa abre a los 30 minutos.** 13 operaciones en la primera media
  hora, 1 ganadora, −$1.448, p=0,029. Es la corrección de mayor impacto: vale +10R contra
  los +6R del riesgo fijo.
- **C3 — ninguna operación se cierra por debajo de 1R.** Cuatro ganadoras del año
  cobraron entre 0,03R y 0,21R: el 12 % de las ganadoras aportando $69.

## Pendiente

**MFE y MAE están vacíos en 96 de las 97 operaciones.** Las capturas de 2026 permitieron
reconstruirlo para cuatro ganadoras, y con eso alcanzó para descartar el 2,5:1. Quedan
dos preguntas abiertas que el resto de las capturas puede responder: hasta dónde llega el
precio en las ganadoras (para confirmar que 2R es el objetivo correcto) y en cuántas
perdedoras el stop se toca por una perforación antes de que el precio se vaya en la
dirección leída — que sería una mejora de winrate, lo único que el ajuste de geometría no
puede dar.

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
| `beta_r.py` | Stop y target en ticks por contrato, por instrumento y por mes |
| `beta_reglas.py` | Cumplimiento de las reglas del plan y atribución de la pérdida |
| `beta_oos.py` | Efecto de cada corrección y tabla de esperanza |
| `lotes.py` | Estructura de lotes y ganadoras según número de contratos |
| `rmult.py` | Cada ganadora medida en múltiplos de R |
| **`hipo.py`** | **El test decisivo: riesgo en dólares al ganar contra al perder** |
| `buckets.py` | Los tres escenarios de stop con comisiones incluidas |
