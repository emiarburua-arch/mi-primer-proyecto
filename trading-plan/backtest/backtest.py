"""Backtest del trading plan MNQ – Entrada tipo 1 (giro tras manipulación de máx/mín de Asia o Europa).

Implementa las reglas de trading-plan/plan.md:
  - Niveles de sesión (sec. 4): Asia 18:00–03:00, Europa 03:00–09:30, ET.
  - Manipulación válida (8.1): profundidad <= 20% del rango de la sesión, máx. 2 perforaciones
    (una perforación termina con 3 cierres seguidos dentro), reingreso con volumen relativo >= 1,5 (8.4).
  - Giro claro (8.1.3): alejamiento >= 20% del rango en <= 12 velas tras el reingreso (variante opcional).
  - Ejecución (5.1, 5.3, 5.4): retroceso (1 vela en contra) -> primera vela a favor -> la siguiente rompe su
    extremo -> orden limit 1 tick dentro, válida solo durante esa vela (se resuelve con velas de 1m).
  - Pivotes (8.2): zigzag con reversión >= 1 x ATR(14) de 5m. El stop debe cubrir el pivote o se descarta.
  - Stop (6): 75/150/300 ticks según ATR(14) de 60m (<100, 100–200, >200 pts); 4/2/1 micros; target 2:1.
  - Riesgo (7): 150 USD por trade, máx. 3 trades/día, corte a -2R diario, cierre a las 16:00 ET.
  - Sesgo (1, 3): rangos activos A-B-C en diario, 4h y 60m (variantes de filtro).

Datos: exportación de NinjaTrader 8 (1 minuto, timestamps UTC = cierre de la barra).
Uso: python3 backtest.py <carpeta_datos> <carpeta_resultados> [desde YYYY-MM-DD] [hasta YYYY-MM-DD]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

TICK = 0.25
USD_PER_POINT_MICRO = 2.0
RISK_USD = 150.0
COST_PER_MICRO_RT = 1.50          # comisión + fees ida y vuelta por micro (supuesto)
STOP_SLIP_TICKS = 1               # deslizamiento en la salida por stop
H = pd.Timedelta(hours=1)
M = pd.Timedelta(minutes=1)

DIAG = []
HOLIDAYS_2026 = {"2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19",
                 "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25"}

P = dict(
    depth_max=0.20,       # 8.1 profundidad máxima (fracción del rango de la sesión)
    max_perfs=2,          # 8.1 perforaciones máximas
    closes_inside=3,      # V1: cierres seguidos dentro que terminan una perforación
    rvol_min=1.5,         # 8.4
    rvol_days=20,
    giro_frac=0.20,       # 8.1.3
    giro_bars=12,
    zz_k=1.0,             # 8.2 multiplicador de ATR(14) 5m
    win_start=pd.Timedelta(hours=9, minutes=30),
    win_end=pd.Timedelta(hours=11, minutes=30),
    close_time=pd.Timedelta(hours=16),
    max_trades=3,
    max_day_loss_r=2.0,
    abc_expiry={"D": 5, "4h": 6, "60m": 8},
)


# ----------------------------------------------------------------------------------------------- datos
def load(datadir):
    frames = []
    for seg, f in enumerate(sorted(glob.glob(os.path.join(datadir, "NQ_*.txt")))):
        d = pd.read_csv(f, sep=";", header=None, names=["ts", "o", "h", "l", "c", "v"])
        t = (pd.to_datetime(d.ts, format="%Y%m%d %H%M%S").dt.tz_localize("UTC")
             .dt.tz_convert("America/New_York").dt.tz_localize(None))
        d["t"] = t - M                     # inicio de la barra de 1m, hora de Nueva York
        d["seg"] = seg
        frames.append(d.drop(columns="ts"))
    df = pd.concat(frames).sort_values("t").drop_duplicates("t", keep="last").reset_index(drop=True)
    df["tday"] = (df.t + pd.Timedelta(hours=6)).dt.normalize()   # día de sesión (18:00 -> día siguiente)
    df["tod"] = df.t - df.t.dt.normalize()
    return df


def resample(df, key):
    g = df.groupby(["seg", key])
    b = g.agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), v=("v", "sum"),
              tday=("tday", "first")).reset_index()
    return b.rename(columns={key: "t"})


def wilder_atr(b, n=14):
    pc = b.groupby("seg").c.shift(1)
    tr = np.maximum(b.h - b.l, np.maximum((b.h - pc).abs(), (b.l - pc).abs())).fillna(b.h - b.l)
    return tr.groupby(b.seg).transform(lambda x: x.ewm(alpha=1 / n, adjust=False).mean())


# --------------------------------------------------------------------------------------------- zigzag
def zigzag(b, k):
    """Pivotes por reversión >= k*ATR. Devuelve, por barra, el índice de la barra del último máximo/mínimo
    pivote CONFIRMADO al cierre de esa barra (-1 si no hay)."""
    n = len(b)
    hi, lo, atr, seg = b.h.values, b.l.values, b.atr_prev.values, b.seg.values
    last_hi = np.full(n, -1)
    last_lo = np.full(n, -1)
    d, ext, ext_i, lh, ll = 1, hi[0], 0, -1, -1
    for i in range(n):
        if i > 0 and seg[i] != seg[i - 1]:
            d, ext, ext_i, lh, ll = 1, hi[i], i, -1, -1
        a = atr[i] if not np.isnan(atr[i]) else hi[i] - lo[i]
        if d == 1:
            if hi[i] > ext:
                ext, ext_i = hi[i], i
            elif ext - lo[i] >= k * a:
                lh, d, ext, ext_i = ext_i, -1, lo[i], i
        else:
            if lo[i] < ext:
                ext, ext_i = lo[i], i
            elif hi[i] - ext >= k * a:
                ll, d, ext, ext_i = ext_i, 1, hi[i], i
        last_hi[i], last_lo[i] = lh, ll
    return last_hi, last_lo


# ------------------------------------------------------------------------------------ rangos A-B-C
def abc_ranges(b, expiry):
    """Rangos activados (reversión) y sesgos de continuación de una temporalidad.
    Devuelve lista de (inicio, fin, dirección): +1 alcista, -1 bajista. Inicio = cierre de B."""
    out = []
    b = b.reset_index(drop=True)
    ends = b.t_end.values
    rows = list(b.itertuples())
    A = None
    for i, B in enumerate(rows):
        if A is None or B.seg != A.seg:
            A = B
            continue
        inside = B.h <= A.h and B.l >= A.l
        if inside:
            continue                                          # P2/P2b: la inside bar no ocupa lugar
        close_in = A.l <= B.c <= A.h
        act = 0
        if B.l < A.l and B.h > A.h:
            act = 0 if close_in else (1 if B.c > A.h else -1) * 2   # P3: outside bar no activa
        elif B.l < A.l and close_in:
            act, target, inval = 1, A.h, B.l
        elif B.h > A.h and close_in:
            act, target, inval = -1, A.l, B.h
        elif B.c > A.h:
            act = 2
        elif B.c < A.l:
            act = -2
        if act in (1, -1):
            end = None
            for j in range(i + 1, min(i + 1 + expiry, len(rows))):
                R = rows[j]
                if R.seg != B.seg:
                    end = ends[j - 1]
                    break
                if (act == 1 and R.h >= target) or (act == -1 and R.l <= target):
                    end = ends[j]
                    break
                if (act == 1 and R.c < inval) or (act == -1 and R.c > inval):
                    end = ends[j]
                    break
            if end is None:
                end = ends[min(i + expiry, len(rows) - 1)]
            out.append((ends[i], end, act))
        elif act in (2, -2) and i + 1 < len(rows):            # continuación: sesgo para la vela C
            out.append((ends[i], ends[i + 1], act // 2))
        A = B
    return out


def bias_at(ranges, t):
    best = None
    for s, e, d in ranges:
        if s <= t < e and (best is None or s > best[0]):
            best = (s, d)
    return 0 if best is None else best[1]


# ----------------------------------------------------------------------------------------- motor
class Setup:
    def __init__(self, name, side, level, rng):
        self.name, self.side, self.level, self.rng = name, side, level, rng
        self.perfs, self.in_perf, self.ins, self.depth = 0, False, 0, 0.0
        self.dead, self.done, self.armed = False, False, False
        self.arm_i, self.fav, self.giro_ok = None, 0.0, False
        self.state, self.ref = None, None
        self.prev_c = None
        self.max_rvol = 0.0


def prepare(df):
    df["t5"] = df.t.dt.floor("5min")
    df["t60"] = df.t.dt.floor("60min")
    df["t4h"] = (df.t - pd.Timedelta(hours=18)).dt.floor("4h") + pd.Timedelta(hours=18)
    b5 = resample(df, "t5")
    b5["atr"] = wilder_atr(b5)
    b5["atr_prev"] = b5.groupby("seg").atr.shift(1)
    b5["tod"] = b5.t - b5.t.dt.normalize()
    b60 = resample(df, "t60")
    b60["atr"] = wilder_atr(b60)
    b60["t_end"] = b60.t + H
    b4 = resample(df, "t4h")
    b4["t_end"] = b4.t + 4 * H
    bd = df.groupby(["seg", "tday"]).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                                         t_end=("t", "last")).reset_index()
    bd["t_end"] = bd.t_end + M
    bd["t"] = bd.tday
    # ATR(14) 60m disponible al inicio de cada barra de 5m (última barra de 60m cerrada)
    a60 = b60[["t_end", "atr"]].rename(columns={"t_end": "t", "atr": "atr60"}).sort_values("t")
    b5 = pd.merge_asof(b5.sort_values("t"), a60, on="t", direction="backward")
    # volumen relativo: mismo horario, últimos 20 días de sesión (sin incluir el día actual)
    piv = b5.pivot_table(index="tday", columns="tod", values="v", aggfunc="sum")
    avg = piv.rolling(P["rvol_days"], min_periods=10).mean().shift(1)
    avg_long = avg.stack().rename("vavg").reset_index()
    b5 = b5.merge(avg_long, on=["tday", "tod"], how="left")
    b5["rvol"] = b5.v / b5.vavg
    b5 = b5.sort_values("t").reset_index(drop=True)
    b5["zz_hi"], b5["zz_lo"] = zigzag(b5, P["zz_k"])
    # sesiones Asia / Europa
    tod = df.tod
    asia = df[(tod >= pd.Timedelta(hours=18)) | (tod < pd.Timedelta(hours=3))]
    eur = df[(tod >= pd.Timedelta(hours=3)) & (tod < pd.Timedelta(hours=9, minutes=30))]
    sess = pd.DataFrame({
        "asia_h": asia.groupby("tday").h.max(), "asia_l": asia.groupby("tday").l.min(),
        "asia_n": asia.groupby("tday").h.size(),
        "eur_h": eur.groupby("tday").h.max(), "eur_l": eur.groupby("tday").l.min(),
        "eur_n": eur.groupby("tday").h.size()})
    ranges = {"D": abc_ranges(bd, P["abc_expiry"]["D"]),
              "4h": abc_ranges(b4, P["abc_expiry"]["4h"]),
              "60m": abc_ranges(b60, P["abc_expiry"]["60m"])}
    return b5, sess, ranges


def stop_points(atr60):
    if atr60 < 100:
        return 75 * TICK, 4
    if atr60 <= 200:
        return 150 * TICK, 2
    return 300 * TICK, 1


def simulate_exit(m1, start_i, side, entry, stop, target, close_t):
    """Recorre velas de 1m desde start_i. Prioridad al stop si ambos ocurren en el mismo minuto."""
    t, hi, lo, c = m1.t.values, m1.h.values, m1.l.values, m1.c.values
    for k in range(start_i, len(m1)):
        if t[k] >= close_t:
            return t[k - 1] + np.timedelta64(1, "m"), c[k - 1], "cierre 16:00"
        if side == 1:
            if lo[k] <= stop:
                return t[k] + np.timedelta64(1, "m"), stop - STOP_SLIP_TICKS * TICK, "stop"
            if hi[k] >= target + TICK:
                return t[k] + np.timedelta64(1, "m"), target, "target"
        else:
            if hi[k] >= stop:
                return t[k] + np.timedelta64(1, "m"), stop + STOP_SLIP_TICKS * TICK, "stop"
            if lo[k] <= target - TICK:
                return t[k] + np.timedelta64(1, "m"), target, "target"
    k = len(m1) - 1
    return t[k] + np.timedelta64(1, "m"), c[k], "fin de datos"


def backtest(df, b5, sess, ranges, from_day, to_day, filt="none", giro=False, vol="reingreso", stop_mode="atr"):
    p = P
    trades, events = [], []
    m1_by_day = {k: g.reset_index(drop=True) for k, g in df.groupby("tday")}
    b5_by_day = {k: g for k, g in b5.groupby("tday")}
    days = [d for d in sorted(b5_by_day) if from_day <= d <= to_day and d.strftime("%Y-%m-%d") not in HOLIDAYS_2026]
    lo5, hi5 = b5.l.values, b5.h.values
    for day in days:
        if day not in sess.index:
            continue
        s = sess.loc[day]
        if s.asia_n < 300 or s.eur_n < 300:
            continue
        bars = b5_by_day[day]
        rth = bars[(bars.tod >= p["win_start"]) & (bars.tod < p["close_time"])]
        if len(rth) < 70:
            continue
        m1 = m1_by_day[day]
        m1_rth = m1[m1.t >= day + p["win_start"]].reset_index(drop=True)
        m1_idx = {t: i for i, t in enumerate(m1_rth.t.values)}
        close_t = (day + p["close_time"]).to_datetime64()
        ar, er = s.asia_h - s.asia_l, s.eur_h - s.eur_l
        setups = [Setup("max Europa", -1, s.eur_h, er), Setup("min Europa", 1, s.eur_l, er)]
        if s.eur_h <= s.asia_h:
            setups.append(Setup("max Asia", -1, s.asia_h, ar))
        if s.eur_l >= s.asia_l:
            setups.append(Setup("min Asia", 1, s.asia_l, ar))
        n_tr, day_r, busy_until = 0, 0.0, None
        for gi, bar in rth.iterrows():
            in_win = bar.tod < p["win_end"]
            for S in setups:
                if S.dead or S.done:
                    continue
                L, sd = S.level, S.side
                fav_hi = bar.h if sd == 1 else -bar.l
                # 1) confirmación + orden limit (vela actual) ------------------------------------------
                broke = False
                if S.armed and S.state == "CONF":
                    ref_ext = S.ref.h if sd == 1 else S.ref.l
                    if (sd == 1 and bar.h > ref_ext) or (sd == -1 and bar.l < ref_ext):
                        broke = True
                        S.state = "WAIT_PULL"
                        ok = in_win and not np.isnan(bar.atr60) and n_tr < p["max_trades"] and day_r > -p["max_day_loss_r"] \
                            and (busy_until is None or bar.t >= busy_until)
                        if ok and giro and not S.giro_ok:
                            ok = False
                            events.append((day, S.name, "sin giro claro"))
                        if ok and filt != "none":
                            bias = [bias_at(ranges[tf], bar.t) for tf in ("D", "4h", "60m")]
                            fondo = next((x for x in bias if x != 0), 0)
                            if filt == "fondo" and fondo != sd:
                                ok = False
                            if filt == "cualquiera" and sd not in bias:
                                ok = False
                            if not ok:
                                events.append((day, S.name, "filtro de sesgo"))
                        if ok:
                            limit = ref_ext - TICK if sd == 1 else ref_ext + TICK
                            stp, qty = stop_points(bar.atr60)
                            if stop_mode == "fijo300":
                                stp, qty = 300 * TICK, 1
                            # pivote: extremo desde el último pivote opuesto confirmado (velas cerradas)
                            j = gi - 1
                            if sd == 1:
                                k0 = b5.zz_hi.values[j]
                                piv = lo5[max(k0, 0):j + 1].min()
                            else:
                                k0 = b5.zz_lo.values[j]
                                piv = hi5[max(k0, 0):j + 1].max()
                            if stop_mode == "minimo_cubre":
                                for stp, qty in ((75 * TICK, 4), (150 * TICK, 2), (300 * TICK, 1)):
                                    if abs(limit - piv) + TICK <= stp:
                                        break
                            stop = limit - stp if sd == 1 else limit + stp
                            covers = (stop <= piv - TICK) if sd == 1 else (stop >= piv + TICK)
                            # fill: primer minuto que rompe, luego algún minuto posterior toca el limit
                            i0 = m1_idx.get(bar.t.to_datetime64())
                            fill_i = None
                            if i0 is not None:
                                brk = None
                                for k in range(i0, min(i0 + 5, len(m1_rth))):
                                    mk = m1_rth.iloc[k]
                                    if brk is None:
                                        if (sd == 1 and mk.h > ref_ext) or (sd == -1 and mk.l < ref_ext):
                                            brk = k
                                    elif (sd == 1 and mk.l <= limit) or (sd == -1 and mk.h >= limit):
                                        fill_i = k
                                        break
                            DIAG.append(dict(dia=day, nivel=S.name, t=bar.t, limit=limit, piv=piv,
                                             dist=abs(limit - piv), stop_pts=stp, atr60=bar.atr60,
                                             atr5=bar.atr_prev, covers=covers, fill=fill_i is not None))
                            if not covers:
                                events.append((day, S.name, "stop no cubre el pivote"))
                            elif fill_i is None:
                                events.append((day, S.name, "limit no ejecutada"))
                            else:
                                target = limit + 2 * stp if sd == 1 else limit - 2 * stp
                                ex_t, ex_p, why = simulate_exit(m1_rth, fill_i + 1, sd, limit, stop, target, close_t)
                                pts = (ex_p - limit) * sd
                                gross = pts * USD_PER_POINT_MICRO * qty
                                net = gross - COST_PER_MICRO_RT * qty
                                trades.append(dict(
                                    dia=day.date(), nivel=S.name, lado="largo" if sd == 1 else "corto",
                                    entrada_t=m1_rth.t.iloc[fill_i], entrada=limit, stop=stop, target=target,
                                    pivote=piv, atr60=round(bar.atr60, 1), micros=qty, salida_t=ex_t,
                                    salida=ex_p, motivo=why, usd_bruto=gross, usd_neto=net,
                                    r_bruto=gross / RISK_USD, r_neto=net / RISK_USD,
                                    profundidad=round(S.depth / S.rng, 3), perforaciones=S.perfs,
                                    giro_ok=S.giro_ok))
                                n_tr += 1
                                day_r += net / RISK_USD
                                busy_until = pd.Timestamp(ex_t)
                                S.done = True
                                events.append((day, S.name, "trade"))
                                continue
                # 2) seguimiento de la manipulación ---------------------------------------------------
                pierce = bar.l < L if sd == 1 else bar.h > L
                inside_close = bar.c > L if sd == 1 else bar.c < L
                if pierce or (not S.armed and S.perfs >= 1):
                    S.max_rvol = max(S.max_rvol, bar.rvol if not np.isnan(bar.rvol) else 0)
                if pierce:
                    if not S.in_perf:
                        S.perfs += 1
                        S.in_perf, S.ins = True, 0
                    S.depth = max(S.depth, (L - bar.l) if sd == 1 else (bar.h - L))
                if S.in_perf:
                    S.ins = S.ins + 1 if inside_close else 0
                    if S.ins >= p["closes_inside"]:
                        S.in_perf = False
                if S.perfs > p["max_perfs"] or S.depth > p["depth_max"] * S.rng:
                    S.dead = True
                    continue
                # 3) reingreso con volumen y máquina de estados --------------------------------------
                if not S.armed:
                    crossed = pierce or (S.prev_c is not None and ((S.prev_c <= L) if sd == 1 else (S.prev_c >= L)))
                    vol_ok = {"reingreso": bar.rvol >= p["rvol_min"],
                              "climax": max(S.max_rvol, bar.rvol if not np.isnan(bar.rvol) else 0) >= p["rvol_min"],
                              "ninguno": True}[vol]
                    if S.perfs >= 1 and inside_close and crossed and vol_ok:
                        S.armed, S.arm_i, S.state = True, gi, "WAIT_PULL"
                        S.fav = bar.h if sd == 1 else bar.l
                else:
                    S.fav = max(S.fav, bar.h) if sd == 1 else min(S.fav, bar.l)
                    if not S.giro_ok and abs(S.fav - L) >= p["giro_frac"] * S.rng and gi - S.arm_i <= p["giro_bars"]:
                        S.giro_ok = True
                    green, red = bar.c > bar.o, bar.c < bar.o
                    fav_c, against_c = (green, red) if sd == 1 else (red, green)
                    if S.state == "WAIT_PULL" and against_c:
                        S.state = "WAIT_GREEN"
                    elif S.state == "WAIT_GREEN" and fav_c:
                        S.state, S.ref = "CONF", bar
                    elif S.state == "CONF" and not broke:
                        if fav_c:
                            S.ref = bar
                        else:
                            S.state = "WAIT_GREEN"
                S.prev_c = bar.c
    return pd.DataFrame(trades), pd.DataFrame(events, columns=["dia", "nivel", "evento"])


# ------------------------------------------------------------------------------------- estadística
def stats(tr, col="r_neto", seed=1):
    if tr.empty:
        return dict(trades=0)
    r = tr[col].values
    eq = np.cumsum(r)
    dd = (np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq).max()
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    rng = np.random.default_rng(seed)
    boots = rng.choice(r, size=(10000, len(r)), replace=True).mean(axis=1)
    t = r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 1 and r.std(ddof=1) > 0 else np.nan
    return dict(trades=len(r), aciertos=round((r > 0).mean() * 100, 1), r_medio=round(r.mean(), 3),
                r_total=round(r.sum(), 2), profit_factor=round(wins / losses, 2) if losses else np.inf,
                max_dd_r=round(dd, 2), t_stat=round(t, 2),
                ic95=f"[{np.percentile(boots, 2.5):.3f}, {np.percentile(boots, 97.5):.3f}]",
                p_media_pos=round((boots > 0).mean(), 3))


def prop_mc(tr, n=10000, seed=2, target=3000, trail=2500, max_trades=400):
    """Probabilidad de pasar la prueba (beneficio 3000, trailing 2500 sobre equity cerrado)."""
    if tr.empty:
        return np.nan
    r = tr.usd_neto.values
    rng = np.random.default_rng(seed)
    passed = 0
    for _ in range(n):
        eq = peak = 0.0
        for x in rng.choice(r, size=max_trades, replace=True):
            eq += x
            peak = max(peak, eq)
            if eq >= target:
                passed += 1
                break
            if eq <= peak - trail:
                break
    return passed / n


if __name__ == "__main__":
    datadir, outdir = sys.argv[1], sys.argv[2]
    d0 = pd.Timestamp(sys.argv[3] if len(sys.argv) > 3 else "2026-01-01")
    d1 = pd.Timestamp(sys.argv[4] if len(sys.argv) > 4 else "2026-11-23")
    os.makedirs(outdir, exist_ok=True)
    df = load(datadir)
    b5, sess, ranges = prepare(df)
    rows = []
    for stop_mode in ("atr", "fijo300", "minimo_cubre"):
        for vol in ("reingreso", "climax", "ninguno"):
            for filt in ("none", "cualquiera", "fondo"):
                for giro in (False, True):
                    tr, ev = backtest(df, b5, sess, ranges, d0, d1, filt, giro, vol, stop_mode)
                    name = f"stop={stop_mode}|vol={vol}|filtro={filt}|giro={'si' if giro else 'no'}"
                    tr.to_csv(os.path.join(outdir, f"trades_{stop_mode}_{vol}_{filt}_{'giro' if giro else 'sin_giro'}.csv"), index=False)
                    st = {"variante": name}
                    st.update(stats(tr))
                    st["prob_pasar_prueba"] = prop_mc(tr)
                    cnt = ev.evento.value_counts().to_dict() if not ev.empty else {}
                    st.update({f"ev:{k}": v for k, v in cnt.items()})
                    rows.append(st)
                    print(name, {k: v for k, v in st.items() if k != "variante"}, flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(outdir, "resumen.csv"), index=False)
