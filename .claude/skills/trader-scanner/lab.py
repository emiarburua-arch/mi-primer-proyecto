#!/usr/bin/env python3
"""Scanner Lab (trader-scanner): measure whether filters improve the
opening-range breakout BEFORE they go into the live scan.

    python3 lab.py fetch --top 500 --cache trader/lab        # liquid names, 60 days of 5-minute bars
    python3 lab.py test  --cache trader/lab                  # ORB long + short, every filter, in R
    python3 lab.py test  --cache trader/lab --target 1       # 1R target instead of 2R

The rule simulated is the skill's own: the 15-minute opening range, entry at the
close of the first 5-minute bar that closes beyond it (long above the high,
short below the low), stop at the range midpoint, target at N times the risk,
flat at 3:55 PM, no new entries after 3:30 PM. A bar that touches both the stop
and the target counts as the stop (the conservative read of a 5-minute bar).
Costs: --cost cents per share per side (default 1) charged in R.

Features measured at the trigger bar:
  rvol      opening-range volume / its average over the previous 20 sessions
  gap       9:30 open vs the previous session's last close, signed in the trade's direction
  vwap      the entry is on the trade's side of the session VWAP
  spy       SPY is on the same side of its own VWAP at that bar
  trig_vol  the trigger bar's volume / the average opening-range bar's volume

This is research on the last ~60 sessions only (Yahoo's limit for 5-minute
bars). Small samples lie: read the half-by-half columns and the day-clustered
t before trusting any row. It is not a prediction and not advice.
"""
import argparse
import datetime
import gzip
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan  # noqa: E402

INDEXES = ("SPY", "QQQ")
FLAT = datetime.time(15, 55)
LAST_ENTRY = datetime.time(15, 30)
N_RANGE = 3          # 15 minutes of 5-minute bars
BASE_DAYS = 20       # sessions for the average opening-range volume
MIN_BASE = 10


# ---------------------------------------------------------------- data

def fetch(a):
    os.makedirs(a.cache, exist_ok=True)
    if not os.path.exists(a.universe):
        raise scan.ScanError("no %s: run `scan.py universe --out %s` first" % (a.universe, a.universe))
    syms = scan.symbols_from_file(a.universe)
    print("Ranking %d symbols by dollar volume (daily spark, 1 month)..." % len(syms), file=sys.stderr)
    daily, _ = scan.fetch_spark(syms, "1mo", "1d", a.pause)
    ranked = []
    for s, ser in daily.items():
        cs = [c for c in ser["c"] if c is not None]
        meta = ser.get("meta") or {}
        if not cs or cs[-1] < a.min_price:
            continue
        vol = meta.get("regularMarketVolume") or 0
        ranked.append((cs[-1] * vol, s))
    # spark has no volume per day: one session's volume ranks well enough to pick the liquid names
    ranked.sort(reverse=True)
    pick = [s for _, s in ranked[:a.top]]
    for idx in INDEXES:
        if idx not in pick:
            pick.append(idx)
    print("Fetching 60 days of 5-minute bars for %d symbols..." % len(pick), file=sys.stderr)
    got, t0 = 0, time.time()
    for k, s in enumerate(pick):
        path = os.path.join(a.cache, "%s.json.gz" % s)
        if os.path.exists(path) and not a.refresh:
            got += 1
            continue
        if k:
            scan.SLEEP(a.pause)
        try:
            text = scan.yahoo_get(scan.chart_path(s, "60d", "5m"))
        except scan.ScanError as e:
            print("  %s: %s" % (s, e), file=sys.stderr)
            continue
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            fh.write(text)
        got += 1
        if (k + 1) % 50 == 0:
            print("  %d of %d (%.0fs)" % (k + 1, len(pick), time.time() - t0), file=sys.stderr)
    print("Cached %d charts in %s." % (got, a.cache))
    return 0


def load_days(path, sym):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        ser = scan.parse_chart(fh.read(), sym)
    days = {}
    for i, ts in enumerate(ser["t"]):
        o, h, l, c, v = (ser[k][i] if ser.get(k) else None for k in ("o", "h", "l", "c", "v"))
        if None in (o, h, l, c):
            continue
        et = scan.ts_to_eastern(ts)
        if et.second or et.minute % 5:
            continue
        s = scan.session(et.date())
        if not s or et.time() < scan.OPEN or et.time() >= s[1]:
            continue
        days.setdefault(et.date(), {})[et] = {"t": et, "o": o, "h": h, "l": l, "c": c, "v": v or 0}
    out = {}
    for d, bars in days.items():
        s = scan.session(d)
        want = int((datetime.datetime.combine(d, s[1]) - scan.slot(d, 0)).total_seconds() // 300)
        lst = [bars[k] for k in sorted(bars)]
        if len(lst) == want and all(b["t"] == scan.slot(d, j) for j, b in enumerate(lst)):
            out[d] = lst  # complete sessions only: a missing bar is a halt or a thin stock
    return out


def vwap_series(bars):
    pv = vv = 0.0
    out = []
    for b in bars:
        tp = (b["h"] + b["l"] + b["c"]) / 3
        pv += tp * b["v"]
        vv += b["v"]
        out.append(pv / vv if vv else b["c"])
    return out


# ---------------------------------------------------------------- simulation

def simulate(bars, k, side, entry, stop, target_r, cost):
    """Walk from bar k+1. -> (R net, outcome)."""
    risk = abs(entry - stop)
    tgt = entry + side * target_r * risk
    flat_dt = datetime.datetime.combine(bars[0]["t"].date(), FLAT)
    res, how, last = None, "close", entry
    for b in bars[k + 1:]:
        if b["t"] >= flat_dt:
            break
        last = b["c"]
        if side > 0:
            if b["o"] <= stop:
                res, how = (b["o"] - entry) / risk, "stop"
            elif b["l"] <= stop:
                res, how = -1.0, "stop"
            elif b["h"] >= tgt:
                res, how = target_r if b["o"] < tgt else (b["o"] - entry) / risk, "target"
        else:
            if b["o"] >= stop:
                res, how = (entry - b["o"]) / risk, "stop"
            elif b["h"] >= stop:
                res, how = -1.0, "stop"
            elif b["l"] <= tgt:
                res, how = target_r if b["o"] > tgt else (entry - b["o"]) / risk, "target"
        if res is not None:
            break
    if res is None:
        res = side * (last - entry) / risk
    return res - 2 * cost / risk, how


def trades_for(sym, days, spy, target_r, cost):
    out = []
    order = sorted(days)
    for j, d in enumerate(order):
        if j < MIN_BASE + 1:
            continue
        prev = order[j - BASE_DAYS - 1:j] if j > BASE_DAYS else order[:j]
        base = [sum(b["v"] for b in days[p][:N_RANGE]) for p in prev[-BASE_DAYS:]]
        base = [x for x in base if x > 0]
        if len(base) < MIN_BASE:
            continue
        bars = days[d]
        prev_close = days[order[j - 1]][-1]["c"]
        rng = bars[:N_RANGE]
        oh, ol = max(b["h"] for b in rng), min(b["l"] for b in rng)
        or_vol = sum(b["v"] for b in rng)
        if or_vol <= 0 or rng[0]["o"] < 5:
            continue
        mid = round((oh + ol) / 2, 2)
        vw = vwap_series(bars)
        spy_vw = vwap_series(spy[d]) if spy and d in spy else None
        rvol = or_vol / (sum(base) / len(base))
        gap = rng[0]["o"] / prev_close - 1
        avg_or_bar = or_vol / N_RANGE
        last_entry = datetime.datetime.combine(d, LAST_ENTRY)
        for side in (1, -1):
            for k in range(N_RANGE, len(bars)):
                b = bars[k]
                if b["t"] + datetime.timedelta(minutes=5) > last_entry:
                    break
                if (side > 0 and b["c"] > oh) or (side < 0 and b["c"] < ol):
                    entry = b["c"]
                    risk = abs(entry - mid)
                    if risk < max(0.05, entry * 0.001):
                        break  # too tight to survive the spread: trader-exit refuses it
                    r, how = simulate(bars, k, side, entry, mid, target_r, cost)
                    spy_ok = None
                    if spy_vw is not None and k < len(spy[d]):
                        spy_ok = (spy[d][k]["c"] - spy_vw[k]) * side > 0
                    out.append({
                        "sym": sym, "day": d.isoformat(), "side": side, "r": r, "how": how,
                        "rvol": rvol, "gap": gap * side, "abs_gap": abs(gap),
                        "vwap": (entry - vw[k]) * side > 0, "spy": spy_ok,
                        "trig_vol": b["v"] / avg_or_bar if avg_or_bar else 0,
                        "early": (b["t"] + datetime.timedelta(minutes=5)).time() <= datetime.time(10, 30),
                        "risk_pct": risk / entry * 100,
                    })
                    break
    return out


# ---------------------------------------------------------------- report

def stats(rows, halves):
    n = len(rows)
    if not n:
        return None
    rs = [t["r"] for t in rows]
    byday = {}
    for t in rows:
        byday.setdefault(t["day"], []).append(t["r"])
    dm = [sum(v) / len(v) for v in byday.values()]
    mu = sum(dm) / len(dm)
    sd = math.sqrt(sum((x - mu) ** 2 for x in dm) / (len(dm) - 1)) if len(dm) > 1 else 0
    tstat = mu / (sd / math.sqrt(len(dm))) if sd and len(dm) >= 10 else 0.0  # too few days to say
    h1 = [t["r"] for t in rows if t["day"] < halves]
    h2 = [t["r"] for t in rows if t["day"] >= halves]
    avg = lambda x: sum(x) / len(x) if x else float("nan")  # noqa: E731
    return {"n": n, "days": len(byday), "win": sum(1 for t in rows if t["how"] == "target") / n * 100,
            "stop": sum(1 for t in rows if t["how"] == "stop") / n * 100,
            "avg": avg(rs), "h1": avg(h1), "h2": avg(h2), "t": tstat}


def top_per_day(rows, k):
    byday = {}
    for t in rows:
        byday.setdefault(t["day"], []).append(t)
    out = []
    for v in byday.values():
        out += sorted(v, key=lambda t: -t["rvol"])[:k]
    return out


FILTERS = [
    ("all breakouts", lambda t: True),
    ("rvol >= 1.5", lambda t: t["rvol"] >= 1.5),
    ("rvol >= 2", lambda t: t["rvol"] >= 2),
    ("rvol >= 3", lambda t: t["rvol"] >= 3),
    ("gap >= 2% with the trade", lambda t: t["gap"] >= 0.02),
    ("gap >= 2% against the trade", lambda t: t["gap"] <= -0.02),
    ("|gap| >= 2%", lambda t: t["abs_gap"] >= 0.02),
    ("on VWAP side", lambda t: t["vwap"]),
    ("SPY with the trade", lambda t: t["spy"] is True),
    ("SPY against the trade", lambda t: t["spy"] is False),
    ("trigger vol >= 1.5x", lambda t: t["trig_vol"] >= 1.5),
    ("trigger by 10:30", lambda t: t["early"]),
    ("trigger after 10:30", lambda t: not t["early"]),
    ("rvol>=2 + SPY with", lambda t: t["rvol"] >= 2 and t["spy"] is True),
    ("rvol>=2 + gap>=2% with", lambda t: t["rvol"] >= 2 and t["gap"] >= 0.02),
    ("rvol>=2 + gap with + SPY with", lambda t: t["rvol"] >= 2 and t["gap"] >= 0.02 and t["spy"] is True),
    ("in play: rvol>=3 + |gap|>=3%", lambda t: t["rvol"] >= 3 and t["abs_gap"] >= 0.03),
]


def report(a):
    files = sorted(f for f in os.listdir(a.cache) if f.endswith(".json.gz"))
    if not files:
        raise scan.ScanError("nothing cached in %s: run `lab.py fetch` first" % a.cache)
    spy = load_days(os.path.join(a.cache, "SPY.json.gz"), "SPY") if "SPY.json.gz" in files else None
    trades = []
    for f in files:
        sym = f[:-8]
        if sym in INDEXES and not a.include_index:
            continue
        trades += trades_for(sym, load_days(os.path.join(a.cache, f), sym), spy, a.target, a.cost / 100.0)
    if not trades:
        raise scan.ScanError("no trades: not enough complete sessions")
    days = sorted({t["day"] for t in trades})
    halves = days[len(days) // 2]
    out = {"symbols": len(files), "days": len(days), "from": days[0], "to": days[-1], "split": halves,
           "target_r": a.target, "cost_cents": a.cost, "rows": []}
    for side_name, side in (("LONG", 1), ("SHORT", -1)):
        rows = [t for t in trades if t["side"] == side]
        for name, f in FILTERS:
            st = stats([t for t in rows if f(t)], halves)
            if st:
                out["rows"].append(dict(st, side=side_name, filter=name))
        st = stats(top_per_day(rows, 5), halves)
        if st:
            out["rows"].append(dict(st, side=side_name, filter="top 5 a day by rvol"))
    if a.json:
        print(json.dumps(out, indent=2))
        return 0
    print("Scanner Lab: %d symbols, %d sessions (%s to %s), target %gR, cost %g c/share/side."
          % (out["symbols"], out["days"], out["from"], out["to"], a.target, a.cost))
    print("avg R is after costs. 1st/2nd half split at %s. t = day-clustered t-stat (|t|>2 is worth a look)." % halves)
    for side_name in ("LONG", "SHORT"):
        print()
        print("%-6s %-32s %6s %5s %6s %6s %7s %7s %7s %6s" % (side_name, "filter", "trades", "days", "tgt%",
                                                                "stop%", "avg R", "1st", "2nd", "t"))
        for r in out["rows"]:
            if r["side"] != side_name:
                continue
            print("%-6s %-32s %6d %5d %5.1f%% %5.1f%% %+7.3f %+7.3f %+7.3f %+6.2f" % (
                "", r["filter"], r["n"], r["days"], r["win"], r["stop"], r["avg"], r["h1"], r["h2"], r["t"]))
    print()
    print("Research on ~40 sessions, not a prediction. A row only counts if both halves agree and |t| > 2.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scanner Lab: test ORB filters on 60 days of 5-minute bars.")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("fetch", help="pick the most traded names and cache 60 days of 5-minute bars")
    p.add_argument("--universe", default=scan.DEFAULT_UNIVERSE)
    p.add_argument("--top", type=int, default=500)
    p.add_argument("--min-price", type=float, default=5.0)
    p.add_argument("--cache", default="trader/lab")
    p.add_argument("--pause", type=float, default=scan.PAUSE)
    p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("test", help="simulate the ORB and report every filter")
    p.add_argument("--cache", default="trader/lab")
    p.add_argument("--target", type=float, default=2.0, help="target in R (2)")
    p.add_argument("--cost", type=float, default=1.0, help="cents per share per side (1)")
    p.add_argument("--include-index", action="store_true", help="also trade SPY and QQQ")
    p.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 1
    try:
        return {"fetch": fetch, "test": report}[a.cmd](a)
    except scan.ScanError as e:
        print("lab.py: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
