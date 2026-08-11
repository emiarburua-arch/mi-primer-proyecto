import json, statistics as st
from datetime import datetime, date
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
DST=[(date(2025,3,9),date(2025,11,2)),(date(2026,3,8),date(2026,11,1))]
def ap(d):
    for a,b in DST:
        if a<=d<b: return 10
    return 11
def rel(t):
    d=datetime.strptime(t['fecha'],'%Y-%m-%d').date(); h,m=map(int,t['hora'].split(':'))
    return h*60+m-ap(d)*60
def stats(v,lbl):
    if not v: return print(f"  {lbl:<46} n=0")
    W=[x['usd'] for x in v if x['usd']>0]; L=[x['usd'] for x in v if x['usd']<=0]
    if not W or not L: return print(f"  {lbl:<46} n={len(v)} (un solo lado) ${sum(x['usd'] for x in v):,.2f}")
    R=st.mean(W)/abs(st.mean(L))
    print(f"  {lbl:<46} n={len(v):>3} WR={len(W)/len(v)*100:>5.1f}% R={R:>4.2f} be={1/(1+R)*100:>5.1f}% PF={sum(W)/abs(sum(L)):>4.2f} ${sum(x['usd'] for x in v):>9,.2f}")

print("### Efecto de cada corrección por separado, sobre las 96 operaciones")
stats(T,'sin cambios (lo que pasó)')
stats([t for t in T if not(t['sym']=='MCL')],'C1 · solo esquemas con R>=2 (CL 1 contrato)')
stats([t for t in T if rel(t)>=30],'C2 · sin entradas en los primeros 30 min')
stats([t for t in T if t['patron']!='Giro+FV'],'C3 · sin Giro+FV')
stats([t for t in T if not t['patron'].startswith('Giro')],'C3b · sin ningun Giro')
print()
stats([t for t in T if t['sym']!='MCL' and rel(t)>=30],'C1+C2')
stats([t for t in T if t['sym']!='MCL' and rel(t)>=30 and t['patron']!='Giro+FV'],'C1+C2+C3')
stats([t for t in T if t['sym']!='MCL' and rel(t)>=30 and not t['patron'].startswith('Giro')],'C1+C2+C3b')

print("\n### VALIDACION FUERA DE MUESTRA (reglas fijadas con la 1a mitad, medidas en la 2a)")
mid=len(T)//2; H1,H2=T[:mid],T[mid:]
def regla(t): return t['sym']!='MCL' and rel(t)>=30 and t['patron']!='Giro+FV'
print(f"  1a mitad {H1[0]['fecha']} -> {H1[-1]['fecha']}")
stats(H1,'    sin filtrar'); stats([t for t in H1 if regla(t)],'    con C1+C2+C3 (in-sample)')
print(f"  2a mitad {H2[0]['fecha']} -> {H2[-1]['fecha']}")
stats(H2,'    sin filtrar'); stats([t for t in H2 if regla(t)],'    con C1+C2+C3 (FUERA DE MUESTRA)')

print("\n### Cuantas operaciones quedan por mes aplicando C1+C2+C3")
from collections import defaultdict
g=defaultdict(lambda:[0,0,0.0,0.0])
for t in T:
    k=t['fecha'][:7]; g[k][0]+=1; g[k][2]+=t['usd']
    if regla(t): g[k][1]+=1; g[k][3]+=t['usd']
print(f"  {'mes':<9} {'ops':>4} {'quedan':>7} {'real':>10} {'filtrado':>10}")
a=b=0
for k in sorted(g):
    a+=g[k][2]; b+=g[k][3]
    print(f"  {k:<9} {g[k][0]:>4} {g[k][1]:>7} {g[k][2]:>10,.2f} {g[k][3]:>10,.2f}")
print(f"  {'TOTAL':<9} {sum(x[0] for x in g.values()):>4} {sum(x[1] for x in g.values()):>7} {a:>10,.2f} {b:>10,.2f}")

print("\n### Esperanza teórica según winrate y R (riesgo $155 por operación)")
print(f"  {'R':>5} " + ''.join(f"{w:>9.0%}" for w in [0.33,0.36,0.40,0.45]))
for R in [1.10,1.51,1.75,2.00,2.25]:
    row=f"  {R:>5.2f} "
    for w in [0.33,0.36,0.40,0.45]:
        e=w*155*R-(1-w)*155
        row+=f"{e:>9,.0f}"
    print(row + f"   (breakeven {1/(1+R)*100:.0f}%)")
