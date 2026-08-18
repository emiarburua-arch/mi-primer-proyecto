#!/usr/bin/env python3
"""
Simulación del SISTEMA COMPLETO sobre el auto-giro: aplica los topes (máquina de estado),
convierte R a dólares reales (MCL + comisión) y arma curva de equity, drawdown y métricas
de riesgo. Es la foto de "cómo habría evolucionado la cuenta operando el sistema entero".

Reglas de gestión (TPP-v2 §1.5, §7):
  - máx 2 operaciones/día (ya viene del detector) → dos stops = −2R = día cerrado.
  - tope semanal: si la semana toca −3R, se cierra la semana (no se abren más).
  - riesgo fijo $150 por operación; MCL, contratos por escenario (A=10, B=5, C=3, D=2).
  - comisión MCL $1,84 round-turn por contrato.

Uso:  CL_DATA_DIR=/ruta python account_sim.py
"""
import os
from collections import defaultdict
import backtest as B

RISK = 150.0
COMMISSION_RT = 1.84                      # MCL, por contrato, round turn
CONTRACTS = {'A': 10, 'B': 5, 'C': 3, 'D': 2}   # MCL para riesgo $150 por escenario
WEEK_STOP_R = -3.0


def apply_week_stop(trades):
    """Aplica el tope semanal −3R: una vez que la semana toca −3R, se saltan las restantes."""
    week_R = defaultdict(float)
    kept = []
    for t in trades:
        wk = t['day'].isocalendar()[:2]
        if week_R[wk] <= WEEK_STOP_R:
            continue
        kept.append(t)
        week_R[wk] += t['R']
    return kept


def to_dollars(trades):
    for t in trades:
        c = CONTRACTS[t['esc']]
        t['usd'] = t['R'] * RISK - COMMISSION_RT * c
    return trades


def metrics(trades):
    if not trades:
        return {}
    eq = 0.0
    peak = 0.0
    max_dd = 0.0
    curve = []
    streak = worst_streak = 0
    for t in trades:
        eq += t['usd']
        curve.append(eq)
        peak = max(peak, eq)
        max_dd = max(max_dd, peak - eq)
        if t['usd'] < 0:
            streak += 1
            worst_streak = max(worst_streak, streak)
        else:
            streak = 0
    R = [t['R'] for t in trades]
    usd = [t['usd'] for t in trades]
    wins = [x for x in usd if x > 0]
    losses = [x for x in usd if x < 0]
    # por semana / peor día
    byday = defaultdict(float)
    byweek = defaultdict(float)
    for t in trades:
        byday[t['day']] += t['usd']
        byweek[t['day'].isocalendar()[:2]] += t['usd']
    return {
        'n': len(trades),
        'winrate': 100 * len(wins) / len(trades),
        'R_total': sum(R),
        'usd_total': eq,
        'PF': (sum(wins) / -sum(losses)) if losses else float('inf'),
        'max_dd': max_dd,
        'max_dd_R': max_dd / RISK,
        'worst_day': min(byday.values()),
        'worst_week': min(byweek.values()),
        'worst_streak': worst_streak,
        'curve': curve,
    }


def report(name, trades):
    m = metrics(trades)
    if not m:
        print(f'{name}: sin trades')
        return
    print(f'\n== {name} ==')
    print(f'  operaciones: {m["n"]}   winrate: {m["winrate"]:.0f}%   profit factor: {m["PF"]:.2f}')
    print(f'  R total: {m["R_total"]:+.0f}   P&L: ${m["usd_total"]:+,.0f}')
    print(f'  drawdown máx: ${m["max_dd"]:,.0f}  ({m["max_dd_R"]:.1f} R)')
    print(f'  peor día: ${m["worst_day"]:+,.0f}   peor semana: ${m["worst_week"]:+,.0f}   '
          f'racha perdedora máx: {m["worst_streak"]}')
    by = defaultdict(list)
    for t in trades:
        by[t['day'].year].append(t)
    for y in sorted(by):
        mm = metrics(by[y])
        print(f'    {y}: {mm["n"]:3d} ops   R {mm["R_total"]:+.0f}   ${mm["usd_total"]:+,.0f}   '
              f'DD máx ${mm["max_dd"]:,.0f}')


def main():
    m5 = B.load('CL_M5_continuo.csv')
    m60 = B.load('CL_M60_continuo.csv')
    atr = B.atr14(m60)
    raw = B.backtest_giro_multi(m5, m60, atr, target_R=2.0)
    print(f'Auto-giro: {len(raw)} señales brutas ({m5[0][0].date()} → {m5[-1][0].date()})')

    report('SIN tope semanal (solo 2/día)', to_dollars([dict(t) for t in raw]))
    report('CON tope semanal −3R (sistema completo)', to_dollars(apply_week_stop([dict(t) for t in raw])))


if __name__ == '__main__':
    main()
