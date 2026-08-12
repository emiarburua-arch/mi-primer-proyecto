import json, statistics as st
from collections import Counter, defaultdict
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
W=[t for t in T if t['usd']>0]; L=[t for t in T if t['usd']<=0]

print("### 1. ¿El riesgo en dólares fue constante?")
per=[abs(t['usd']) for t in L]
print(f"  perdida: mediana ${st.median(per):,.2f} | media ${st.mean(per):,.2f} | desv ${st.pstdev(per):,.2f}")
print(f"           min ${min(per):,.2f} | max ${max(per):,.2f}")
q=sorted(per); n=len(q)
print(f"           p10 ${q[n//10]:,.2f} | p25 ${q[n//4]:,.2f} | p75 ${q[3*n//4]:,.2f} | p90 ${q[9*n//10]:,.2f}")
print(f"  -> el riesgo SI fue bastante constante en dolares (coef. variacion {st.pstdev(per)/st.mean(per)*100:.0f}%)")

print("\n### 2. Si el ratio planificado fue siempre 2:1, la ganancia media deberia ser ~2x la perdida media")
print(f"  perdida media  ${st.mean(per):,.2f}   ->  2R esperado = ${2*st.mean(per):,.2f}")
print(f"  ganancia media ${st.mean([t['usd'] for t in W]):,.2f}   ->  deficit de ${2*st.mean(per)-st.mean([t['usd'] for t in W]):,.2f} por ganadora")
print(f"  ratio realizado {st.mean([t['usd'] for t in W])/st.mean(per):.2f} en vez de 2.00")

print("\n### 3. ¿Las ganadoras llegan al target completo o se cierran antes?")
print("  Reparto de ganadoras segun cuantos lotes se usaron:")
g=defaultdict(list)
for t in W:
    k = 3 if t['l3'] is not None else (2 if t['l2'] is not None else 1)
    g[k].append(t)
for k in sorted(g):
    v=g[k]
    print(f"    {k} lote(s): n={len(v):>2}  ganancia media ${st.mean([x['usd'] for x in v]):>8,.2f}"
          f"   ratio vs perdida media = {st.mean([x['usd'] for x in v])/st.mean(per):.2f}")
print("\n  Reparto de PERDEDORAS segun lotes:")
g=defaultdict(list)
for t in L:
    k = 3 if t['l3'] is not None else (2 if t['l2'] is not None else 1)
    g[k].append(t)
for k in sorted(g):
    v=g[k]
    print(f"    {k} lote(s): n={len(v):>2}  perdida media ${st.mean([x['usd'] for x in v]):>8,.2f}")

print("\n### 4. Detalle de los lotes en las ganadoras con parciales")
print(f"  {'fecha':<11}{'sym':<5}{'ct':>3} {'L1':>6}{'L2':>6}{'L3':>6} {'total tk':>9} {'$':>9}  stop implicito y ratio")
for t in W:
    if t['l2'] is None: continue
    lots=[x for x in [t['l1'],t['l2'],t['l3']] if x is not None]
    print(f"  {t['fecha']:<11}{t['sym']:<5}{t['contratos']:>3} "
          f"{str(t['l1']):>6}{str(t['l2']):>6}{str(t['l3'] if t['l3'] is not None else ''):>6} "
          f"{t['ticks']:>9} {t['usd']:>9,.2f}")

print("\n### 5. Ganadoras SIN parciales: ¿llegan a 2R?")
solo=[t for t in W if t['l2'] is None]
print(f"  n={len(solo)}  ganancia media ${st.mean([t['usd'] for t in solo]):,.2f}  = {st.mean([t['usd'] for t in solo])/st.mean(per):.2f}R")
print("  ticks por contrato de esas ganadoras:", sorted(round(t['ticks']/t['contratos']) for t in solo))
print("  ticks por contrato de las perdedoras:", sorted(round(abs(t['ticks'])/t['contratos']) for t in L))
