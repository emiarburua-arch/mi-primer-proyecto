#!/usr/bin/env python3
"""
Empalma los exports de contratos mensuales de CL (NinjaTrader 8, 1 minuto) en una
serie continua y la resamplea a M5 y M60.

Entrada:  un directorio con los .txt de NT, formato por línea:
              yyyyMMdd HHmmss;open;high;low;close;volume
          (uno por contrato: CL_1225, CL_0126, ...). Timestamps en UTC.
Salida:   CL_M1_continuo.csv, CL_M5_continuo.csv, CL_M60_continuo.csv
          columnas: datetime,open,high,low,close,volume[,contract]

Empalme: para cada día se usa el contrato con MÁS volumen ese día (el "front"),
que es la forma robusta de rollover sin ajustar precios (raw). Ver 04-SPEC.md §1.

Uso:  python build_data.py <dir_raw> <dir_salida>
"""
import sys, os, glob
from datetime import datetime
from collections import defaultdict


def load_txt(path):
    rows = []
    with open(path) as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            p = ln.split(';')
            dt = datetime.strptime(p[0], '%Y%m%d %H%M%S')
            rows.append((dt, float(p[1]), float(p[2]), float(p[3]), float(p[4]), int(p[5])))
    return rows


def resample(rows, minutes):
    buckets = defaultdict(list)
    for dt, o, h, l, c, v in rows:
        key = dt.replace(minute=(dt.minute // minutes) * minutes, second=0, microsecond=0)
        buckets[key].append((dt, o, h, l, c, v))
    out = []
    for key in sorted(buckets):
        g = sorted(buckets[key])
        out.append((key, g[0][1], max(x[2] for x in g), min(x[3] for x in g),
                    g[-1][4], sum(x[5] for x in g)))
    return out


def main(raw_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(raw_dir, '*.txt')))
    if not files:
        sys.exit(f'no se encontraron .txt en {raw_dir}')

    bars = defaultdict(list)               # (día, contrato) -> barras
    dayvol = defaultdict(lambda: defaultdict(int))
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        for rec in load_txt(path):
            d = rec[0].date()
            bars[(d, name)].append(rec)
            dayvol[d][name] += rec[5]

    # elegir front por día y concatenar
    out = []
    front = {}
    for day in sorted(dayvol):
        f = max(dayvol[day], key=lambda k: dayvol[day][k])
        front[day] = f
        out.extend(sorted(bars[(day, f)]))
    out.sort()

    p1 = os.path.join(out_dir, 'CL_M1_continuo.csv')
    with open(p1, 'w') as f:
        f.write('datetime,open,high,low,close,volume,contract\n')
        for dt, o, h, l, c, v in out:
            f.write(f'{dt:%Y-%m-%d %H:%M:%S},{o},{h},{l},{c},{v},{front[dt.date()]}\n')
    print(f'M1: {len(out)} barras -> {p1}')

    for mins, nm in ((5, 'M5'), (60, 'M60')):
        r = resample(out, mins)
        pp = os.path.join(out_dir, f'CL_{nm}_continuo.csv')
        with open(pp, 'w') as f:
            f.write('datetime,open,high,low,close,volume\n')
            for dt, o, h, l, c, v in r:
                f.write(f'{dt:%Y-%m-%d %H:%M:%S},{o},{h},{l},{c},{v}\n')
        print(f'{nm}: {len(r)} barras -> {pp}')

    print('rango:', out[0][0], '->', out[-1][0])


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('uso: python build_data.py <dir_raw> <dir_salida>')
    main(sys.argv[1], sys.argv[2])
