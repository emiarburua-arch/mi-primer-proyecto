#!/usr/bin/env python3
"""
Primer Empuje (M2 v2.2) — opening range breakout sobre barras de 1 minuto.

Reglas congeladas (D1–D6):
  D1 Rango de apertura = máx/mín de los primeros 5 min de la sesión RTH del activo.
  D2 Ruptura = una vela de 1 min CIERRA fuera del rango (no basta la mecha).
  D3 Solo la PRIMERA ruptura de la sesión cuenta.
  D4 Dirección = la de la primera ruptura.
  D5 R = altura del rango (máx − mín).
  D6 Entrada = cierre de la vela que confirma; Stop = extremo opuesto; Objetivo = 1R desde la entrada.

Extensiones medidas (no son parte de las reglas congeladas; se prueban aparte):
  - `target_R`: dejar correr el objetivo (2R rindió mejor en CL).
  - `time_exit`: salir a mercado si no resolvió en N minutos ("funciona rápido o se desploma").
  - `side='against'`: fadear la ruptura (para activos que revierten, p.ej. ES).

Hallazgos (CL, dic-2023 → jul-2026, simulador fiel, ANTES de costos):
  - CL es activo de RUPTURA: breakout 2R + salida 60min = +0,065 R/trade, PF 1,13, positivo
    todos los años. Fadear el CL pierde. La apertura de EE.UU. (09:00) supera a la de Europa.

RTH open por activo (hora ET): CL 09:00 (pit de crudo); índices (NQ/ES) 09:30.

Uso:  CL_DATA_DIR=/ruta python primer_empuje.py    # lee CL_M1_continuo.csv
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

UTC = ZoneInfo('UTC')
NY = ZoneInfo('America/New_York')
DATA_DIR = os.environ.get('CL_DATA_DIR', 'data')


def load_m1(fn='CL_M1_continuo.csv'):
    rows = []
    with open(os.path.join(DATA_DIR, fn)) as f:
        next(f)
        for ln in f:
            p = ln.split(',')
            rows.append([datetime.strptime(p[0], '%Y-%m-%d %H:%M:%S'),
                         float(p[1]), float(p[2]), float(p[3]), float(p[4])])
    return rows


def backtest(m1, open_et_hour=9, open_et_min=0, target_R=2.0, time_exit_min=None,
             side='with', search_hours=5, flat_utc_hour=20):
    """side: 'with' = a favor de la ruptura; 'against' = fade (opuesto)."""
    by = defaultdict(list)
    for b in m1:
        by[b[0].date()].append(b)
    et = lambda dt: dt.replace(tzinfo=UTC).astimezone(NY)
    trades = []
    for day in sorted(by):
        bars = sorted(by[day])
        rng = [b for b in bars if et(b[0]).hour == open_et_hour
               and open_et_min <= et(b[0]).minute < open_et_min + 5]
        if len(rng) < 3:
            continue
        hi = max(b[2] for b in rng)
        lo = min(b[3] for b in rng)
        R = hi - lo
        if R <= 0:
            continue
        t0 = rng[-1][0]
        after = [b for b in bars if t0 < b[0] <= t0 + timedelta(hours=search_hours)]
        bdir = None
        for k, b in enumerate(after):
            if b[4] > hi:
                bdir, ep, k0, et0 = 'up', b[4], k, b[0]; break
            if b[4] < lo:
                bdir, ep, k0, et0 = 'down', b[4], k, b[0]; break
        if bdir is None:
            continue
        if side == 'with':
            is_long = bdir == 'up'
            stop = lo if is_long else hi
            tgt = ep + target_R * R if is_long else ep - target_R * R
        else:  # fade
            is_long = bdir == 'down'
            if bdir == 'up':
                stop, tgt = ep + R, lo
            else:
                stop, tgt = ep - R, hi
        risk = abs(ep - stop)
        out = None
        for b in after[k0 + 1:]:
            if b[0].hour >= flat_utc_hour:
                out = (b[4] - ep) if is_long else (ep - b[4]); break
            if time_exit_min and (b[0] - et0) >= timedelta(minutes=time_exit_min):
                out = (b[4] - ep) if is_long else (ep - b[4]); break
            hitS = b[3] <= stop if is_long else b[2] >= stop
            hitT = b[2] >= tgt if is_long else b[3] <= tgt
            if hitS:
                out = -risk; break
            if hitT:
                out = abs(tgt - ep); break
        if out is None:
            out = 0.0
        trades.append({'day': day, 'pts': out, 'R': out / risk if risk > 0 else 0, 'win': out > 0})
    return trades


def report(name, trades):
    if not trades:
        print(f'{name}: sin trades'); return
    n = len(trades)
    wr = 100 * sum(1 for t in trades if t['win']) / n
    exp = sum(t['R'] for t in trades) / n
    w = sum(t['R'] for t in trades if t['R'] > 0)
    l = -sum(t['R'] for t in trades if t['R'] < 0)
    by = defaultdict(list)
    for t in trades:
        by[t['day'].year].append(t)
    yr = '  '.join(f'{y}:{sum(x["R"] for x in v)/len(v):+.2f}' for y, v in sorted(by.items()))
    print(f'{name}: n={n}  WR {wr:.0f}%  exp {exp:+.3f}R  PF {(w/l if l else 9):.2f} | {yr}')


if __name__ == '__main__':
    m1 = load_m1()
    print(f'CL M1: {len(m1)} barras\n')
    report('CL breakout 2R + salida 60min', backtest(m1, 9, 0, 2.0, 60, 'with'))
    report('CL breakout 1R                ', backtest(m1, 9, 0, 1.0, None, 'with'))
    report('CL fade                       ', backtest(m1, 9, 0, 1.0, None, 'against'))
