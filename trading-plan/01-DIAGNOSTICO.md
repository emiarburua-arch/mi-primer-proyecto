# Diagnóstico del TPP EA n01 — por qué el sistema pierde

Análisis sobre los registros B20x50 de backtesting y operativa real.
Fuentes: `B20x50 - CL Backtest desde 01-02-2024.xlsx`, `B20x50 - MES backtest desde
1-02-2024.xlsx`, `B20x50 - TPP EA n01.xlsx`, `B20x50 - Earn2 trade 22-04 EA01 A.xlsx`.

---

## 1. Los números

| Muestra | Período | Ops | Winrate | P&L | Profit Factor |
|---|---|---:|---:|---:|---:|
| Backtest CL | feb-24 → ene-25 | 78 | **57,7 %** | +$5.213 | 2,51 |
| Backtest MES | feb-24 → mar-24 | 24 | **29,2 %** | −$212 | 0,71 |
| Real — TPP EA n01 | feb-25 → mar-25 | 19 | **26,3 %** | −$501 | 0,66 |
| Real — Earn2Trade 22-04 | abr-25 → may-25 | 8 | **12,5 %** | −$443 | 0,31 |
| **Real combinado** | feb-25 → may-25 | **27** | **22,2 %** | **−$944** | **0,55** |

El ratio ganancia/pérdida se mantuvo estable en todas las muestras (1,85–2,14).
El sistema no falló por el lado del ratio: **falló por winrate**.

### El umbral que importa

Con stop de 10 ticks y target de 20 ticks en CL con 1 contrato, neto de comisiones
($5,32 round-turn):

- ganadora = **+$194,68**
- perdedora = **−$105,32**
- R neto = **1,85**
- **winrate de breakeven = 35,1 %**

El real dio 22,2 %. Está 13 puntos por debajo del punto de equilibrio. Esa es toda
la explicación de la pérdida: no es gestión, no es tamaño, no es disciplina.

---

## 2. No fue mala suerte

Si el sistema fuese realmente del 57,7 % que dio el backtest, la probabilidad de
sacar 6 ganadoras o menos en 27 operaciones es del **0,019 %** (1 en 5.200).

Intervalos de confianza al 95 %:

- backtest CL (n=78): **46,6 % – 68,0 %**
- real (n=27): **10,6 % – 40,8 %**

Apenas se tocan, y el real cae casi entero por debajo del breakeven del 35 %.
La conclusión estadística es que **el 57,7 % del backtest no describe al sistema
tal como se puede operar en vivo**.

### La señal de alarma ya existía antes de operar en real

El backtest de MES, con el mismo método, dio **29,2 % de winrate y profit factor
0,71** sobre 24 operaciones, y se abandonó a las 5 semanas. Es decir:

- una sola muestra dice 57,7 %: el backtest manual de CL, construido mirando el
  gráfico hacia atrás;
- dos muestras independientes dicen 22–29 %: el backtest de MES y toda la
  operativa en vivo.

La muestra discordante es justamente la única en la que se conocía el desenlace al
momento de marcar la entrada. Eso es sesgo de backtest manual (*hindsight*): con la
vela siguiente a la vista, "estructura + vela de confirmación" se reconoce con
mucha más generosidad en los sitios donde funcionó.

Un dato coherente con esto: el backtest registra 78 operaciones en 61 días sobre
~250 hábiles. Se operó apenas el 24 % de los días disponibles. Un intradía de dos
horas en M5 sobre CL genera muchas más ventanas que ésas.

---

## 3. La causa mecánica: el stop está dentro del ruido

De las 27 operaciones reales, **20 salieron por stop exacto de −10 ticks y 6 por
target exacto de +20**. Una sola salió distinto. El sistema es completamente
binario, y el lado que domina es el stop.

La preparación de sesión del 14/02/2025 registra **ATR ≈ 0,317 en M60**, es decir
unos 32 ticks de rango medio por hora. Con eso:

- stop de 10 ticks = **0,31 × ATR horario**
- target de 20 ticks = **0,63 × ATR horario**

Se le está pidiendo al precio que no retroceda ni un tercio de lo que se mueve en
una hora normal. A esa distancia el stop no mide que la hipótesis se invalidó:
mide ruido.

Los propios comentarios del registro histórico dicen exactamente eso, una y otra vez:

> "ME SACA EN EL EXACTO TICK DE MI STOP, Y VA AL TARGET"
> "LA LECTURA ESTABA BIEN, LA MECHA ERA MUY GRANDE, ME SACO RAPIDAMENTE Y CONTINUA AL TARGET"
> "llego exactamente a nuestro stop y de ahi directo al BE"
> "me saca con una mecha por debajo del minimo, ingresamos, sale target"

El diagnóstico ya estaba escrito en el diario. Nunca se trasladó al plan.

Hay además un factor de régimen: el backtest cubre feb-24 → ene-25, y la operativa
real de la última cuenta cae en **abril-mayo 2025**, uno de los períodos de mayor
volatilidad del crudo en años. El mismo stop de 10 ticks fijos vale cosas muy
distintas en un régimen y en otro, y el plan lo dejó fijo.

---

## 4. El agujero de datos que impide corregir con precisión

**Las columnas MFE y MAE están vacías en las cuatro planillas.** Sin ellas no se
puede distinguir entre los dos diagnósticos posibles, que exigen correcciones
opuestas:

| Si el MFE típico de las perdedoras es… | Significa | Corrección |
|---|---|---|
| alto (12–19 ticks) | la entrada es buena, el target de 20 está fuera de alcance | bajar/parcializar el target, mover a BE tarde |
| bajo (0–5 ticks) | la entrada llega tarde o el sesgo está mal | corregir el disparador, no la salida |

Y el MAE de las **ganadoras** dice cuánto respiro necesitaba realmente el stop.

Todo lo demás de este informe es sólido; esta pieza es la que falta y es gratis
conseguirla. Es la corrección de mayor valor del documento.

---

## 5. Dónde se pierde el dinero (cortes)

### Por momento de la sesión (ajustado por el cambio de horario USA)

| Ventana | Backtest | Real |
|---|---|---|
| 1.ª hora (0–59 min) | n=30 · 53,3 % · +$1.577 | n=7 · **42,9 % · +$163** |
| 2.ª hora (60–119 min) | n=47 · 59,6 % · +$3.442 | n=17 · **17,6 % · −$890** |
| Fuera de ventana (>2 h) | n=1 | n=3 · **0 % · −$216** |

La primera hora es lo único que quedó en positivo en vivo. La segunda hora
concentra prácticamente toda la pérdida. Ojo: n=7 en la primera hora es muy poco
para tratarlo como conclusión firme, pero la dirección es consistente.

Las 3 operaciones de mayo entradas pasadas los 120 minutos **estaban fuera del
horario que fija el plan** y las tres perdieron.

### Por patrón

| Patrón | Backtest | Real |
|---|---|---|
| ESTRUC+VC | n=39 · 59,0 % | n=14 · **28,6 % · −$274** |
| ESTRUC+FV | n=34 · 52,9 % | n=12 · **16,7 % · −$664** |

El disparador de falta de volumen se degradó más que la vela de confirmación. Es
también el más subjetivo de los dos: qué vela cuenta como "la corrección" es una
decisión del operador, y en backtest se elige distinto que en vivo.

### Disciplina

26 de 27 operaciones marcadas como disciplinadas. **La única indisciplinada perdió
$5,32.** El problema no es la ejecución: el trader está siguiendo un plan que no
tiene ventaja. Vale la pena decirlo explícitamente porque la conclusión natural
después de 8 stops seguidos es "me falta disciplina", y los datos dicen lo contrario.

### Otros

- Racha máxima de perdedoras: **8 en real** (5 en backtest).
- Drawdown real: **−$1.106** de los $2.000 permitidos por la prueba: 55 % consumido.
- Comisiones: $143,64 sobre −$944, el **15 % de la pérdida**.

---

## 6. Qué probabilidad real hay de superar la prueba

Simulación Monte Carlo (40.000 corridas) de la prueba Earn2Trade 50k: objetivo
+$3.000, drawdown máximo $2.000, tope de 2 stops por día, CL 1 contrato, R=1,85.

| Winrate | P(superar la prueba) | Esperanza por op | Aprox. mensual (1,3 ops/día) |
|---:|---:|---:|---:|
| 22,2 % (el real) | **0,0 %** | −$38,72 | −$1.057 |
| 30 % | 0,7 % | −$15,32 | −$418 |
| 35 % (breakeven) | 22,1 % | −$0,32 | −$9 |
| 40 % | 79,1 % | +$14,68 | +$401 |
| 45 % | 97,8 % | +$29,68 | +$810 |
| 50 % | 99,8 % | +$44,68 | +$1.220 |

La lectura importante: **entre el 30 % y el 40 % de winrate se juega todo**. Es un
margen de 10 puntos que separa la ruina segura del aprobado casi seguro. Por eso
la prioridad no es "operar más", es medir bien dónde está ese número.

### Cuántas operaciones hacen falta para saberlo

Test de una cola contra el breakeven del 35 %, α=5 %, potencia 80 %:

| Si el winrate verdadero fuese… | Operaciones necesarias | Tiempo a 1,3 ops/día |
|---|---:|---:|
| 42 % | ~294 | ~11 meses |
| 45 % | ~145 | ~5 meses |
| 50 % | ~65 | ~2,5 meses |
| 55 % | ~37 | ~1,5 meses |

Con 27 operaciones no se puede concluir nada sobre una corrección. Es el motivo
por el que la fase siguiente tiene que ser barata: a $105 de riesgo por operación,
juntar 100 operaciones cuesta $10.500 de exposición y no cabe en una cuenta con
$2.000 de drawdown.

---

## 7. Resumen

1. El sistema pierde porque su winrate real (22 %) está muy por debajo del
   breakeven (35 %), no por gestión ni por psicología.
2. El 57,7 % del backtest no es reproducible en vivo; hay sesgo de hindsight, y el
   backtest de MES ya lo anticipaba.
3. La causa mecánica más probable es un stop de 10 ticks que equivale a 0,3 × ATR
   horario: el precio lo toca por ruido antes de resolver la hipótesis.
4. No se registró MFE/MAE, y sin esos dos números no se puede elegir entre corregir
   la entrada o corregir la salida.
5. La disciplina no es el problema. 26 de 27 operaciones fueron ejecutadas según plan.

Las correcciones concretas están en `02-PLAN-CORREGIDO.md`.
