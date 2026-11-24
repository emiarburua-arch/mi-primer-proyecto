# Backtest 2026 – Entrada tipo 1 (giro tras manipulación de sesión)

- **Datos:** NQ 1 minuto (NinjaTrader, contratos 03-26, 06-26, 09-26, 12-26), 2026-01-02 a 2026-11-23.
  Faltan datos del 28/02 al 11/03, del 01/06 al 07/06 y del 01/09 al 09/09.
- **Código:** `trading-plan/backtest/backtest.py` (reglas del plan v1.7).
- **Qué se prueba:** solo la entrada tipo 1 (barrida de máx/mín de Asia o Europa + giro), ventana 09:30–11:30 ET.
- **No incluido todavía:** entrada tipo 2 (continuación), filtro de noticias, niveles semanales/lunes.
- **Costos:** 1,50 USD por micro ida y vuelta + 1 tick de deslizamiento en el stop. Target por trade-through de 1 tick.

## Verificación con las capturas

| Captura | Día en los datos | Coincidencia |
|---|---|---|
| C2/C4/C5 | 2026-11-10 | Europa 27590–28044,25; máximo 28090 a las 10:00; mínimo 27516 a las 12:40 ✅ |
| C8 | 2026-11-20 | Europa 26000–26447,75 ✅ |

Los horarios del gráfico del trader están en hora de Nueva York.

## Resultado 1 – Plan tal como está escrito: 0 trades

- 188 gatillos (vela de confirmación) en 2026 sin filtro de volumen; 39–41 con filtro de volumen.
- **Todos se descartan porque el stop no cubre el pivote.**
- Distancia entrada → pivote: mediana **66 pts** (25%: 49 pts, 75%: 109 pts).
- Stop disponible: 18,75 pts (ATR < 100) o 37,5 pts (ATR 100–200). El ATR(14) de 60m superó 200 en solo 1 de 188 gatillos.
- Caso C5 (10/11, 13:30): el ATR(14) de 60m calculado es **186** → stop de 150 ticks → no cubre el pivote (27582,50).
  El trader indicó ATR > 200: hay que comparar con el valor de NinjaTrader.

## Resultado 2 – Variantes hipotéticas (NO son el plan)

Para ver si hay ventaja cuando el stop sí entra:
- `fijo300`: stop siempre de 300 ticks (75 pts, 1 micro).
- `minimo_cubre`: el stop más chico de 75/150/300 ticks que cubre el pivote (regla descartada en P17f).

| Variante | Trades | Aciertos | R medio | R total | PF | Máx. DD (R) | t |
|---|---|---|---|---|---|---|---|
| fijo300, sin filtro de volumen, sin sesgo | 54 | 25,9% | −0,30 | −16,4 | 0,58 | 19,6 | −1,86 |
| fijo300, volumen en reingreso, sin sesgo | 11 | 27,3% | −0,28 | −3,1 | 0,59 | 3,7 | −0,78 |
| fijo300, volumen en reingreso, sesgo de fondo | 7 | 42,9% | +0,14 | +0,9 | 1,27 | 2,0 | 0,26 |
| minimo_cubre, sin filtro de volumen, sin sesgo | 54 | 25,9% | −0,28 | −15,1 | 0,62 | 18,4 | −1,63 |
| minimo_cubre, volumen en reingreso, sesgo de fondo | 7 | 42,9% | +0,36 | +2,5 | 1,72 | 2,0 | 0,61 |

Con 2:1 el punto de equilibrio es 33,3% de aciertos. Tabla completa: `resumen.csv`.

## Lectura

1. Tal como está definido, el plan **no opera** en NQ 2026: los stops (18,75 / 37,5 pts) son menores que una vela
   media de 5m (ATR(14) 5m mediana ~48 pts) y que la distancia típica al pivote.
2. En la versión con más trades (54), el resultado es **negativo** (−0,30 R/trade, aciertos 26%): no hay ventaja.
3. Con filtros (volumen + sesgo de fondo) quedan 7–11 trades: **demasiado pocos** para concluir nada.
4. La regla de volumen en el reingreso no detecta el caso C5: la vela de reingreso tuvo volumen relativo 0,9; el pico
   de volumen (1,75) fue en la vela de la perforación (12:35).
