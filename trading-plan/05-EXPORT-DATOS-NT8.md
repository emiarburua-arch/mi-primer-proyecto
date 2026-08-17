# Guía · exportar datos de CL desde NinjaTrader 8

Objetivo: sacar de NT8 el **histórico de CL** en dos temporalidades (M5 y M60) **con volumen**,
en un formato que el detector de backtest pueda leer sin retoques. Es el **paso 2** de la ruta
(el spec `04-SPEC.md` es el paso 1).

---

## 0 · Qué necesitamos exactamente

| Dato | Valor | Por qué |
|---|---|---|
| Instrumento | **CL ##-## (WTI Crude Oil)** — continuo | MCL es el mismo subyacente; backtesteamos CL y aplicamos tick/comisión de MCL (§4 del spec) |
| Temporalidades | **M5** y **M60** | M5 = detección y ejecución · M60 = ATR(14) y contexto |
| Campos | fecha-hora, open, high, low, close, **volume** | El volumen es obligatorio: lo usa el disparador FV y el test de manipulación del giro |
| Zona horaria | la del **exchange** (o anotada y constante) | Para resolver sesiones (Europa, cash) y DST sin errores |
| Rango | lo más largo que tengas cargado (varios años) | El objetivo es el backtest largo que con 97 ops no alcanzaba |

> Antes que nada tenés que **tener las barras cargadas** en NT8. Si sólo tenés unos meses,
> primero hay que bajar histórico (ver §3).

---

## 1 · Verificar/Descargar el histórico primero

NT8 sólo exporta lo que ya tiene en su base de datos local. Para asegurarte de cuánto hay:

1. **Tools → Historical Data** (o `Control Center → Tools → Historical Data`).
2. Pestaña **Edit**. En *Instrument* poné `CL` y elegí el continuo (`CL ##-##`).
3. Mirá el rango de fechas disponible por *Type*: **Minute** (de ahí salen M5 y M60) y **Tick**
   si lo tuvieras.
4. Si te falta histórico, pestaña **Load** → seleccioná `Minute`, el rango de fechas que querés,
   y descargá desde tu proveedor de datos. (Con datos de continuo/rollover, ver §4.)

> **Importante sobre volumen:** si tu proveedor es sólo de una parte de la sesión, el volumen
> puede venir incompleto. Verificá que el volumen no sea 0 o constante en las barras — si lo es,
> el detector de FV y de manipulación no va a servir y hay que conseguir mejor fuente.

---

## 2 · Exportar a CSV (el método directo)

**Tools → Historical Data → pestaña Export.**

1. *Instrument*: `CL ##-##` (el continuo).
2. *Type*: **Minute**. (NT guarda todo en barras de minuto; de ahí generás M5 y M60 — ver nota abajo.)
3. *From / To*: el rango completo que tengas.
4. Elegí carpeta y **Export**. Sale un archivo (por defecto comprimido) con líneas tipo:

```
yyyyMMdd HHmmss ;open;high;low;close;volume
```

o, según versión/locale, separado por `;` con la fecha en una sola columna.

### 2.1 · El detalle de M5 vs M60

NT exporta **barras de 1 minuto** (o la base que tengas). Dos caminos:

- **Recomendado — exportar Minute (M1) una sola vez** y que el script de Python arme M5 y M60
  por *resampling* (agrupar de a 5 y de a 60, sumando volumen). Es más robusto y evita exportar
  dos veces. Es lo que asume `04-SPEC.md`.
- **Alternativa** — si preferís exportar ya en M5 y M60: abrí un **Chart** de CL en 5 min, luego
  otro en 60 min, y usá el export del chart (ver §5). Pero el resampling desde M1 es mejor.

> **Pedime a mí el resampling**: si me pasás el CSV de **M1 con volumen**, yo genero M5 y M60
> exactos en el detector. Con eso alcanza. No hace falta que exportes tres archivos.

---

## 3 · Si el export de Historical Data no te da volumen o formato claro

Camino por **gráfico**, que es más visual:

1. Abrí un **Chart** de `CL ##-##` en **5 minutos**, con todo el histórico cargado
   (Data Series → Days to load: alto, o Bars to load).
2. Verificá que el chart muestre volumen (panel inferior).
3. Con el chart activo: **botón derecho → aparece menú**; buscá una opción de exportar, o usá
   el add-on de export de barras. Si tu versión no lo trae nativo, usá el método §2 (Historical
   Data Export), que es el estándar.

---

## 4 · Rollover / continuo (importante para no pegar saltos)

CL vence cada mes. Hay dos formas del continuo:

- **Sin ajuste (raw)**: cada mes salta al nuevo contrato → hay *gaps* de precio en el rollover
  (≈ día 18). El **volumen** es real.
- **Back-adjusted**: NT empalma los precios para que no haya gap, pero entonces los **niveles
  absolutos históricos se desplazan** y el ATR en $ de años atrás no es comparable al de hoy.

Para nuestro backtest:

- Guardá, si podés, **qué contrato es cada barra** (columna de contrato) — el spec §1 lo pide
  para no pegar saltos.
- Si sólo podés exportar el continuo raw, **está bien**: el detector trabaja intradía (sesión
  por sesión) y los gaps de rollover caen fuera de la ventana operativa. Lo anotamos y seguimos.
- **Evitá back-adjusted** para el ATR: distorsiona la tabla de escenarios. Si es lo único que
  tenés, avisá y lo compensamos.

---

## 5 · Formato final que me sirve

Un **CSV por temporalidad** (o sólo M1 y yo hago el resto), con estas columnas y una cabecera:

```
datetime,open,high,low,close,volume
2025-10-22 09:00:00,58.42,58.55,58.38,58.51,1240
2025-10-22 09:05:00,58.51,58.60,58.47,58.49,980
...
```

- **datetime**: fecha y hora juntas, formato `YYYY-MM-DD HH:MM:SS`. Si NT te lo da como
  `yyyyMMdd HHmmss`, no lo toques — yo lo convierto.
- **Zona horaria**: decime cuál es (la de tu NT: `Tools → Options → General → Time zone`).
  No la cambies; sólo necesito saber cuál es.
- **Separador**: da igual `,` o `;`; me avisás cuál.
- **Peso**: si son años de M1, el archivo puede ser grande (decenas de MB). Comprimilo en `.zip`
  y me lo pasás — como hicimos con la captura del giro.

---

## 6 · Checklist antes de mandármelo

- [ ] Instrumento **CL** continuo (no MCL, no otro símbolo).
- [ ] **Minute (M1)** con **volumen real** (verificado que no es 0).
- [ ] Rango: lo más largo posible (mínimo cubrir 22/10/2025 → 26/06/2026 para la validación §10).
- [ ] Sé **qué zona horaria** tiene NT configurada.
- [ ] Idealmente, columna de **contrato** por barra (si no, avisar que es continuo raw).
- [ ] Comprimido en `.zip`.

Con eso corro la **validación obligatoria**: el detector tiene que reproducir tus 97 operaciones
reales antes de que confiemos en cualquier backtest de años. Si reproduce, seguimos al largo.
