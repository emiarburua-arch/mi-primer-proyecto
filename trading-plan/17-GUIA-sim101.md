# Guía — poner el bot a correr en Sim101 (papel, tiempo real)

El probador de estrategias (Strategy Analyzer) es backtest. Para operar en vivo simulado hay que
**activar la estrategia sobre un gráfico** conectado al feed en tiempo real. Sim101 es la cuenta de
simulación que ya viene en NinjaTrader.

## Antes de empezar
1. **Conexión de datos.** Control Center → *Connections* → conectá tu proveedor (para que lleguen
   los precios en vivo). Sin conexión, el bot no recibe velas nuevas.
2. **Zona horaria.** Tools → Options → General → Time zone = **(UTC-05:00) Eastern Time (US & Canada)**.
   (Ya la tenés.)
3. **Compilado al día.** Que `PrimerEmpujeAdaptativo` compile sin errores (F5 en el editor).

## Activar el bot en un gráfico (hacelo para MES y de nuevo para MNQ)
1. New → **Chart**. Instrumento = **MES 09-26** (el contrato del mes en curso). Tipo de barra =
   **Minute**, valor **1**.
2. Arriba, en *Days to load* (o Data Series → Days), poné **90 días** para que la media 200, el
   filtro de volatilidad y la señal de régimen arranquen ya calientes.
3. Que la serie sea **sesión completa (Globex)**, no solo RTH (la media 200 necesita el overnight).
4. Click derecho sobre el gráfico → **Strategies…**.
5. En *Available*, seleccioná **PrimerEmpujeAdaptativo** → botón para agregarla a la derecha.
6. Configurá las propiedades:
   - **Contratos** = 1
   - **K (ventana de régimen)** = 10
   - **Usar filtros media/dirección** = **True**  ← obligatorio (sin filtros rompe el drawdown)
   - **Apertura RTH (HHMM ET)** = 930
   - **Aplanado (HHMM ET)** = 1555
   - **Account** = **Sim101**
   - **Enabled** = **True**
7. **OK.** La estrategia queda corriendo en vivo sobre ese gráfico.
8. **Repetí todo para MNQ** (otro gráfico, **MNQ 09-26**, 1 minuto, misma configuración).

## Seguimiento
- Control Center → pestaña **Strategies**: ves la estrategia activa, su estado y su P&L.
- Pestaña **Orders / Positions**: las órdenes y posiciones vivas.
- Pestaña **Accounts**: el saldo de Sim101.

## Qué esperar
- Al activarla, NinjaTrader primero **recorre los 90 días históricos** (calcula la señal de régimen
  y calienta los filtros) y **después sigue en vivo**. Así no arranca del todo en frío.
- Opera **1 vez por día** como máximo, entre las 09:30 y las 10:00 ET busca la ruptura; aplana
  15:55 ET. No deja posiciones overnight.
- Los primeros días quizá no coincidan exactamente con el backtest (arranque de la señal, datos en
  vivo): es normal. Se juzga por varias semanas, no por un día.

## Reglas de la cuenta de fondeo (recordatorio)
- Tope de drawdown **$2.500**, pérdida diaria máxima **$900**.
- En el backtest de 3 años el peor drawdown fue **−$1.848** y el peor día **−$565** (1 MES + 1 MNQ):
  con margen, pero seguí de cerca las primeras semanas.

## Cuándo pasar a real
Solo si el papel acompaña a los números del backtest durante varias semanas. Ahí sí, plata real,
**1 contrato**, escalando de a poco.
