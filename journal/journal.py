#!/usr/bin/env python3
"""Registro de operaciones (journal/operaciones.csv).

    python3 journal/journal.py add --fecha 2026-11-12 --accion JBS --lado corto \
        --entrada 11.85 --stop 12.01 --objetivo 11.53 --salida 11.53 --acciones 310 \
        --en-juego si --rvol 3.2 --gap 3.5 --tipo-dia venta --cuenta papel
    python3 journal/journal.py list
    python3 journal/journal.py stats
    python3 journal/journal.py edit 3 --salida 11.60 --notas "salí antes"

R = (salida - entrada) / |entrada - stop|, con el signo del lado (corto: al revés).
Resultado en USD = R por acción x acciones - comisiones. Una operación sin salida queda "abierta".
"""
import argparse
import csv
import os
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "operaciones.csv")
COLS = ["id", "fecha", "hora_entrada", "hora_salida", "accion", "lado", "entrada", "stop", "objetivo",
        "salida", "acciones", "comisiones", "riesgo_por_accion", "R", "resultado_usd", "estado",
        "en_juego", "rvol", "gap_pct", "tipo_dia", "cuenta", "setup", "notas"]
NUM = ("entrada", "stop", "objetivo", "salida", "acciones", "comisiones", "rvol", "gap_pct")


def load():
    if not os.path.exists(PATH):
        return []
    with open(PATH, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def save(rows):
    with open(PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLS})


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def compute(r):
    side = -1 if r.get("lado", "").lower().startswith("c") else 1
    e, s, x = f(r.get("entrada")), f(r.get("stop")), f(r.get("salida"))
    risk = abs(e - s) if e is not None and s is not None else None
    r["riesgo_por_accion"] = "%.4f" % risk if risk else ""
    if risk and (s - e) * side >= 0:
        raise SystemExit("el stop está del lado equivocado de la entrada para un %s" % r["lado"])
    if x is None:
        r["estado"], r["R"], r["resultado_usd"] = "abierta", "", ""
        return r
    R = side * (x - e) / risk if risk else None
    r["R"] = "%.2f" % R if R is not None else ""
    n, c = f(r.get("acciones")), f(r.get("comisiones")) or 0.0
    r["resultado_usd"] = "%.2f" % (side * (x - e) * n - c) if n else ""
    tgt = f(r.get("objetivo"))
    if tgt is not None and side * (x - tgt) >= -1e-9:
        r["estado"] = "objetivo"
    elif side * (x - s) <= 1e-9:
        r["estado"] = "stop"
    else:
        r["estado"] = "manual"
    return r


def cmd_add(a):
    rows = load()
    r = {k: v for k, v in vars(a).items() if k in COLS and v is not None}
    r["lado"] = "corto" if a.lado.lower().startswith(("c", "s")) else "largo"
    r["accion"] = a.accion.upper()
    r["id"] = str(max([int(x["id"]) for x in rows] or [0]) + 1)
    rows.append(compute(r))
    save(rows)
    show([rows[-1]])
    return 0


def cmd_edit(a):
    rows = load()
    for r in rows:
        if r["id"] == str(a.id):
            for k, v in vars(a).items():
                if k in COLS and k != "id" and v is not None:
                    r[k] = v
            compute(r)
            save(rows)
            show([r])
            return 0
    raise SystemExit("no hay operación con id %s" % a.id)


def show(rows):
    print("%3s %-10s %-6s %-5s %9s %9s %9s %9s %6s %10s %-8s %-3s %-7s %-6s" % (
        "id", "fecha", "accion", "lado", "entrada", "stop", "objetivo", "salida", "R", "USD", "estado", "EJ", "dia", "cuenta"))
    for r in rows:
        print("%3s %-10s %-6s %-5s %9s %9s %9s %9s %6s %10s %-8s %-3s %-7s %-6s" % (
            r["id"], r["fecha"], r["accion"], r["lado"], r["entrada"], r["stop"], r["objetivo"], r["salida"] or "-",
            r["R"] or "-", r["resultado_usd"] or "-", r["estado"], r.get("en_juego", ""), r.get("tipo_dia", ""), r.get("cuenta", "")))


def cmd_list(a):
    show(load())
    return 0


def block(rows, title):
    done = [r for r in rows if r["R"]]
    if not done:
        return
    R = [float(r["R"]) for r in done]
    usd = [float(r["resultado_usd"]) for r in done if r["resultado_usd"]]
    wins = [x for x in R if x > 0]
    loss = [x for x in R if x <= 0]
    peak = run = dd = 0.0
    for x in R:
        run += x
        peak = max(peak, run)
        dd = min(dd, run - peak)
    print("%-28s n=%3d  ganadoras %5.1f%%  objetivo %5.1f%%  R medio %+.2f  R total %+.1f  gana %+.2f / pierde %+.2f  peor racha %+.1fR%s" % (
        title, len(R), 100 * len(wins) / len(R), 100 * sum(r["estado"] == "objetivo" for r in done) / len(done),
        sum(R) / len(R), sum(R), sum(wins) / len(wins) if wins else 0, sum(loss) / len(loss) if loss else 0, dd,
        ("  USD %+.2f" % sum(usd)) if usd else ""))


def cmd_stats(a):
    rows = load()
    print("Operaciones: %d (%d abiertas)" % (len(rows), sum(r["estado"] == "abierta" for r in rows)))
    block(rows, "TODAS")
    for key, vals in (("lado", ("largo", "corto")), ("en_juego", ("si", "no")), ("tipo_dia", sorted({r.get("tipo_dia", "") for r in rows} - {""})),
                      ("cuenta", ("papel", "real"))):
        for v in vals:
            block([r for r in rows if r.get(key, "") == v], "%s = %s" % (key, v))
    n = sum(1 for r in rows if r["R"])
    if n < 30:
        print("\nCon %d operaciones cerradas todavía es ruido: hacen falta 30 o más para empezar a leer algo, y 100+ para confiar." % n)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Registro de operaciones")
    sub = ap.add_subparsers(dest="cmd")

    def fields(p, required):
        p.add_argument("--fecha", required=required)
        p.add_argument("--accion", required=required)
        p.add_argument("--lado", required=required, help="largo | corto")
        p.add_argument("--entrada", required=required)
        p.add_argument("--stop", required=required)
        for k in ("objetivo", "salida", "acciones", "comisiones", "hora_entrada", "hora_salida", "en_juego", "rvol",
                  "gap_pct", "tipo_dia", "cuenta", "setup", "notas"):
            p.add_argument("--" + k.replace("_", "-"), dest=k)
        p.add_argument("--gap", dest="gap_pct", help="gap en %% a favor de la operación")
    fields(sub.add_parser("add"), True)
    p = sub.add_parser("edit")
    p.add_argument("id", type=int)
    fields(p, False)
    sub.add_parser("list")
    sub.add_parser("stats")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 1
    return {"add": cmd_add, "edit": cmd_edit, "list": cmd_list, "stats": cmd_stats}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
