# backtest/

Motor de backtesting del sistema CL/MCL. Ver `../04-SPEC.md` (reglas) y
`../06-BACKTEST-v0.md` (resultados y advertencias).

## Archivos

- **`build_data.py`** — empalma los exports de contratos mensuales de CL (NT8, 1 min) en
  una serie continua y la resamplea a M5/M60.
- **`backtest.py`** — detecta el gatillo mecánico de ESTRUC+VC, aplica la tabla ATR y simula
  el resultado en R. Imprime sensibilidad al objetivo y desgloses.

## Datos

Los CSV de precio **no** se versionan (son grandes y se regeneran). Pipeline:

```bash
# 1) juntar los .txt de NinjaTrader (uno por contrato) en un directorio raw/
python build_data.py raw/ data/

# 2) correr el backtest apuntando a ese directorio
CL_DATA_DIR=data python backtest.py
```

Formato de cada `.txt` de NT (timestamps en UTC):
`yyyyMMdd HHmmss;open;high;low;close;volume`

## Zonas horarias

- Datos de precio: **UTC**.
- Ventana operativa: se calcula en **America/New_York** (apertura cash 09:00, DST real).
- Aplanado no-overnight: **21:00 UTC** (18:00 Buenos Aires).
- Registro B20x50 (para validar): **Buenos Aires −3** → sumar 3 h para pasar a UTC.
