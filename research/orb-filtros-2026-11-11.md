# Estudio: ¿qué filtros mejoran la ruptura del rango de apertura (ORB)?

- **Datos:** barras de 5 minutos de Yahoo Finance, del 2026-09-03 al 2026-11-11.
- **Muestra:** 500 acciones de EE. UU. con más volumen en dólares y precio de $5 o más; 49 sesiones con historia suficiente.
- **Herramienta:** `.claude/skills/trader-scanner/lab.py`.

## Reglas simuladas

Son las mismas del skill:
- **Rango:** máximo y mínimo de los primeros 15 minutos (9:30 a 9:45 ET).
- **Entrada:** al cierre de la primera barra que cierra por fuera del rango. Largo por arriba, corto por abajo.
- **Stop:** en la mitad del rango. **Objetivo:** 2R (y 1R en la segunda tabla).
- **Horario:** sin entradas nuevas después de las 15:30; salida obligada a las 15:55.
- **Supuesto conservador:** si una barra toca el stop y el objetivo a la vez, cuenta como stop.
- **Costo:** 1 centavo por acción en la entrada y 1 en la salida, ya descontado.

## Cómo leer la tabla

- **avg R:** resultado promedio por operación, en múltiplos del riesgo. Por ejemplo, +0.30 significa ganar en promedio 0.3 veces lo arriesgado.
- **1st / 2nd:** el mismo promedio en la primera y en la segunda mitad del período. Si un filtro sirve, debería ser positivo en las dos mitades.
- **t:** estadística t agrupada por día. Con |t| > 2 es poco probable que el resultado sea casualidad.

## Conclusiones

1. **La ORB sola pierde dinero**, tanto en largos como en cortos: unos −0.06R por operación con t ≈ −2.3. Coincide con lo que dice la literatura sobre esta estrategia.
2. **En largos, ningún filtro dio una ventaja robusta.** Volumen relativo alto, gap y SPY a favor quedan cerca de 0R, y ninguno supera |t| > 2 con las dos mitades positivas.
3. **Lo único consistente fue el corto en acciones "en juego" a la baja:** gap a la baja de 2 % o más y volumen relativo de 2x o más.
   - Con objetivo de 2R: +0.31R por operación, positivo en las dos mitades (+0.16 / +0.35), t = 1.77.
   - Con objetivo de 1R: +0.23R, positivo en las dos mitades (+0.13 / +0.25), **t = 2.11**.
   - Una versión más estricta (volumen relativo ≥ 3 y gap ≥ 3 % en cualquier dirección) también da positivo en las dos mitades.
4. **Agregar el filtro del SPY no mejora** ese corto.
5. **El filtro de VWAP no aporta nada:** toda ruptura del rango ya está del lado correcto del VWAP.

## Advertencias

- **Muestra corta:** 49 sesiones son un solo régimen de mercado. Lo que funcionó acá puede dejar de funcionar.
- **Sesgo de selección:** las 500 acciones se eligieron por su volumen de hoy, no por el de cada día del estudio, lo que favorece un poco a las acciones "activas".
- **Costos reales de los cortos:** no se simuló la disponibilidad de acciones para pedir prestadas, la regla de venta en corto (después de una caída del 10 % solo se puede vender en corto en un "uptick"), ni el slippage en acciones con gaps grandes.
- **No es una predicción ni un consejo financiero.**

## Tablas completas

### Objetivo 2R

```
Scanner Lab: 502 symbols, 49 sessions (2026-09-03 to 2026-11-11), target 2R, cost 1 c/share/side.
avg R is after costs. 1st/2nd half split at 2026-10-08. t = day-clustered t-stat (|t|>2 is worth a look).

LONG   filter                           trades  days   tgt%  stop%   avg R     1st     2nd      t
       all breakouts                     13122    49  15.0%  44.4%  -0.055  -0.140  +0.016  -2.27
       rvol >= 1.5                        2102    49  12.3%  40.9%  -0.065  -0.106  -0.038  -2.57
       rvol >= 2                          1127    49  12.6%  38.4%  -0.027  -0.026  -0.028  -1.88
       rvol >= 3                           478    49  10.9%  33.5%  +0.015  +0.020  +0.012  -1.16
       gap >= 2% with the trade           1174    46  15.2%  39.2%  -0.002  -0.047  +0.026  -2.47
       gap >= 2% against the trade        1088    49  12.7%  43.0%  -0.089  -0.237  -0.005  -2.32
       |gap| >= 2%                        2262    49  14.0%  41.0%  -0.044  -0.137  +0.011  -2.64
       on VWAP side                      13122    49  15.0%  44.4%  -0.055  -0.140  +0.016  -2.27
       SPY with the trade                 7952    48  14.1%  43.7%  -0.069  -0.172  +0.005  -3.54
       SPY against the trade              5170    47  16.4%  45.3%  -0.032  -0.098  +0.036  -0.23
       trigger vol >= 1.5x                1124    49  17.3%  43.4%  +0.002  -0.125  +0.102  -1.07
       trigger by 10:30                   8315    49  17.5%  50.5%  -0.069  -0.148  -0.008  -1.97
       trigger after 10:30                4807    49  10.7%  33.7%  -0.029  -0.126  +0.060  -1.87
       rvol>=2 + SPY with                  629    44  12.2%  35.8%  -0.001  -0.040  +0.016  -1.82
       rvol>=2 + gap>=2% with              253    39  11.5%  35.6%  -0.028  -0.074  -0.007  -1.46
       rvol>=2 + gap with + SPY with       171    30  12.9%  32.2%  +0.067  +0.118  +0.049  -1.34
       in play: rvol>=3 + |gap|>=3%        189    44   8.5%  31.2%  +0.020  -0.171  +0.087  -1.06
       top 5 a day by rvol                 245    49  10.2%  36.7%  -0.048  -0.178  +0.076  -0.67

SHORT  filter                           trades  days   tgt%  stop%   avg R     1st     2nd      t
       all breakouts                     13188    49  15.3%  45.6%  -0.069  -0.124  -0.014  -2.38
       rvol >= 1.5                        2182    49  15.1%  39.4%  +0.020  -0.093  +0.108  -1.71
       rvol >= 2                          1141    49  13.8%  38.5%  +0.012  -0.090  +0.095  -1.03
       rvol >= 3                           480    49  11.5%  38.5%  -0.025  -0.065  +0.010  +0.22
       gap >= 2% with the trade           1134    48  24.5%  33.6%  +0.272  -0.249  +0.421  +0.34
       gap >= 2% against the trade        1001    49  11.0%  45.3%  -0.139  -0.015  -0.247  -1.03
       |gap| >= 2%                        2135    49  18.2%  39.1%  +0.079  -0.097  +0.168  -0.67
       on VWAP side                      13188    49  15.3%  45.6%  -0.069  -0.124  -0.014  -2.38
       SPY with the trade                 8502    47  15.9%  44.5%  -0.045  -0.147  +0.068  -2.44
       SPY against the trade              4686    48  14.3%  47.6%  -0.114  -0.077  -0.148  -1.85
       trigger vol >= 1.5x                1019    49  14.6%  48.0%  -0.117  -0.062  -0.171  -2.96
       trigger by 10:30                   8750    49  17.5%  50.7%  -0.082  -0.119  -0.044  -2.32
       trigger after 10:30                4438    49  11.1%  35.6%  -0.044  -0.134  +0.044  -2.09
       rvol>=2 + SPY with                  768    47  14.2%  39.5%  -0.007  -0.122  +0.101  -1.91
       rvol>=2 + gap>=2% with              241    47  20.7%  32.0%  +0.308  +0.159  +0.346  +1.77
       rvol>=2 + gap with + SPY with       171    35  22.8%  33.3%  +0.302  +0.124  +0.345  +1.40
       in play: rvol>=3 + |gap|>=3%        170    45  12.4%  31.8%  +0.160  +0.128  +0.170  +1.56
       top 5 a day by rvol                 245    49   9.8%  37.6%  -0.024  +0.057  -0.101  -0.32

Research on ~40 sessions, not a prediction. A row only counts if both halves agree and |t| > 2.
```

### Objetivo 1R

```
Scanner Lab: 502 symbols, 49 sessions (2026-09-03 to 2026-11-11), target 1R, cost 1 c/share/side.
avg R is after costs. 1st/2nd half split at 2026-10-08. t = day-clustered t-stat (|t|>2 is worth a look).

LONG   filter                           trades  days   tgt%  stop%   avg R     1st     2nd      t
       all breakouts                     13122    49  37.8%  39.8%  -0.057  -0.128  +0.003  -2.84
       rvol >= 1.5                        2102    49  34.2%  37.7%  -0.065  -0.108  -0.036  -2.93
       rvol >= 2                          1127    49  35.0%  35.3%  -0.028  -0.035  -0.023  -1.83
       rvol >= 3                           478    49  34.3%  30.8%  +0.028  +0.017  +0.034  -0.57
       gap >= 2% with the trade           1174    46  39.9%  34.9%  +0.014  -0.091  +0.077  -2.28
       gap >= 2% against the trade        1088    49  36.6%  38.1%  -0.040  -0.164  +0.030  -1.78
       |gap| >= 2%                        2262    49  38.3%  36.4%  -0.012  -0.126  +0.054  -2.47
       on VWAP side                      13122    49  37.8%  39.8%  -0.057  -0.128  +0.003  -2.84
       SPY with the trade                 7952    48  36.6%  39.7%  -0.072  -0.161  -0.008  -3.83
       SPY against the trade              5170    47  39.5%  39.8%  -0.033  -0.086  +0.021  -0.55
       trigger vol >= 1.5x                1124    49  38.3%  39.4%  -0.054  -0.151  +0.023  -2.42
       trigger by 10:30                   8315    49  40.6%  44.7%  -0.071  -0.143  -0.014  -2.72
       trigger after 10:30                4807    49  32.8%  31.2%  -0.032  -0.105  +0.035  -2.16
       rvol>=2 + SPY with                  629    44  32.6%  33.7%  -0.030  -0.104  +0.002  -2.53
       rvol>=2 + gap>=2% with              253    39  35.2%  32.0%  +0.007  -0.052  +0.034  -0.66
       rvol>=2 + gap with + SPY with       171    30  33.9%  31.0%  +0.019  +0.014  +0.021  -1.80
       in play: rvol>=3 + |gap|>=3%        189    44  31.2%  28.6%  +0.058  -0.082  +0.108  -0.06
       top 5 a day by rvol                 245    49  30.6%  34.3%  -0.036  -0.157  +0.080  -0.56

SHORT  filter                           trades  days   tgt%  stop%   avg R     1st     2nd      t
       all breakouts                     13188    49  38.7%  40.3%  -0.055  -0.096  -0.014  -2.49
       rvol >= 1.5                        2182    49  40.2%  34.9%  +0.016  -0.081  +0.091  -1.77
       rvol >= 2                          1141    49  38.0%  34.8%  -0.004  -0.097  +0.071  -1.48
       rvol >= 3                           480    49  35.8%  34.6%  -0.015  -0.095  +0.052  +0.33
       gap >= 2% with the trade           1134    48  50.9%  29.9%  +0.175  -0.201  +0.283  +0.35
       gap >= 2% against the trade        1001    49  30.8%  41.6%  -0.136  -0.076  -0.187  -2.08
       |gap| >= 2%                        2135    49  41.5%  35.4%  +0.029  -0.120  +0.105  -1.69
       on VWAP side                      13188    49  38.7%  40.3%  -0.055  -0.096  -0.014  -2.49
       SPY with the trade                 8502    47  38.9%  39.9%  -0.049  -0.108  +0.017  -2.90
       SPY against the trade              4686    48  38.2%  41.1%  -0.067  -0.071  -0.064  -1.24
       trigger vol >= 1.5x                1019    49  37.6%  42.3%  -0.085  -0.037  -0.133  -2.64
       trigger by 10:30                   8750    49  41.2%  44.3%  -0.066  -0.098  -0.034  -2.45
       trigger after 10:30                4438    49  33.7%  32.4%  -0.033  -0.092  +0.025  -2.39
       rvol>=2 + SPY with                  768    47  37.6%  36.1%  -0.030  -0.115  +0.050  -2.27
       rvol>=2 + gap>=2% with              241    47  50.2%  27.0%  +0.227  +0.129  +0.252  +2.11
       rvol>=2 + gap with + SPY with       171    35  49.7%  29.2%  +0.184  +0.021  +0.224  +1.35
       in play: rvol>=3 + |gap|>=3%        170    45  41.2%  27.6%  +0.137  +0.058  +0.164  +1.71
       top 5 a day by rvol                 245    49  33.1%  33.9%  -0.032  +0.026  -0.088  -0.57

Research on ~40 sessions, not a prediction. A row only counts if both halves agree and |t| > 2.
```

---

## Corrección (2026-11-12): la ventaja de los cortos depende de pocos días

Repetí el estudio con más acciones (1.500, unas 9.500 rupturas con gap a favor) y probé unas 48.000 combinaciones de filtros y formas de ejecutar la operación. Una parte de los días se usó para elegir la combinación y otra parte para validarla.

- **El corto "en juego"** (rango de 15 minutos, stop en la mitad del rango, volumen relativo ≥ 2 y gap ≥ 2 %) da +0,12R por operación en total. Pero **sin el mejor día (2026-11-05) da −0,02R, y sin los 3 mejores días da −0,14R.** La "consistencia" que vi en las dos mitades del período venía de días de venta generalizada del mercado.
- **La mejor combinación encontrada** acierta el objetivo de 2R en el 48,6 % de los casos, con +0,45R por operación. Le exige al corto volumen relativo ≥ 1,5, gap ≥ 2 % a favor, el SPY por debajo de su VWAP y que la acción también haya caído el día anterior, y pone el stop en el máximo de la barra que da la señal. Pero **111 de sus 368 operaciones caen en un solo día (2026-11-05)**. Sin los 3 mejores días acierta el 29 % y da −0,13R.
- **Lo que sí es estructural:** poner el stop en el extremo de la barra que da la señal, en lugar de la mitad del rango, sube la tasa de objetivos de 2R de ~17 % a ~40 %, porque el objetivo queda más cerca. Aun así, en los días normales el resultado sigue sin ser positivo.
- **Conclusión:** con 49 sesiones no hay evidencia de un sistema ORB en acciones que acierte ~50 % con objetivo 2:1 de forma robusta. Lo que existe es un efecto de **días de pánico**: cuando el mercado entero vende, los cortos con gap a la baja funcionan muy bien. Para estudiar un filtro que detecte esos días hacen falta muchos más días de historia.
