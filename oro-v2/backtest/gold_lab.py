"""Laboratorio de motores para MGC 5m. Cada motor se corre con sesgo forzado LARGO, forzado CORTO
y natural (sin sesgo); después se combina con sesgo mecánico (B), oráculo (C) y sesgos de exactitud p.
Uso: python gold_lab.py <dir_data> <dir_out> E1 E2 E3 ..."""
import sys, os, math
import numpy as np, pandas as pd

DATA, OUT, ENGINES = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(OUT, exist_ok=True)
TICK, PT, COMM, RISK, MAXC = 0.1, 10.0, 1.84, 150.0, 5
rnd = lambda x: round(round(x / TICK) * TICK, 1)

# ---------------- datos (igual que gold_bt) ----------------
m1 = pd.read_pickle(os.path.join(DATA, "m1.pkl"))
c = m1["contract"].values; idx = m1.index; adj = np.zeros(len(m1)); off = 0.0
for k in range(len(m1) - 1, 0, -1):
    if c[k] != c[k - 1] and (idx[k] - idx[k - 1]) < pd.Timedelta(days=4):
        off += m1["open"].iat[k] - m1["close"].iat[k - 1]
    adj[k - 1] = off
for col in ("open", "high", "low", "close"):
    m1[col] = m1[col] + adj
gap_starts = [idx[k] for k in range(1, len(m1)) if idx[k] - idx[k - 1] > pd.Timedelta(days=4)] + [idx[0]]
def rs(df, rule):
    g = df.resample(rule, label="left", closed="left")
    return pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last()}).dropna()
m5 = rs(m1, "5min"); h1 = rs(m1, "60min")
m5["ema20"] = m5.close.ewm(span=20, adjust=False).mean(); m5["ema50"] = m5.close.ewm(span=50, adjust=False).mean()
pc = m5.close.shift()
m5["atr"] = pd.concat([m5.high - m5.low, (m5.high - pc).abs(), (m5.low - pc).abs()], axis=1).max(axis=1).ewm(alpha=1/14, adjust=False).mean()
h1["ema50"] = h1.close.ewm(span=50, adjust=False).mean()
win = m1.between_time("08:45", "12:59"); cnt = win.groupby(win.index.date).size()
days = [d for d, n in cnt.items() if n >= 250 and pd.Timestamp(d).weekday() < 5]
skip = set()
for gs in gap_starts:
    skip.update([d for d in days if pd.Timestamp(d) >= gs.tz_localize(None).normalize()][:2])
days = [d for d in days if d not in skip]
o = win.groupby(win.index.date).open.first(); cl = win.groupby(win.index.date).close.last()
TRUTH = {d: (1 if cl[d] > o[d] else -1) for d in days}
def biasB(d):
    r = h1[h1.index <= pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=7)].iloc[-1]
    return 1 if r.close > r.ema50 else -1
BIAS_B = {d: biasB(d) for d in days}
M5D = {d: g for d, g in m5.groupby(m5.index.date)}
M1D = {d: g for d, g in m1.groupby(m1.index.date)}

def T(d, hm): return pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hm + ":00")

# ---------------- generadores de señales ----------------
# cada señal: dict(dir, ready, P, stop, valid_until, atr, exit, cancel_ema50)
def sig_pullback(d, bias, exit_mode):
    b = m5[(m5.index >= T(d, "05:00")) & (m5.index < T(d, "13:00"))]
    out = []
    for j in range(3, len(b)):
        ts = b.index[j]; ct = ts + pd.Timedelta(minutes=5)
        if ct < T(d, "08:45") or ct > T(d, "11:30"): continue
        r, p1, p2, e3 = b.iloc[j], b.iloc[j - 1], b.iloc[j - 2], b.ema20.iloc[j - 3]; rng = r.high - r.low
        for s in (1, -1):
            if bias not in (None, s): continue
            if s == 1 and not (r.ema20 > r.ema50 and r.ema20 > e3 and r.low <= r.ema20 + .2 * r.atr and r.low <= min(p1.low, p2.low) and r.close > r.ema50 and r.close >= r.low + .5 * rng): continue
            if s == -1 and not (r.ema20 < r.ema50 and r.ema20 < e3 and r.high >= r.ema20 - .2 * r.atr and r.high >= max(p1.high, p2.high) and r.close < r.ema50 and r.close <= r.high - .5 * rng): continue
            P = rnd(r.high + TICK) if s == 1 else rnd(r.low - TICK)
            st = rnd(min(r.low, p1.low) - TICK) if s == 1 else rnd(max(r.high, p1.high) + TICK)
            if abs(P - st) > 1.5 * r.atr: continue
            out.append(dict(dir=s, ready=ct, P=P, stop=st, valid=min(ct + pd.Timedelta(minutes=10), T(d, "11:30")), atr=r.atr, exit=exit_mode, cancel_ema50=True, sigbar=j, bars=b))
    return out

def sig_london(d, bias):
    b = m5[(m5.index >= T(d, "03:00")) & (m5.index < T(d, "13:00"))]
    lon = b[b.index < T(d, "08:30")]
    if len(lon) < 50: return []
    LH, LL = lon.high.max(), lon.low.min()
    ny = b[b.index >= T(d, "08:30")]
    out = []; st = {1: [False, None], -1: [False, None]}   # [barrido?, extremo]
    for ts, r in ny.iterrows():
        ct = ts + pd.Timedelta(minutes=5)
        if ct > T(d, "11:30"): break
        # largo: barre el mínimo de Londres y vuelve a cerrar adentro
        if r.low < LL:
            st[1][0] = True; st[1][1] = r.low if st[1][1] is None else min(st[1][1], r.low)
        if st[1][0] and r.close > LL:
            if bias in (None, 1):
                out.append(dict(dir=1, ready=ct, P=rnd(r.high + TICK), stop=rnd(st[1][1] - TICK), valid=min(ct + pd.Timedelta(minutes=10), T(d, "11:30")), atr=r.atr, exit="2R", cancel_ema50=False))
            st[1] = [False, None]
        if r.high > LH:
            st[-1][0] = True; st[-1][1] = r.high if st[-1][1] is None else max(st[-1][1], r.high)
        if st[-1][0] and r.close < LH:
            if bias in (None, -1):
                out.append(dict(dir=-1, ready=ct, P=rnd(r.low - TICK), stop=rnd(st[-1][1] + TICK), valid=min(ct + pd.Timedelta(minutes=10), T(d, "11:30")), atr=r.atr, exit="2R", cancel_ema50=False))
            st[-1] = [False, None]
    return out

def sig_ib(d, bias):
    b = m5[(m5.index >= T(d, "08:30")) & (m5.index < T(d, "13:00"))]
    ib = b[b.index < T(d, "09:30")]
    if len(ib) < 12: return []
    IH, IL = ib.high.max(), ib.low.min(); mid = (IH + IL) / 2
    out = []; prev_in = {1: True, -1: True}
    for ts, r in b[b.index >= T(d, "09:30")].iterrows():
        ct = ts + pd.Timedelta(minutes=5)
        if ct > T(d, "11:30"): break
        for s, lvl in ((1, IH), (-1, IL)):
            outside = r.close > lvl if s == 1 else r.close < lvl
            if outside and prev_in[s] and bias in (None, s):
                P = rnd(r.high + TICK) if s == 1 else rnd(r.low - TICK)
                out.append(dict(dir=s, ready=ct, P=P, stop=rnd(mid), valid=min(ct + pd.Timedelta(minutes=10), T(d, "11:30")), atr=r.atr, exit="2R", cancel_ema50=False))
            prev_in[s] = not outside
    return out

GEN = {"E0": lambda d, b: sig_pullback(d, b, "2R"),      # plan v2 (referencia)
       "E1": sig_london, "E2": sig_ib,
       "E3": lambda d, b: sig_pullback(d, b, "trail")}

# ---------------- ejecución minuto a minuto ----------------
def simulate_day(d, sigs):
    trades = []; free = T(d, "08:00"); ntr = nloss = 0
    mm = M1D[d]; mm = mm[(mm.index >= T(d, "08:30")) & (mm.index < T(d, "13:00"))]
    tm = mm.index; O, H, L, C = mm.open.values, mm.high.values, mm.low.values, mm.close.values
    e5 = M5D[d]
    for s in sorted(sigs, key=lambda x: x["ready"]):
        if ntr >= 2 or nloss >= 2: break
        if s["ready"] <= free: continue
        sg, P, stop = s["dir"], s["P"], s["stop"]
        dist = rnd((P - stop) * sg)
        if dist < 0.5 * s["atr"]:
            dist = rnd(0.5 * s["atr"]); stop = rnd(P - sg * dist)
        if dist <= 0 or dist > 15.0: continue
        nc = min(MAXC, math.floor(RISK / (dist * PT) + 1e-9))
        tp = rnd(P + sg * 2 * dist) if s["exit"] == "2R" else None
        i0 = np.searchsorted(tm, s["ready"]); fill = None
        for i in range(i0, len(tm)):
            if tm[i] >= s["valid"]: break
            if s["cancel_ema50"] and tm[i] >= s["ready"] + pd.Timedelta(minutes=5):
                nb = e5[e5.index == s["ready"]]
                if len(nb) and ((sg == 1 and nb.close.iat[0] < nb.ema50.iat[0]) or (sg == -1 and nb.close.iat[0] > nb.ema50.iat[0])): break
            if sg == 1 and H[i] >= P: fill = max(O[i], P) + TICK
            if sg == -1 and L[i] <= P: fill = min(O[i], P) - TICK
            if fill is not None: fi = i; break
        if fill is None: continue
        exitp = how = None
        for i in range(fi, len(tm)):
            if sg == 1:
                if i > fi and O[i] <= stop: exitp, how = O[i] - TICK, "stop"
                elif L[i] <= stop: exitp, how = stop - TICK, "stop"
                elif tp is not None and H[i] >= tp + TICK: exitp, how = tp, "tp"
            else:
                if i > fi and O[i] >= stop: exitp, how = O[i] + TICK, "stop"
                elif H[i] >= stop: exitp, how = stop + TICK, "stop"
                elif tp is not None and L[i] <= tp - TICK: exitp, how = tp, "tp"
            if exitp is None and s["exit"] == "trail" and (tm[i].minute % 5 == 4):
                bs = tm[i] - pd.Timedelta(minutes=4)
                if bs in e5.index:
                    rb = e5.loc[bs]
                    if (sg == 1 and rb.close < rb.ema20) or (sg == -1 and rb.close > rb.ema20):
                        exitp, how = C[i] - sg * TICK, "trail"
            if exitp is not None: xi = i; break
        if exitp is None: xi = len(tm) - 1; exitp, how = C[xi] - sg * TICK, "tiempo"
        pnl = (exitp - fill) * sg * PT * nc - COMM * nc
        trades.append(dict(day=str(d), dir=sg, ready=s["ready"], entry=round(fill, 1), stop=stop, dist=dist, nc=nc, exit=round(exitp, 1), how=how, pnl=round(pnl, 2), R=round(pnl / (dist * PT * nc), 3)))
        ntr += 1; free = tm[xi]
        if pnl > 0: break
        nloss += 1
    return trades

def combine(per_dir, choice):
    out = []; wk = {}
    for d in days:
        k = pd.Timestamp(d).isocalendar()[:2]
        if wk.get(k, 0) <= -4: continue
        for t in per_dir[choice[d]].get(str(d), []):
            if wk.get(k, 0) <= -4: break
            out.append(t); wk[k] = wk.get(k, 0) + t["R"]
    return pd.DataFrame(out)

def summ(t):
    if t.empty: return dict(n=0)
    w = t[t.pnl > 0]; l = t[t.pnl <= 0]; eq = t.R.cumsum()
    half = [str(d) for d in days if pd.Timestamp(d) < pd.Timestamp("2026-07-01")]
    return dict(n=len(t), win=round(len(w) / len(t) * 100, 1), PF=round(w.pnl.sum() / -l.pnl.sum(), 2), expR=round(t.R.mean(), 3),
                neto=round(t.pnl.sum()), DD_R=round((eq - eq.cummax().clip(lower=0)).min(), 1),
                H1_R=round(t[t.day.isin(half)].R.sum(), 1), H2_R=round(t[~t.day.isin(half)].R.sum(), 1))

rng = np.random.default_rng(11)
report = []
for E in ENGINES:
    per = {}
    for key, bias in (("L", 1), ("S", -1), ("N", None)):
        dd = {}
        for d in days:
            tr = simulate_day(d, GEN[E](d, bias))
            if tr: dd[str(d)] = tr
        per[key] = dd
    per_dir = {1: per["L"], -1: per["S"]}
    A = combine({0: per["N"]}, {d: 0 for d in days})
    B = combine(per_dir, BIAS_B); C = combine(per_dir, TRUTH)
    for nm, t in (("A", A), ("B", B), ("C", C)):
        s = summ(t); s.update(motor=E, sesgo=nm); report.append(s); print(E, nm, s, flush=True)
        t.to_csv(os.path.join(OUT, f"lab_{E}_{nm}.csv"), index=False)
    curve = {}
    for p in (0.55, 0.60, 0.65, 0.70, 0.80):
        ex = []
        for _ in range(400):
            ch = {d: (TRUTH[d] if rng.random() < p else -TRUTH[d]) for d in days}
            t = combine(per_dir, ch); ex.append(t.R.mean() if len(t) else 0)
        curve[p] = (round(float(np.mean(ex)), 3), round(float(np.mean(np.array(ex) > 0)), 2))
    print(E, "curva de exactitud (esperanza, P>0):", curve, flush=True)
    report[-1]["curva"] = curve
pd.DataFrame(report).to_csv(os.path.join(OUT, "lab_resumen.csv"), index=False)
