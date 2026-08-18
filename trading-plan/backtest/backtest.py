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
import bisect
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

UTC = ZoneInfo('UTC')
NY = ZoneInfo('America/New_York')
DATA_DIR = os.environ.get('CL_DATA_DIR', 'data')

# --- parámetros congelados (04-SPEC.md §9) ---
WINDOW_OPEN_MIN = 30      # entradas desde apertura_cash + 30
WINDOW_CLOSE_MIN = 150    # hasta apertura_cash + 150
FLAT_UTC_HOUR = 20        # aplanado no-overnight 17:00 BA (límite operativo del operador)
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


def ema(vals, n):
    k = 2 / (n + 1)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out


_m60_times = {}


def m60_completed_idx(m60, dt):
    """Índice de la última barra M60 CERRADA antes de dt (sin mirar al futuro).
    Los timestamps de M60 son hora de apertura; la barra cierra 60 min después.
    Usa búsqueda binaria sobre las marcas de tiempo (cacheadas) para escalar."""
    times = _m60_times.get(id(m60))
    if times is None:
        times = [b[0] for b in m60]
        _m60_times[id(m60)] = times
    pos = bisect.bisect_right(times, dt - timedelta(minutes=60)) - 1
    return pos if pos >= 0 else None


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
    """ATR de la última barra M60 cerrada antes de dt (preparación de sesión, §4)."""
    j = m60_completed_idx(m60, dt)
    while j is not None and atr[j] is None:
        j -= 1
        if j < 0:
            return None
    return atr[j] if j is not None else None


def m60_trend_ok(m60, ema20, ema50, dt, is_long, mode):
    """Filtro de contexto M60: ¿está la tendencia a favor de la dirección?
    Mide el sesgo direccional (la 'hipótesis A/B' vuelta mecánica). Modos:
      'ema50'  : precio del lado correcto de la EMA50
      'slope6' : pendiente del M60 (close vs 6 barras atrás) a favor
      'combo'  : EMA20 alineada Y pendiente6 a favor (el más robusto en v0)
    """
    j = m60_completed_idx(m60, dt)
    if j is None or j < 50:
        return False
    close = m60[j][4]
    if mode == 'ema50':
        return (close > ema50[j]) if is_long else (close < ema50[j])
    if mode == 'slope6':
        s = close - m60[j - 6][4]
        return (s > 0) if is_long else (s < 0)
    if mode == 'combo':
        s = close - m60[j - 6][4]
        if is_long:
            return close > ema20[j] and s > 0
        return close < ema20[j] and s < 0
    return True


def backtest(m5, m60, atr, target_R=2.0, use_structure=False,
             m60_mode=None, ema20=None, ema50=None, trigger='VC'):
    """`trigger`:
      'VC' = vela a favor cerrada (verde en alcista) tras un retroceso contrario.
      'FV' = vela CONTRARIA al impulso (roja en alcista) con volumen < las 2 previas
             ('falta de volumen' en el retroceso), precedida de impulso a favor."""
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
                if trigger == 'VC':
                    if (color(trig) != 'V') if is_long else (color(trig) != 'R'):
                        continue
                    # retroceso: >=1 vela contraria inmediatamente antes del disparador
                    if not any(((color(m5[t - m]) == 'R') if is_long else (color(m5[t - m]) == 'V'))
                               for m in range(1, 4)):
                        continue
                else:  # FV: la vela disparador es el retroceso contrario con poco volumen
                    if (color(trig) != 'R') if is_long else (color(trig) != 'V'):
                        continue
                    if not (trig[5] < m5[t - 1][5] and trig[5] < m5[t - 2][5]):
                        continue
                    # impulso a favor antes del retroceso
                    if not any(((color(m5[t - m]) == 'V') if is_long else (color(m5[t - m]) == 'R'))
                               for m in range(1, 4)):
                        continue
                brk = trig[2] if is_long else trig[3]
                if (b[2] > brk) if is_long else (b[3] < brk):
                    if use_structure and not has_structure(m5, t, is_long):
                        continue
                    if m60_mode and not m60_trend_ok(m60, ema20, ema50, b[0], is_long, m60_mode):
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


def session_levels(m5):
    """máx/mín por día de cada sesión (hora BA → UTC):
      asia   15:30–04:00 BA = 18:30–07:00 UTC (cruza medianoche → cuenta al día siguiente)
      europa 04:00–10:00 BA = 07:00–13:00 UTC
      nyor   10:00–11:00 BA = 13:00–14:00 UTC (rango de apertura: 1ª hora de NY)
    Devuelve {'asia':{d:(lo,hi)}, 'europa':{...}, 'nyor':{...}}."""
    asia, eu, nyor = {}, {}, {}

    def upd(store, d, b):
        lo, hi = store.get(d, (None, None))
        store[d] = (b[3] if lo is None else min(lo, b[3]),
                    b[2] if hi is None else max(hi, b[2]))

    for b in m5:
        t = b[0]
        h = t.hour + t.minute / 60
        if h < 7:
            upd(asia, t.date(), b)
        elif h >= 18.5:
            upd(asia, t.date() + timedelta(days=1), b)
        if 7 <= h < 13:
            upd(eu, t.date(), b)
        if 13 <= h < 14:
            upd(nyor, t.date(), b)
    return {'asia': asia, 'europa': eu, 'nyor': nyor}


def europe_levels(m5):
    """Compatibilidad: solo los niveles de Europa."""
    return session_levels(m5)['europa']


def giro_window(dt):
    """Ventana del giro: 08:00–11:30 ET. Más temprana que la de ESTRUC porque el
    barrido de Europa ocurre en torno a la apertura de NY (visto en las operaciones reales)."""
    ny = dt.replace(tzinfo=UTC).astimezone(NY)
    op = ny.replace(hour=9, minute=0, second=0, microsecond=0)
    return op - timedelta(minutes=60) <= ny <= op + timedelta(minutes=WINDOW_CLOSE_MIN)


def _giro_signal(m5, m60, atr, i, level, is_long, target_R, reject):
    """Intenta un GIRO+VC sobre `level` en la barra i, dirección dada. Devuelve
    (R, exit_i, escenario) si hay entrada válida; si no, None. Sin efectos secundarios.
    Mecánica (alcista sobre el mínimo; corto espejo): manipulación (perfora el nivel) →
    confirmación (1ª vela a favor) → entrada al romper su extremo, stop del escenario debajo
    del pivote (mín. de la manipulación)."""
    n = len(m5)
    b = m5[i]
    manip = None
    for j in range(max(i - 12, 20), i):
        perf = (m5[j][3] < level - TICK) if is_long else (m5[j][2] > level + TICK)
        if perf and (manip is None or ((m5[j][3] < m5[manip][3]) if is_long
                                       else (m5[j][2] > m5[manip][2]))):
            manip = j
    if manip is None:
        return None
    trig = None
    for j in range(manip, i):
        if (color(m5[j]) == 'V') if is_long else (color(m5[j]) == 'R'):
            trig = j
            break
    if trig is None:
        return None
    if reject:
        mb = m5[manip]
        rng = mb[2] - mb[3]
        wick = ((min(mb[1], mb[4]) - mb[3]) / rng if is_long
                else (mb[2] - max(mb[1], mb[4])) / rng) if rng > 0 else 0
        med = sorted(x[5] for x in m5[max(manip - 20, 0):manip])
        medv = med[len(med) // 2] if med else 0
        if not (wick >= 0.60 or (medv > 0 and mb[5] >= 3 * medv)):
            return None
    brk = m5[trig][2] if is_long else m5[trig][3]
    if not ((b[2] > brk) if is_long else (b[3] < brk)):
        return None
    sc = scenario(atr_before(m60, atr, b[0]))
    if sc is None:
        return None
    lab, stk, ctr = sc
    entry = brk + (TICK if is_long else -TICK)
    dist = stk * TICK
    manip_px = m5[manip][3] if is_long else m5[manip][2]
    # el pivote (manipulación) debe caer dentro del stop del escenario (§1.3)
    if (entry - manip_px if is_long else manip_px - entry) > dist + 2 * TICK:
        return None
    stop = entry - dist if is_long else entry + dist
    tgt = entry + target_R * dist if is_long else entry - target_R * dist
    day = b[0].date()
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
        if hitS:
            out, ei = -1.0, k
            break
        if hitT:
            out, ei = target_R, k
            break
    if out is None:
        out = 0.0
    return round(out, 3), ei, lab


def backtest_giro(m5, m60, atr, target_R=2.0, reject=False, levels=None, min_utc_hour=None):
    """GIRO+VC sobre UN nivel de sesión (§6.2.1). `levels`: dict día→(lo,hi); por defecto Europa.
    `min_utc_hour`: no abre giros antes de esa hora UTC (para niveles que aún se forman, p.ej.
    el rango de apertura de NY que cierra a las 14:00). Para el bot ver `backtest_giro_multi`."""
    if levels is None:
        levels = europe_levels(m5)
    trades = []
    i, n = 30, len(m5)
    last_day, day_count = None, 0
    while i < n - 3:
        b = m5[i]
        if not giro_window(b[0]) or (min_utc_hour is not None and b[0].hour < min_utc_hour):
            i += 1
            continue
        day = b[0].date()
        if day != last_day:
            last_day, day_count = day, 0
        if day_count >= MAX_TRADES_DAY or day not in levels or levels[day][0] is None:
            i += 1
            continue
        lo, hi = levels[day]
        fired = False
        for is_long in (True, False):
            res = _giro_signal(m5, m60, atr, i, lo if is_long else hi, is_long, target_R, reject)
            if res:
                R, ei, lab = res
                trades.append({'day': day, 'dir': 'L' if is_long else 'C', 'esc': lab, 'R': R})
                day_count += 1
                fired = True
                i = ei + 1
                break
        if not fired:
            i += 1
    return trades


def giro_sources(m5):
    """Las fuentes de nivel del auto-giro: los tres niveles de sesión del mismo día.
    Cada fuente es (nombre, dict_niveles, min_utc_hour). Pivotes dinámicos quedan afuera
    (sin edge; ver 07-GIRO-validacion.md)."""
    lv = session_levels(m5)
    return [('asia', lv['asia'], None),
            ('europa', lv['europa'], None),
            ('nyor', lv['nyor'], 14)]   # el rango de apertura cierra 14:00 UTC


def backtest_giro_multi(m5, m60, atr, target_R=2.0, sources=None):
    """AUTO-GIRO del bot: dispara sobre CUALQUIERA de los niveles de sesión (Asia/Europa/NY),
    tope de 2/día, una operación por vez. En cada barra prueba las fuentes en orden y toma el
    primer giro válido."""
    if sources is None:
        sources = giro_sources(m5)
    trades = []
    i, n = 30, len(m5)
    last_day, day_count = None, 0
    while i < n - 3:
        b = m5[i]
        if not giro_window(b[0]):
            i += 1
            continue
        day = b[0].date()
        if day != last_day:
            last_day, day_count = day, 0
        if day_count >= MAX_TRADES_DAY:
            i += 1
            continue
        fired = False
        for name, levels, mh in sources:
            if mh is not None and b[0].hour < mh:
                continue
            if day not in levels or levels[day][0] is None:
                continue
            lo, hi = levels[day]
            for is_long in (True, False):
                res = _giro_signal(m5, m60, atr, i, lo if is_long else hi, is_long, target_R, False)
                if res:
                    R, ei, lab = res
                    trades.append({'day': day, 'dir': 'L' if is_long else 'C',
                                   'esc': lab, 'src': name, 'R': R})
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

    print('\nFiltro de contexto M60 (a 2R) — sesgo direccional = hipótesis A/B mecánica:')
    e20 = ema([b[4] for b in m60], 20)
    e50 = ema([b[4] for b in m60], 50)
    base = backtest(m5, m60, atr, target_R=2.0)
    mid = base[len(base) // 2]['day']
    for mode in (None, 'ema50', 'slope6', 'combo'):
        tr = backtest(m5, m60, atr, target_R=2.0, m60_mode=mode, ema20=e20, ema50=e50)
        s = stats(tr)
        h1 = stats([t for t in tr if t['day'] < mid])
        h2 = stats([t for t in tr if t['day'] >= mid])
        name = mode or 'sin filtro'
        print(f'  {name:9}: n={s["n"]:3d}  WR {s["winrate"]:.0f}%  R/trade {s["R_medio"]:+.3f}  '
              f'PF {s["PF"]:.2f}  | mitades {h1.get("R_medio",0):+.3f} / {h2.get("R_medio",0):+.3f}')

    print('\nGIRO+VC sobre nivel de Europa (a 2R) — solo giros de Europa, no pivotes:')
    gbase = backtest_giro(m5, m60, atr, target_R=2.0)
    gmid = gbase[len(gbase) // 2]['day']
    for rj in (False, True):
        tr = backtest_giro(m5, m60, atr, target_R=2.0, reject=rj)
        s = stats(tr)
        h1 = stats([t for t in tr if t['day'] < gmid])
        h2 = stats([t for t in tr if t['day'] >= gmid])
        name = 'con rechazo' if rj else 'sin rechazo'
        print(f'  {name:11}: n={s["n"]:3d}  WR {s["winrate"]:.0f}%  R/trade {s["R_medio"]:+.3f}  '
              f'PF {s["PF"]:.2f}  | mitades {h1.get("R_medio",0):+.3f} / {h2.get("R_medio",0):+.3f}')

    print('\nGIRO por nivel de sesión (2R, por año):')
    lv = session_levels(m5)
    for name, key, mh in [('Europa', 'europa', None), ('Asia', 'asia', None),
                          ('Apertura NY', 'nyor', 14)]:
        tr = backtest_giro(m5, m60, atr, target_R=2.0, levels=lv[key], min_utc_hour=mh)
        s = stats(tr)
        by = defaultdict(list)
        for t in tr:
            by[t['day'].year].append(t)
        yr = '  '.join(f'{y}:{stats(v)["R_medio"]:+.2f}' for y, v in sorted(by.items()))
        print(f'  {name:12}: n={s["n"]:3d}  R/trade {s["R_medio"]:+.3f}  PF {s["PF"]:.2f}  | {yr}')

    print('\nAUTO-GIRO del bot (Asia+Europa+NY combinados, 2R, por año):')
    tr = backtest_giro_multi(m5, m60, atr, target_R=2.0)
    s = stats(tr)
    by = defaultdict(list)
    for t in tr:
        by[t['day'].year].append(t)
    yr = '  '.join(f'{y}:{stats(v)["R_medio"]:+.2f}' for y, v in sorted(by.items()))
    src = defaultdict(list)
    for t in tr:
        src[t['src']].append(t)
    print(f'  combinado : n={s["n"]:3d}  WR {s["winrate"]:.0f}%  R/trade {s["R_medio"]:+.3f}  '
          f'PF {s["PF"]:.2f}  Rtot {s["R_total"]:+.0f}  | {yr}')
    for k in sorted(src):
        ss = stats(src[k])
        print(f'    por fuente {k:7}: n={ss["n"]:3d}  R/trade {ss["R_medio"]:+.3f}  PF {ss["PF"]:.2f}')

    print('\nComparación de setups (2R, por año):')
    setups = [('ESTRUC+VC', backtest(m5, m60, atr, target_R=2.0, trigger='VC')),
              ('ESTRUC+FV', backtest(m5, m60, atr, target_R=2.0, trigger='FV')),
              ('GIRO+VC Eu', backtest_giro(m5, m60, atr, target_R=2.0))]
    for name, tr in setups:
        s = stats(tr)
        by = defaultdict(list)
        for t in tr:
            by[t['day'].year].append(t)
        yr = '  '.join(f'{y}:{stats(v)["R_medio"]:+.2f}' for y, v in sorted(by.items()))
        print(f'  {name:10}: n={s["n"]:3d}  R/trade {s["R_medio"]:+.3f}  PF {s["PF"]:.2f}  | {yr}')


if __name__ == '__main__':
    main()
