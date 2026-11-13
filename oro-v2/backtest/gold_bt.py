"""Backtest del Trading Plan v2 (MGC 5m, pullback a EMA20 con sesgo).
Señales en 5m; ejecución minuto a minuto sobre las velas de 1m.
Uso: python gold_bt.py <dir_data> <dir_out>"""
import sys, os, math
import numpy as np, pandas as pd

DATA, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
TICK, USD_PER_PT, COMM, RISK, MAXC = 0.1, 10.0, 1.84, 150.0, 5

# ---------- datos ----------
m1 = pd.read_pickle(os.path.join(DATA, "m1.pkl"))
# back-adjust aditivo en cambios de contrato contiguos (no altera P&L intradía, da EMAs continuas)
c = m1["contract"].values; idx = m1.index
adj = np.zeros(len(m1)); off = 0.0
for k in range(len(m1) - 1, 0, -1):
    if c[k] != c[k - 1] and (idx[k] - idx[k - 1]) < pd.Timedelta(days=4):
        off += m1["open"].iat[k] - m1["close"].iat[k - 1]
    adj[k - 1] = off
for col in ("open", "high", "low", "close"):
    m1[col] = m1[col] + adj
gap_starts = [idx[k] for k in range(1, len(m1)) if idx[k] - idx[k - 1] > pd.Timedelta(days=4)] + [idx[0]]

def rs(df, rule):
    g = df.resample(rule, label="left", closed="left")
    o = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "volume": g["volume"].sum()}).dropna()
    return o

m5 = rs(m1, "5min"); h1 = rs(m1, "60min")
m5["ema20"] = m5["close"].ewm(span=20, adjust=False).mean()
m5["ema50"] = m5["close"].ewm(span=50, adjust=False).mean()
pc = m5["close"].shift()
tr = pd.concat([m5["high"] - m5["low"], (m5["high"] - pc).abs(), (m5["low"] - pc).abs()], axis=1).max(axis=1)
m5["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
h1["ema50"] = h1["close"].ewm(span=50, adjust=False).mean()

# ---------- días operables ----------
win = m1.between_time("08:45", "12:59")
cnt = win.groupby(win.index.date).size()
days = [d for d, n in cnt.items() if n >= 250 and pd.Timestamp(d).weekday() < 5]
skip = set()
for gs in gap_starts:  # 2 primeros días tras inicio de datos / hueco largo: calentamiento de EMAs 1h
    after = [d for d in days if pd.Timestamp(d) >= gs.tz_localize(None).normalize()][:2]
    skip.update(after)
days = [d for d in days if d not in skip]

m5_by_day = {d: g for d, g in m5.groupby(m5.index.date)}
m1_by_day = {d: g for d, g in m1.groupby(m1.index.date)}

def bias_for(day, mode):
    if mode == "A":
        return None
    if mode == "B":
        cut = pd.Timestamp(day).tz_localize("America/New_York") + pd.Timedelta(hours=7)
        hb = h1[h1.index <= cut]
        if hb.empty: return 0
        r = hb.iloc[-1]
        return 1 if r["close"] > r["ema50"] else -1
    if mode == "C":
        d1 = m1_by_day[day].between_time("08:45", "12:59")
        return 1 if d1["close"].iloc[-1] > d1["open"].iloc[0] else -1

def rnd(x): return round(round(x / TICK) * TICK, 1)

def run(mode, exit_mode):
    trades = []; week_R = {}
    for day in days:
        bias = bias_for(day, mode)
        wk = pd.Timestamp(day).isocalendar()[:2]
        if week_R.get(wk, 0) <= -4: continue
        b5 = m5_by_day[day]; b1 = m1_by_day[day]
        day0 = pd.Timestamp(day).tz_localize("America/New_York")
        t_open, t_close_sig, t_flat = day0 + pd.Timedelta("08:45:00"), day0 + pd.Timedelta("11:30:00"), day0 + pd.Timedelta("13:00:00")
        allb = m5[(m5.index >= day0 - pd.Timedelta(hours=3)) & (m5.index < t_flat)]
        ntr = nloss = 0; free_after = t_open - pd.Timedelta(minutes=5)
        pos = list(allb.index)
        for j in range(3, len(pos)):
            if ntr >= 2 or nloss >= 2 or week_R.get(wk, 0) <= -4: break
            ts = pos[j]; close_t = ts + pd.Timedelta(minutes=5)
            if close_t < t_open or close_t > t_close_sig or close_t <= free_after: continue
            r = allb.iloc[j]; p1 = allb.iloc[j - 1]; p2 = allb.iloc[j - 2]; e20_3 = allb["ema20"].iloc[j - 3]
            sig = 0
            rng = r.high - r.low
            if bias in (None, 1) and r.ema20 > r.ema50 and r.ema20 > e20_3 and r.low <= r.ema20 + 0.2 * r.atr \
               and r.low <= min(p1.low, p2.low) and r.close > r.ema50 and r.close >= r.low + 0.5 * rng:
                sig = 1
            elif bias in (None, -1) and r.ema20 < r.ema50 and r.ema20 < e20_3 and r.high >= r.ema20 - 0.2 * r.atr \
               and r.high >= max(p1.high, p2.high) and r.close < r.ema50 and r.close <= r.high - 0.5 * rng:
                sig = -1
            if not sig: continue
            if sig == 1:
                P = rnd(r.high + TICK); stop = rnd(min(r.low, p1.low) - TICK); dist = rnd(P - stop)
            else:
                P = rnd(r.low - TICK); stop = rnd(max(r.high, p1.high) + TICK); dist = rnd(stop - P)
            if dist < 0.5 * r.atr:
                dist = rnd(0.5 * r.atr); stop = rnd(P - sig * dist)
            if dist > 1.5 * r.atr or dist > 15.0 or dist <= 0: continue
            nc = min(MAXC, math.floor(RISK / (dist * USD_PER_PT) + 1e-9))
            if nc < 1: continue
            k = 1.5 if exit_mode == "1.5R" else 2.0
            tp = rnd(P + sig * k * dist)
            # --- orden: válida durante las 2 velas de 5m siguientes, hasta 11:30 ---
            v_end = min(close_t + pd.Timedelta(minutes=10), t_close_sig)
            bar1_close = close_t + pd.Timedelta(minutes=5)
            mins = b1[(b1.index >= close_t) & (b1.index < v_end)]
            fill = None; ft = None
            for mt, mb in mins.iterrows():
                if mt >= bar1_close and fill is None:
                    b_1 = allb.iloc[j + 1] if j + 1 < len(allb) else None   # vela 1 cerró al otro lado de EMA50 -> cancela
                    if b_1 is not None and ((sig == 1 and b_1.close < b_1.ema50) or (sig == -1 and b_1.close > b_1.ema50)):
                        break
                if sig == 1:
                    if mb.open >= P: fill = mb.open + TICK
                    elif mb.high >= P: fill = P + TICK
                else:
                    if mb.open <= P: fill = mb.open - TICK
                    elif mb.low <= P: fill = P - TICK
                if fill is not None: ft = mt; break
            if fill is None: continue
            # --- gestión minuto a minuto ---
            cur_stop = stop; be_armed = False; exitp = None; how = None
            path = b1[(b1.index >= ft) & (b1.index < t_flat)]
            mfe = mae = 0.0
            for mt, mb in path.iterrows():
                fav = (mb.high - fill) if sig == 1 else (fill - mb.low)
                adv = (fill - mb.low) if sig == 1 else (mb.high - fill)
                mfe = max(mfe, fav); mae = max(mae, adv)
                if sig == 1:
                    if mt > ft and mb.open <= cur_stop: exitp, how = mb.open - TICK, "stop"
                    elif mb.low <= cur_stop: exitp, how = cur_stop - TICK, "stop"
                    elif mb.high >= tp + TICK: exitp, how = tp, "tp"
                else:
                    if mt > ft and mb.open >= cur_stop: exitp, how = mb.open + TICK, "stop"
                    elif mb.high >= cur_stop: exitp, how = cur_stop + TICK, "stop"
                    elif mb.low <= tp - TICK: exitp, how = tp, "tp"
                if exitp is not None:
                    xt = mt; break
                if exit_mode == "BE" and not be_armed and fav >= dist:
                    be_armed = True; cur_stop = fill
            if exitp is None:
                last = path.iloc[-1]; xt = path.index[-1]
                exitp = last.close - sig * TICK; how = "tiempo"
            if how == "stop" and be_armed: how = "BE"
            pnl = (exitp - fill) * sig * USD_PER_PT * nc - COMM * nc
            R = pnl / (dist * USD_PER_PT * nc)
            trades.append(dict(day=day, signal=ts, fill_t=ft, exit_t=xt, dir="L" if sig == 1 else "C", entry=round(fill, 1),
                               stop=stop, tp=tp, dist=dist, atr=round(r.atr, 2), contracts=nc, exit=round(exitp, 1),
                               how=how, pnl=round(pnl, 2), R=round(R, 3), mfeR=round(mfe / dist, 2), maeR=round(mae / dist, 2)))
            ntr += 1; week_R[wk] = week_R.get(wk, 0) + R
            if pnl > 0: break
            nloss += 1
            free_after = xt
    return pd.DataFrame(trades)

def stats(t):
    if t.empty: return dict(n=0)
    w = t[t.pnl > 0]; l = t[t.pnl <= 0]
    eqR = t.R.cumsum(); eq = t.pnl.cumsum()
    ddR = (eqR - eqR.cummax().clip(lower=0)).min(); dd = (eq - eq.cummax().clip(lower=0)).min()
    thirds = np.array_split(np.array(days, dtype=object), 3)
    tR = [round(t[t.day.isin(set(x))].R.sum(), 1) for x in thirds]
    return dict(n=len(t), win=round(len(w) / len(t) * 100, 1), PF=round(w.pnl.sum() / -l.pnl.sum(), 2) if len(l) and l.pnl.sum() < 0 else np.inf,
                expR=round(t.R.mean(), 3), exp_usd=round(t.pnl.mean(), 1), total_usd=round(t.pnl.sum(), 0), totR=round(t.R.sum(), 1),
                maxDD_R=round(ddR, 1), maxDD_usd=round(dd, 0), tercios_R=tR, largos=int((t.dir == "L").sum()), cortos=int((t.dir == "C").sum()))

rows = []
for mode in ("A", "B", "C"):
    for ex in ("2R", "1.5R", "BE"):
        t = run(mode, ex)
        t.to_csv(os.path.join(OUT, f"trades_{mode}_{ex}.csv"), index=False)
        s = stats(t); s.update(sesgo=mode, salida=ex); rows.append(s)
        print(mode, ex, s, flush=True)
res = pd.DataFrame(rows)
res.to_csv(os.path.join(OUT, "resumen.csv"), index=False)
print(f"\nDías operables: {len(days)}  ({days[0]} -> {days[-1]})")
