import json, statistics as st
from collections import defaultdict
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
L=[t for t in T if t['usd']<=0]; W=[t for t in T if t['usd']>0]
RISK=st.mean([abs(t['usd']) for t in L])
print(f"Riesgo medio por operacion: ${RISK:,.2f}  (1R)\n")

print("### Cada ganadora, medida en R  (2R = target completo si el ratio 2:1 se respeto)")
mult=sorted(((t['usd']/RISK, t) for t in W), key=lambda p: p[0])
for m,t in mult:
    tkc=t['ticks']/t['contratos']
    bar='#'*max(1,round(m*14))
    print(f"  {t['fecha']}  {t['sym']:<4}{t['contratos']}c  {tkc:>6.0f} tk/ct  ${t['usd']:>8,.2f}  {m:>5.2f}R  {bar}")

low=[t for m,t in mult if m<1]
mid=[t for m,t in mult if 1<=m<1.75]
full=[t for m,t in mult if m>=1.75]
print(f"\n  ganadoras por debajo de 1R : {len(low):>2} de {len(W)}  aportan ${sum(t['usd'] for t in low):>8,.2f}")
print(f"  ganadoras entre 1R y 1.75R : {len(mid):>2} de {len(W)}  aportan ${sum(t['usd'] for t in mid):>8,.2f}")
print(f"  ganadoras de 1.75R o mas   : {len(full):>2} de {len(W)}  aportan ${sum(t['usd'] for t in full):>8,.2f}")

print(f"\n### El efecto sobre el resultado")
print(f"  Si las {len(low)+len(mid)} ganadoras cortas hubiesen llegado a 2R:")
extra=sum(2*RISK-t['usd'] for t in low+mid)
print(f"    ganancia adicional ${extra:,.2f}  ->  P&L pasaria de ${sum(t['usd'] for t in T):,.2f} a ${sum(t['usd'] for t in T)+extra:,.2f}")

print("\n### Dispersion del stop en ticks por contrato (¿cuanto variaba el stop?)")
for lbl,f in [('CL',lambda t:t['sym']=='CL'),('MCL',lambda t:t['sym']=='MCL')]:
    v=sorted(abs(t['ticks'])/t['contratos'] for t in L if f(t))
    if not v: continue
    print(f"  {lbl}: n={len(v)} min {v[0]:.0f} | p25 {v[len(v)//4]:.0f} | mediana {st.median(v):.0f} | p75 {v[3*len(v)//4]:.0f} | max {v[-1]:.0f}"
          f"   -> el mayor es {v[-1]/v[0]:.1f}x el menor")

print("\n### Riesgo en dolares por bucket de tamaño de stop (¿se normalizo bien?)")
def buck(t):
    s=abs(t['ticks'])/t['contratos']
    if s<=20: return 'a. stop <=20 tk'
    if s<=50: return 'b. stop 21-50 tk'
    if s<=80: return 'c. stop 51-80 tk'
    return 'd. stop >80 tk'
g=defaultdict(list)
for t in L: g[buck(t)].append(abs(t['usd']))
for k in sorted(g):
    print(f"  {k:<18} n={len(g[k]):>2}  riesgo medio ${st.mean(g[k]):>7,.2f}  (mediana ${st.median(g[k]):>7,.2f})")

print("\n### Y el rendimiento por ese mismo bucket")
g=defaultdict(list)
for t in T: g[buck(t)].append(t)
for k in sorted(g):
    v=g[k]; w=[x for x in v if x['usd']>0]
    print(f"  {k:<18} n={len(v):>2} WR={len(w)/len(v)*100:>5.1f}% P&L=${sum(x['usd'] for x in v):>9,.2f}")
