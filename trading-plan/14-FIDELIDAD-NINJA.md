# Fidelidad NinjaTrader ↔ Python (Primer Empuje)

Antes de operar en papel había que probar que el NinjaScript reproduce el backtest. No lo hacía:
NinjaTrader daba **41 operaciones** (−$245) donde Python daba puñado. Se diagnosticó con una
versión con `Print()` (`ninjascript/PrimerEmpuje2_debug`) que registra, por día, qué decide cada
filtro. La salida real de NinjaTrader localizó dos causas.

## Causa 1 — filtro de volatilidad recalculado en cada vela (ya corregido)

El `orbSet`/mediana se evaluaba en cada barra, corrompiendo el historial de rangos. Se corrigió
con el flag `orbEvaluated` (una evaluación por día). Bajó de 41 a ~17 operaciones. `velasRango=30`
y `n` creciendo de a 1 por día en la salida confirman que el filtro ya opera bien.

## Causa 2 — no se respetaba la regla D3 (la corregida acá)

La regla dice **"solo la PRIMERA ruptura de la sesión cuenta"**. El NinjaScript marcaba el día como
operado (`tradedToday`) **solo al entrar**. Si la primera ruptura no pasaba los filtros, seguía
escaneando y **entraba en una ruptura posterior más favorable**. Ejemplos de la salida real:

- **01/07**: primera ruptura 10:32 BAJA (día previo alcista → `dirOK=False`, descarta correctamente).
  El día debía terminar ahí. En cambio entró 11:06 en una ruptura ALTA posterior.
- **31/07**: primera ruptura 10:23 ALTA rechazada (precio bajo la media). Entró 10:30 cuando la
  media "alcanzó" al precio.

Es el mismo tipo de artefacto optimista que hundió al giro: elegir la entrada con el diario del
lunes. **Arreglo:** la primera ruptura cierra el día, pase o no los filtros
(`tradedToday = true` apenas se detecta la ruptura). Elimina 5 operaciones espurias en la muestra
(18/06, 01/07, 28/07, 31/07, 20/08). Tras el arreglo, cada día imprime **una sola línea BREAK**.

## Lo que queda: diferencia de datos (irreducible)

Con ambas causas corregidas, NinjaTrader da ~12 operaciones y mi espejo fiel
(`backtest/primer_empuje_espejo_nt.py`, mismo continuo, misma lógica) da 7. La diferencia **no es
de lógica** sino de **datos**: mi continuo stitcheado y el de NinjaTrader difieren a nivel minuto,
sobre todo cerca de los rolls trimestrales (el **19/06 es exactamente el roll del MES**), donde el
gap entre contratos corre el rango de apertura. Ejemplo 19/06: mi rango lo=7556,00 hi=7563,75 vs
NinjaTrader lo=7533,50 hi=7562,25.

**Consecuencia:** la validación final del edge debe hacerse sobre **los datos con los que se va a
operar** (el Strategy Analyzer de NinjaTrader), no solo sobre mi continuo. La lógica ya es fiel a
las reglas; los números definitivos salen de NinjaTrader.

## Próximo paso

Recompilar `PrimerEmpuje` con el arreglo D3, correr en el Analyzer el período completo disponible,
y recién ahí leer PF / ganancia media / drawdown reales para decidir el paso a Sim101.
