# El giro que faltaba: fadear el MES, no romperlo

## Lo que dijeron los datos limpios

NinjaTrader corrió Primer Empuje (breakout) sobre **un solo contrato MES SEP26, ene–ago 2026, 32
operaciones**. Al ser un contrato único no hay artefactos de roll: es la data más limpia que
tenemos. Resultado real:

| Dirección | n | WR | Neto | PF | media/op |
|---|---|---|---|---|---|
| **A favor (breakout)** | 32 | 28 % | **−$1.674** | 0,35 | −$52 |
| **Fadeado (inversión exacta)** | 32 | 72 % | **+$1.514** | 2,87 | +$47 |

Negativo el breakout en 6 de 8 meses (marzo 0 % −$658, abril 0 % −$329). **El breakout mecánico no
tiene ventaja en MES.** Mi backtest de Python (PF 1,41) era un espejismo de datos sucios: el
continuo stitcheado inflaba los rangos de apertura en cada roll.

## Por qué el fade, y por qué no es data mining

Como el **stop del breakout y el objetivo del fade están en el mismo nivel de precio** (y el primer
toque decide), invertir las 32 operaciones reales es exacto, no una simulación optimista. Y el
resultado confirma lo que ya estaba escrito en el **doc 13**: los índices (ES, NQ) **revierten**
intradía; el petróleo (CL) **tiene momentum**. Elegimos la dirección equivocada para el MES.
El fade positivo (72 % WR, PF 2,87) es la misma tesis vista desde el lado correcto.

El fade además tiene asimetría favorable: gana el ancho del rango (+1R+ε) y arriesga 1R, al revés
del breakout.

## Implementación

`ninjascript/PrimerEmpuje.cs` ahora tiene un parámetro **`Fade`** (mismo código, un tilde):
- `Fade=false` → sigue la ruptura (para CL).
- `Fade=true` → fadea: objetivo = extremo opuesto del rango, stop = 1R más allá de la entrada.

Y `UsarFiltros` para probar con/sin media 200 + dirección del día previo (esos filtros se pensaron
para el breakout; en el fade hay que revalidarlos).

## Confirmación con corrida REAL (no inversión)

Se corrió `PrimerEmpuje2` con `Fade=true` en el Strategy Analyzer sobre el mismo contrato limpio
(MES SEP26, ene–ago 2026). Resultado real de ejecución:

| Versión | n | WR | Neto | PF | media/op | Max DD (1 lote) |
|---|---|---|---|---|---|---|
| Fade sin filtros | 76 | 58 % | +$1.804 | 1,65 | +$24 | −$554 |
| **Fade con filtros** (corrida real) | 33 | **70 %** | **+$1.415** | **2,59** | +$43 | **−$276** |

Positivo en 6 de 8 meses ambas versiones. **Es el primer resultado positivo, real y sobre datos
limpios del proyecto.**

Los filtros agregan calidad: las 33 operaciones filtradas rinden +$43/op con PF 2,59 y DD de solo
−$276; las 43 extra sin filtro sumaron ~+$5/op. Menos operaciones, mejor PF, curva más suave.

**Riesgo vs topes de fondeo ($2.500 DD / $900 diario):** con 1 operación por día la pérdida diaria
máxima posible es un stop (~$178), muy por debajo de $900. Racha perdedora máxima: 3. El DD de
−$276 a 1 lote deja margen para escalar a varios contratos — con prudencia, dada la muestra de
7 meses.

## Lo que falta antes de confiar

La inversión de +$1.514 es sólida pero es **la inversión de 32 operaciones en 7 meses**. Antes de
Sim101:

1. Correr `PrimerEmpuje` con **`Fade=true`** en el Strategy Analyzer sobre el MISMO contrato limpio
   y confirmar que la corrida real reproduce el +$1.514 (debería, por la simetría).
2. Extender a **más años** y a **MNQ** (el otro índice que revierte, doc 13).
3. Revalidar los filtros para el fade (probar `UsarFiltros=false`).
4. Chequear el drawdown real contra los topes: $2.500 DD / $900 diario. Con media +$47/op y stops
   de ~$100–160, 1 contrato entra cómodo; ver rachas perdedoras máximas.

Recién con eso positivo en varios años pasa a papel en Sim101.
