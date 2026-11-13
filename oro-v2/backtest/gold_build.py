"""Une exports NT8 (1 min, UTC, timestamp = cierre de la vela) de MGC en una serie continua.
Uso: python gold_build.py <dir_raw> <dir_out>"""
import sys, glob, os, re
import pandas as pd

raw, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
frames = []
for p in sorted(glob.glob(os.path.join(raw, "*.txt"))):
    m = re.search(r"(MGC_\d\d-\d\d)", p)
    df = pd.read_csv(p, sep=";", header=None, names=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], format="%Y%m%d %H%M%S", utc=True) - pd.Timedelta(minutes=1)  # inicio de vela
    df["contract"] = m.group(1)
    frames.append(df)
df = pd.concat(frames)
df["ny"] = df["ts"].dt.tz_convert("America/New_York")
df["nydate"] = df["ny"].dt.date
# contrato front por día NY = el de más volumen
vol = df.groupby(["nydate", "contract"])["volume"].sum().reset_index()
front = vol.loc[vol.groupby("nydate")["volume"].idxmax()].set_index("nydate")["contract"]
df = df[df["contract"] == df["nydate"].map(front)].sort_values("ts").drop_duplicates("ts")
df = df.set_index("ny")[["open", "high", "low", "close", "volume", "contract"]]
df.to_pickle(os.path.join(out, "m1.pkl"))
print("M1 barras:", len(df), "|", df.index[0], "->", df.index[-1])
print(df.groupby("contract").apply(lambda g: f"{g.index[0]:%Y-%m-%d} -> {g.index[-1]:%Y-%m-%d}  ({len(g)} barras)"))
# calidad de la ventana operativa 08:45-13:00 NY por día
w = df.between_time("08:45", "12:59")
cnt = w.groupby(w.index.date).size()
print("\nDías con ventana completa (>=250 velas de 1m):", (cnt >= 250).sum(), "| incompletos:", (cnt < 250).sum())
print(cnt[cnt < 250].to_string())
