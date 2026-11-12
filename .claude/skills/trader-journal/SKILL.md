---
name: trader-journal
description: >-
  Registro de operaciones del usuario. Usar cuando el usuario cuenta una
  operación que hizo o cerró ("entré corto en JBS a 11.85", "salí de HUBS en
  219", "registra esta operación", "anota el trade", "cómo voy", "mis
  estadísticas", "cuántas gané"), para agregarla, corregirla o resumir
  resultados. Guarda todo en journal/operaciones.csv del repo.
argument-hint: "[add | edit | list | stats]"
---

# trader-journal

El usuario dicta sus operaciones en el chat; Claude las registra con
`journal/journal.py` (en la raíz del repo) y hace commit + push para que el
registro sobreviva al contenedor.

```bash
python3 journal/journal.py add --fecha 2026-11-12 --accion JBS --lado corto \
  --entrada 11.85 --stop 12.01 --objetivo 11.53 --salida 11.53 --acciones 310 \
  --hora-entrada 09:50 --en-juego si --rvol 3.2 --gap 3.5 --tipo-dia venta --cuenta papel \
  --setup "ORB 15m corto"
python3 journal/journal.py edit 1 --salida 11.60 --hora-salida 10:40   # completar o corregir
python3 journal/journal.py list
python3 journal/journal.py stats
```

## Cómo registrar

1. Sacar del mensaje lo que haya: acción, lado, entrada, stop, objetivo,
   salida, acciones, horas, cuenta (papel o real), comisiones.
2. Si la señal salió de un escaneo de esta conversación, completar `rvol`,
   `gap_pct` (a favor de la operación), `en_juego` (si: rvol >= 2 y gap >= 2%)
   y `setup` desde ahí. `tipo_dia`: `venta` si el SPY abrió abajo y estaba
   bajo su VWAP con muchas acciones en gap a la baja, `subida` al revés, si no
   `normal`.
3. Lo que falte y cambie el resultado (salida, acciones, cuenta), preguntarlo
   en UNA pregunta corta; lo demás dejarlo vacío. Una operación sin salida
   queda `abierta` y se completa después con `edit`.
4. Mostrar la fila registrada, y `stats` si hay 5 o más operaciones.
5. `git add journal && git commit && git push` a la rama de trabajo.

## Cómo leer las estadísticas

`stats` da, en total y por lado, en juego, tipo de día y cuenta: n, %
ganadoras, % que tocó objetivo, R medio, R total, ganancia y pérdida media,
la peor racha (drawdown en R) y USD. Decirlo siempre así: con menos de 30
operaciones cerradas es ruido; 100+ para confiar. Comparar con el laboratorio
(research/orb-filtros-2026-11-11.md): el corto en juego dependía de días de
venta generalizada, así que mirar sobre todo `tipo_dia`.

No es consejo financiero; registrar no es recomendar.
