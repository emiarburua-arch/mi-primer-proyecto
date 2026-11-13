# Pre-registro — motor v3 (ruptura del rango inicial con sesgo)

Fijado el 2026-11-13, **antes** de ver datos de 2025. Nada de esto se cambia después de mirar 2025.

## Por qué este motor

Laboratorio sobre ene–nov 2026 (212 días, `backtest/gold_lab.py`), esperanza por trade neta de costos:

| Motor | Sin sesgo | Sesgo mecánico (56% acierto) | Sesgo al 60% | Sesgo perfecto |
|---|---|---|---|---|
| E0 pullback EMA20 2R (plan v2) | −0,18R | +0,00R | −0,08R | +0,22R (PF 1,34) |
| E1 barrida de Londres | −0,06R | +0,01R | +0,07R | +0,50R (PF 1,91) |
| **E2 ruptura rango 08:30–09:30** | **+0,04R** | **+0,06R** | **+0,19R** | **+0,60R (PF 2,97)** |
| E3 pullback con stop móvil | −0,07R | +0,16R | +0,03R | +0,39R (PF 1,57) |

Ventanas vecinas de E2 (control de sobreajuste): 08:30–09:00 → +0,07R al 60%; 08:00–09:00 → +0,25R al 60%.
Ventanas que terminan 10:00 o más tarde casi no operan (el medio rango supera $15).

Advertencia: se probaron 4 motores y 4 ventanas sobre los mismos datos. La elección tiene sesgo de
selección hasta que 2025 la confirme.

## Reglas v3 (principal)

- MGC, 5 m, sesgo diario del trader (LARGO / CORTO / NEUTRAL + nivel de invalidación).
- Rango inicial: máximo y mínimo de las velas 08:30–09:25 (cierre 09:30) hora NY.
- Señal: desde las 09:30 hasta las 11:30, la primera vela de 5 m que **cierra** fuera del rango a favor
  del sesgo (si vuelve adentro y cierra otra vez afuera, es señal nueva).
- Entrada: orden stop 1 tick más allá del extremo de la vela de señal, válida 2 velas.
- Stop: punto medio del rango inicial. Mínimo 0,5 ATR(14); si la distancia supera $15, no se opera.
- Contratos = mín(5, piso(150 / (distancia × 10))). Objetivo 2R. Cierre forzado 13:00 NY.
- Máx. 2 trades/día, un ganador cierra el día, 2 perdedores cierran el día, −4R semanal.
- Variante alternativa pre-registrada: rango 08:00–08:55 (cierre 09:00), señal desde 09:00. Resto igual.

## Criterio de aprobación en 2025 (fuera de muestra)

Para la versión principal y por separado para la alternativa:
1. Sin sesgo: esperanza ≥ 0.
2. Sesgo simulado al 60% de acierto: esperanza > 0 en al menos el 75% de las simulaciones.
3. Sesgo perfecto: profit factor ≥ 1,5.
