import json, statistics as st
from collections import defaultdict, Counter
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
mid=len(T)//2; H1,H2=T[:mid],T[mid:]
def resumen(H,lbl):
    W=[t['usd'] for t in H if t['usd']>0]; L=[t['usd'] for t in H if t['usd']<=0]
    R=st.mean(W)/abs(st.mean(L))
    print(f"  {lbl}")
    print(f"    n={len(H)}  WR={len(W)/len(H)*100:.1f}%  P&L=${sum(t['usd'] for t in H):>9,.2f}")
    print(f"    ganancia media ${st.mean(W):>8,.2f}  (mediana ${st.median(W):>8,.2f}, max ${max(W):>8,.2f})")
    print(f"    perdida  media ${st.mean(L):>8,.2f}  (mediana ${st.median(L):>8,.2f}, max ${min(L):>8,.2f})")
    print(f"    R = {R:.2f}   breakeven = {1/(1+R)*100:.1f}%")
    print(f"    contratos medios {st.mean([t['contratos'] for t in H]):.2f} | MCL {len([t for t in H if t['sym']=='MCL'])}/{len(H)}")
    print(f"    ticks medios ganadoras {st.mean([t['ticks'] for t in H if t['usd']>0]):>7.1f} | perdedoras {st.mean([t['ticks'] for t in H if t['usd']<=0]):>7.1f}")
print("### Qué cambió entre las dos mitades")
resumen(H1,f"1a MITAD  {H1[0]['fecha']} -> {H1[-1]['fecha']}")
resumen(H2,f"2a MITAD  {H2[0]['fecha']} -> {H2[-1]['fecha']}")

print("\n### Riesgo asumido por operación (pérdida en $ y como % del capital vivo)")
for lbl,H in [('1a mitad',H1),('2a mitad',H2)]:
    L=[t for t in H if t['usd']<=0]
    pct=[abs(t['usd'])/(t['acum']-t['usd'])*100 for t in L]
    print(f"  {lbl}: perdida mediana ${st.median([abs(t['usd']) for t in L]):>7,.2f}  = {st.median(pct):.2f}% del capital"
          f"   | >2%: {len([x for x in pct if x>2])}/{len(L)}")

print("\n### Evolución trimestral del tamaño de la pérdida típica")
g=defaultdict(list)
for t in T:
    if t['usd']<=0: g[t['fecha'][:7]].append(abs(t['usd']))
for k in sorted(g):
    print(f"  {k}: n={len(g[k]):>2} perdida mediana ${st.median(g[k]):>7,.2f}  media ${st.mean(g[k]):>7,.2f}")

print("\n### Ganadoras: ¿se están cortando?")
g=defaultdict(list)
for t in T:
    if t['usd']>0: g[t['fecha'][:7]].append(t['ticks'])
for k in sorted(g):
    print(f"  {k}: n={len(g[k]):>2} ticks mediana {st.median(g[k]):>6.0f}")

print("\n### Relación tamaño de posición vs resultado")
for c in [1,2,3]:
    v=[t for t in T if t['contratos']==c]
    if not v: continue
    W=[t['usd'] for t in v if t['usd']>0]; L=[t['usd'] for t in v if t['usd']<=0]
    print(f"  {c} contrato(s): n={len(v):>3} WR={len(W)/len(v)*100:>5.1f}% P&L=${sum(t['usd'] for t in v):>9,.2f}"
          f" | gan.media ${st.mean(W) if W else 0:>7,.2f} perd.media ${st.mean(L) if L else 0:>8,.2f}")

print("\n### Las 10 peores y las 10 mejores operaciones")
S=sorted(T,key=lambda t:t['usd'])
print("  PEORES:")
for t in S[:10]:
    print(f"    {t['fecha']} {t['hora']} {t['sym']:<3} {t['contratos']}c {t['dir']} {t['patron']:<10} {t['ticks']:>5}tk ${t['usd']:>9,.2f} disc={t['disc']}")
print("  MEJORES:")
for t in S[-10:][::-1]:
    print(f"    {t['fecha']} {t['hora']} {t['sym']:<3} {t['contratos']}c {t['dir']} {t['patron']:<10} {t['ticks']:>5}tk ${t['usd']:>9,.2f} disc={t['disc']}")

print("\n### Concentración: cuánto pesan las peores operaciones")
tot=sum(t['usd'] for t in T)
for k in [3,5,10]:
    print(f"  las {k} peores suman ${sum(t['usd'] for t in S[:k]):>9,.2f}  (P&L total ${tot:,.2f})")
