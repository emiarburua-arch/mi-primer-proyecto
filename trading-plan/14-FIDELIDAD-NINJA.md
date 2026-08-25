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

## Resultado tras el arreglo — y el problema de datos que destapó

Con D3 corregido, NinjaTrader dio **exactamente 12 operaciones** (lo predicho). La **fidelidad de la
lógica quedó probada**. Pero el P&L del trimestre jun-ago 2026 fue **PF 0,44, 33 % aciertos,
−$487**. Mi backtest fiel sobre el mismo trimestre daba lo contrario: **PF 5,05, 88 %, +$704**.

Comparando operación por operación, los dos sets casi no se superponen y donde coinciden divergen
brutalmente:
- **24/06**: mi backtest entra LARGO (7472,75), NinjaTrader entra CORTO (7447,00). Opuesto.
- **25/06**: mi rango de apertura fue **7388,50–7490,50 = 102 puntos** (stop de $510); el de
  NinjaTrader, 7473–7496 = 23 puntos. Mi serie tiene un spike de 85 pts dentro de la ventana.

**Diagnóstico: mi continuo de MES está contaminado.** Rangos de apertura sistemáticamente más
anchos que los reales (31–45 pts vs 7–25), con spikes/artefactos en las semanas de roll trimestral.
Rangos inflados → objetivos inflados → ganancias falsas. **Todos mis números de MES (incluido el
PF 1,46 de 3 años) son poco confiables**, porque el stitching mete ruido en cada roll.

Es la lección del giro de nuevo: cuando la ejecución real contradice al backtest de forma
consistente, el error está en el backtest.

## Paso decisivo

No sirve seguir puliendo sobre mi data sucia. La verdad tiene que salir de **datos limpios de
ejecución**, y esos los tiene el Strategy Analyzer de NinjaTrader.

**Acción:** correr `PrimerEmpuje` (ya con el arreglo D3) en el Strategy Analyzer sobre el
**máximo histórico de MES disponible en NinjaTrader** (varios años, no 3 meses). Ese único informe
—PF, ganancia media, drawdown, positivo/negativo por año— decide go/no-go, sobre los datos con los
que se operaría de verdad. 12 operaciones no alcanzan para condenar ni salvar la estrategia; un
histórico largo y limpio, sí.

Los scripts `backtest/primer_empuje_espejo_nt.py` (espejo de conteo) y `backtest/primer_empuje_pnl.py`
(P&L por año) quedan para comparar contra NinjaTrader una vez que consigamos data limpia.
