#!/usr/bin/env python3
"""
Backtest v0 del sistema CL/MCL (ver 04-SPEC.md y TPP-v2.md).

Detecta el GATILLO MECÁNICO de ESTRUC+VC — retroceso → vela de confirmación →
ruptura de su extremo — dentro de la ventana operativa, aplica la tabla ATR para
stop/objetivo del escenario, y simula el resultado en múltiplos de R.

Lo que ESTE código NO decide (es discrecional, se mide como filtro, no se fuerza):
  - la lectura de estructura HH+HL,
  - la hipótesis A/B de contexto M60.
Por eso el detector "sobre-dispara" respecto de las entradas selectivas reales;
su valor es medir el EDGE MECÁNICO crudo sobre una muestra larga y sin sesgo.

Zonas horarias: datos de precio en UTC; ventana operativa calculada en
America/New_York (apertura cash 09:00) con DST real; aplanado 21:00 UTC (18:00 BA).

Uso:  CL_DATA_DIR=/ruta/a/csvs python backtest.py
      (por defecto lee ./data relativo al cwd)
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

UTC = ZoneInfo('UTC')
NY = ZoneInfo('America/New_York')
DATA_DIR = os.environ.get('CL_DATA_DIR', 'data')

# --- parámetros congelados (04-SPEC.md §9) ---
WINDOW_OPEN_MIN = 30      # entradas desde apertura_cash + 30
WINDOW_CLOSE_MIN = 150    # hasta apertura_cash + 150
FLAT_UTC_HOUR = 21        # aplanado no-overnight (18:00 BA)
MAX_TRADES_DAY = 2
TICK = 0.01

# tabla ATR: escala plataforma (ATR$ * 1000) -> (etiqueta, stop_ticks, contratos)
def scenario(atr_dollars):
    if atr_dollars is None:
        return None
    u = atr_dollars * 1000
    if u < 500:  return ('A', 15, 1)
    if u < 1000: return ('B', 30, 5)
    if u < 1250: return ('C', 50, 3)
    if u < 1500: return ('D', 75, 2)
    return None  # atr >= 1500: no se opera


def load(fn):
    rows = []
    with open(os.path.join(DATA_DIR, fn)) as f:
        next(f)
        for ln in f:
            p = ln.strip().split(',')
            rows.append([datetime.strptime(p[0], '%Y-%m-%d %H:%M:%S'),
                         float(p[1]), float(p[2]), float(p[3]), float(p[4]), int(p[5])])
    return rows


def atr14(m60):
    a = [None] * len(m60)
    for i in range(1, len(m60)):
        trs = []
        for j in range(max(1, i - 13), i + 1):
            h, l, pc = m60[j][2], m60[j][3], m60[j - 1][4]
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))
        if len(trs) >= 14:
            a[i] = sum(trs[-14:]) / 14
    return a


def color(b):
    return 'V' if b[4] > b[1] else ('R' if b[4] < b[1] else '-')


def in_window(dt):
    ny = dt.replace(tzinfo=UTC).astimezone(NY)
    op = ny.replace(hour=9, minute=0, second=0, microsecond=0)
    return op + timedelta(minutes=WINDOW_OPEN_MIN) <= ny <= op + timedelta(minutes=WINDOW_CLOSE_MIN)


def swings(seg, k=2):
    sh, sl = [], []
    for j in range(k, len(seg) - k):
        if all(seg[j][2] >= seg[j - m][2] and seg[j][2] >= seg[j + m][2] for m in range(1, k + 1)):
            sh.append((j, seg[j][2]))
        if all(seg[j][3] <= seg[j - m][3] and seg[j][3] <= seg[j + m][3] for m in range(1, k + 1)):
            sl.append((j, seg[j][3]))
    return sh, sl


def has_structure(m5, t, is_long, look=24):
    """Proxy mecánico de estructura HH (higher-highs) / LL. Discrecional en la práctica."""
    if t < look:
        return False
    sh, sl = swings(m5[t - look:t + 1])
    if is_long:
        return len(sh) >= 2 and sh[-1][1] > sh[-2][1]
    return len(sl) >= 2 and sl[-1][1] < sl[-2][1]


def atr_before(m60, atr, dt):
    best = None
    for i in range(len(m60)):
        if m60[i][0] <= dt and atr[i] is not None:
            best = atr[i]
        elif m60[i][0] > dt:
            break
    return best


def backtest(m5, m60, atr, target_R=2.0, use_structure=False):
    trades = []
    i, n = 6, len(m5)
    last_day, day_count = None, 0
    while i < n - 3:
        b = m5[i]
        if not in_window(b[0]):
            i += 1
            continue
        day = b[0].date()
        if day != last_day:
            last_day, day_count = day, 0
        if day_count >= MAX_TRADES_DAY:
            i += 1
            continue
        fired = False
        for is_long in (True, False):
            for t in range(i - 1, i - 4, -1):
                trig = m5[t]
                if (color(trig) != 'V') if is_long else (color(trig) != 'R'):
                    continue
                # retroceso: >=1 vela contraria inmediatamente antes del disparador
                if not any(((color(m5[t - m]) == 'R') if is_long else (color(m5[t - m]) == 'V'))
                           for m in range(1, 4)):
                    continue
                brk = trig[2] if is_long else trig[3]
                if (b[2] > brk) if is_long else (b[3] < brk):
                    if use_structure and not has_structure(m5, t, is_long):
                        continue
                    sc = scenario(atr_before(m60, atr, b[0]))
                    if sc is None:
                        continue
                    lab, stk, ctr = sc
                    entry = brk + (TICK if is_long else -TICK)
                    dist = stk * TICK
                    stop = entry - dist if is_long else entry + dist
                    tgt = entry + target_R * dist if is_long else entry - target_R * dist
                    out, ei = None, i
                    for k in range(i, n):
                        bb = m5[k]
                        if bb[0].hour >= FLAT_UTC_HOUR and bb[0].date() == day:
                            px = bb[4]
                            out = ((px - entry) / dist) if is_long else ((entry - px) / dist)
                            ei = k
                            break
                        hitS = bb[3] <= stop if is_long else bb[2] >= stop
                        hitT = bb[2] >= tgt if is_long else bb[3] <= tgt
                        if hitS:   # pesimista: si toca stop y target en la misma barra, cuenta stop
                            out, ei = -1.0, k
                            break
                        if hitT:
                            out, ei = target_R, k
                            break
                    if out is None:
                        out = 0.0
                    trades.append({'day': day, 'dir': 'L' if is_long else 'C',
                                   'esc': lab, 'R': round(out, 3)})
                    day_count += 1
                    fired = True
                    i = ei + 1
                    break
            if fired:
                break
        if not fired:
            i += 1
    return trades


def stats(trades):
    R = [t['R'] for t in trades]
    if not R:
        return {}
    wins = [r for r in R if r > 0]
    losses = [r for r in R if r < 0]
    return {
        'n': len(R),
        'winrate': 100 * len(wins) / len(R),
        'R_medio': sum(R) / len(R),
        'PF': (sum(wins) / -sum(losses)) if losses else float('inf'),
        'R_total': sum(R),
    }


def main():
    m5 = load('CL_M5_continuo.csv')
    m60 = load('CL_M60_continuo.csv')
    atr = atr14(m60)
    print(f'datos: {len(m5)} M5, {len(m60)} M60  ({m5[0][0].date()} -> {m5[-1][0].date()})\n')

    print('Sensibilidad al múltiplo de objetivo (gatillo mecánico, stop del escenario):')
    for rr in (1.0, 1.5, 2.0, 2.5, 3.0):
        s = stats(backtest(m5, m60, atr, target_R=rr))
        print(f'  {rr}R: n={s["n"]}  WR {s["winrate"]:.0f}%  '
              f'R/trade {s["R_medio"]:+.3f}  PF {s["PF"]:.2f}  Rtot {s["R_total"]:+.0f}')

    print('\nDesglose a 2R por dirección y escenario:')
    tr = backtest(m5, m60, atr, target_R=2.0)
    for field in ('dir', 'esc'):
        groups = defaultdict(list)
        for t in tr:
            groups[t[field]].append(t)
        for k in sorted(groups):
            s = stats(groups[k])
            print(f'  {field}={k}: n={s["n"]}  WR {s["winrate"]:.0f}%  R/trade {s["R_medio"]:+.3f}')


if __name__ == '__main__':
    main()
