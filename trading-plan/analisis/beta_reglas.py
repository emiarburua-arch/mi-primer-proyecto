import json, statistics as st
from collections import defaultdict, Counter
from datetime import datetime
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
print("### Cumplimiento de las reglas del plan\n")
# 1. max 2 ops por dia
pd=Counter(t['fecha'] for t in T)
viol=[d for d,c in pd.items() if c>2]
print(f"1) 'Máximo de operaciones por día: 2'  -> dias con 3 operaciones: {len(viol)} {sorted(viol)}")
# 2. max perdida semanal 500
wk=defaultdict(float)
for t in T:
    d=datetime.strptime(t['fecha'],'%Y-%m-%d'); wk[d.strftime('%G-W%V')]+=t['usd']
bad=sorted([(k,v) for k,v in wk.items() if v<-500], key=lambda x:x[1])
print(f"2) 'Máxima pérdida semanal: $500'  -> semanas que la superaron: {len(bad)} de {len(wk)}")
for k,v in bad: print(f"     {k}: ${v:,.2f}")
# 3. riesgo 1-2%
L=[t for t in T if t['usd']<=0]
over=[t for t in L if abs(t['usd'])/(t['acum']-t['usd'])>0.02]
print(f"3) 'Riesgo 1%-2%'  -> operaciones que perdieron mas del 2%: {len(over)} de {len(L)}")
for t in sorted(over,key=lambda x:x['usd'])[:6]:
    print(f"     {t['fecha']} {t['sym']} {t['contratos']}c  ${t['usd']:,.2f} = {abs(t['usd'])/(t['acum']-t['usd'])*100:.2f}%")
# 4. R de cada set up
print("\n### R por set up (¿el problema de Giro es el winrate o el R?)")
g=defaultdict(list)
for t in T: g[t['patron']].append(t)
print(f"  {'set up':<12} {'n':>3} {'WR':>7} {'R':>6} {'breakeven':>10} {'PF':>6} {'P&L':>10}")
for k in sorted(g,key=lambda k:-sum(x['usd'] for x in g[k])):
    v=g[k]; W=[x['usd'] for x in v if x['usd']>0]; Ls=[x['usd'] for x in v if x['usd']<=0]
    if not W: 
        print(f"  {k:<12} {len(v):>3} {0.0:>6.1f}%   (0 ganadoras)          {sum(x['usd'] for x in v):>10,.2f}")
        continue
    R=st.mean(W)/abs(st.mean(Ls))
    gp=sum(W); gl=abs(sum(Ls))
    print(f"  {k:<12} {len(v):>3} {len(W)/len(v)*100:>6.1f}% {R:>6.2f} {1/(1+R)*100:>9.1f}% {gp/gl:>6.2f} {sum(x['usd'] for x in v):>10,.2f}")
# 5. cuantas operaciones tenian R planificado < 2
print("\n### Reparto de operaciones por el ratio target/stop del esquema usado")
for lbl,f in [('CL 1 contrato (ratio ~2.0)',lambda t:t['sym']=='CL' and t['contratos']==1),
              ('MCL (ratio ~1.2)',lambda t:t['sym']=='MCL')]:
    v=[t for t in T if f(t)]
    print(f"  {lbl:<30} n={len(v):>3}  P&L=${sum(x['usd'] for x in v):>9,.2f}")
# 6. impacto acumulado de cada hallazgo
print("\n### Peso de cada problema sobre el resultado total (P&L real: $-1.549,52)")
items=[
 ('Operaciones en MCL / multi-contrato (R comprimido)', lambda t:t['sym']=='MCL'),
 ('Entradas en los primeros 30 min tras la apertura', lambda t: True),  # se calcula aparte
]
from datetime import date
DST=[(date(2025,3,9),date(2025,11,2)),(date(2026,3,8),date(2026,11,1))]
def ap(d):
    for a,b in DST:
        if a<=d<b: return 10
    return 11
def rel(t):
    d=datetime.strptime(t['fecha'],'%Y-%m-%d').date(); h,m=map(int,t['hora'].split(':'))
    return h*60+m-ap(d)*60
mcl=[t for t in T if t['sym']=='MCL']
p30=[t for t in T if 0<=rel(t)<30]
gfv=[t for t in T if t['patron']=='Giro+FV']
ind=[t for t in T if t['disc']=='NO']
print(f"  MCL / multi-contrato:        n={len(mcl):>3}  ${sum(t['usd'] for t in mcl):>9,.2f}")
print(f"  primeros 30 min:             n={len(p30):>3}  ${sum(t['usd'] for t in p30):>9,.2f}")
print(f"  set up Giro+FV:              n={len(gfv):>3}  ${sum(t['usd'] for t in gfv):>9,.2f}")
print(f"  operaciones indisciplinadas: n={len(ind):>3}  ${sum(t['usd'] for t in ind):>9,.2f}")
union=[t for t in T if t['sym']=='MCL' or 0<=rel(t)<30 or t['patron']=='Giro+FV']
print(f"  union de los tres primeros:  n={len(union):>3}  ${sum(t['usd'] for t in union):>9,.2f}")
resto=[t for t in T if t not in union]
W=[x['usd'] for x in resto if x['usd']>0]; Ls=[x['usd'] for x in resto if x['usd']<=0]
print(f"  LO QUE QUEDA:                n={len(resto):>3}  ${sum(t['usd'] for t in resto):>9,.2f}"
      f"  WR={len(W)/len(resto)*100:.1f}%  R={st.mean(W)/abs(st.mean(Ls)):.2f}  PF={sum(W)/abs(sum(Ls)):.2f}")
