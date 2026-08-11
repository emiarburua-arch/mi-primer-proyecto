import json, statistics as st, math
from collections import Counter, defaultdict
from datetime import datetime
T=json.load(open('beta.json'))
DIAS=['Lun','Mar','Mie','Jue','Vie','Sab','Dom']
def wd(t): return DIAS[datetime.strptime(t['fecha'],'%Y-%m-%d').weekday()]
pnl=[t['usd'] for t in T]
W=[t for t in T if t['usd']>0]; L=[t for t in T if t['usd']<=0]
tot=sum(pnl)
print('='*76)
print(f"97 OPERACIONES REALES · CL Beta plan 30d · 22-10-2025 → 26-06-2026")
print('='*76)
print(f"Capital 10.000 → {T[-1]['acum']:,.2f}   P&L neto ${tot:,.2f}  ({tot/10000*100:.2f}%)")
print(f"Winrate {len(W)/len(T)*100:.1f}%  ({len(W)}W / {len(L)}L)")
print(f"Ganancia media ${st.mean([t['usd'] for t in W]):,.2f}  |  Perdida media ${st.mean([t['usd'] for t in L]):,.2f}")
gp=sum(t['usd'] for t in W); gl=abs(sum(t['usd'] for t in L))
print(f"Profit factor {gp/gl:.3f}   (bruto ganado ${gp:,.2f} / perdido ${gl:,.2f})")
R=st.mean([t['usd'] for t in W])/abs(st.mean([t['usd'] for t in L]))
print(f"R real = {R:.2f}  ->  winrate de breakeven = {1/(1+R)*100:.1f}%")
print(f"Esperanza por operacion: ${tot/len(T):,.2f}")
# drawdown
eq=0;pk=0;dd=0;ddi=0
for i,t in enumerate(T):
    eq+=t['usd']; pk=max(pk,eq)
    if eq-pk<dd: dd=eq-pk; ddi=i+1
print(f"Max drawdown ${dd:,.2f} (op #{ddi})")
mx=cur=0
for t in T:
    cur=cur+1 if t['usd']<=0 else 0; mx=max(mx,cur)
print(f"Racha maxima de perdedoras: {mx}")
print(f"Comisiones totales estimadas: ${sum((5.32 if t['sym']=='CL' else 1.84)*t['contratos'] for t in T):,.2f}")

def grp(f,title,order=None,extra=None):
    g=defaultdict(list)
    for t in T: g[f(t)].append(t)
    print(f"\n--- {title} ---")
    ks=order if order else sorted(g,key=lambda k:-sum(x['usd'] for x in g[k]))
    for k in ks:
        if k not in g: continue
        v=g[k]; w=[x for x in v if x['usd']>0]; s=sum(x['usd'] for x in v)
        print(f"  {str(k):<18} n={len(v):>3}  WR={len(w)/len(v)*100:>5.1f}%  P&L=${s:>9,.2f}  media=${s/len(v):>7,.2f}")
grp(lambda t:t['patron'],'PATRON / SET UP')
grp(lambda t:t['sym'],'INSTRUMENTO')
grp(lambda t:t['dir'],'DIRECCION (L=largo, C=corto)')
grp(lambda t:t['contratos'],'CONTRATOS',order=[1,2,3,4,5])
grp(lambda t:t['hora'][:2]+':00' if t['hora'] else '?','HORA')
grp(wd,'DIA DE LA SEMANA',order=DIAS)
grp(lambda t:t['fecha'][:7],'MES',order=sorted({t['fecha'][:7] for t in T}))
grp(lambda t:'con parciales' if t['l2'] is not None else 'lote unico','GESTION DE SALIDA')
grp(lambda t:t['disc'] or 'n/d','DISCIPLINA')
mot=Counter(t['motivo'] for t in T if t['motivo'])
print('\n  Motivos de indisciplina:', dict(mot))
# ops por dia
pd=Counter(t['fecha'] for t in T)
print(f"\nDias operados: {len(pd)}  ops/dia {len(T)/len(pd):.2f}  max {max(pd.values())}")
seq=defaultdict(list)
for t in T: seq[t['fecha']].append(t)
for i in range(max(pd.values())):
    v=[d[i] for d in seq.values() if len(d)>i]
    w=[x for x in v if x['usd']>0]
    print(f"  Op #{i+1} del dia: n={len(v):>3} WR={len(w)/len(v)*100:>5.1f}% P&L=${sum(x['usd'] for x in v):>9,.2f}")
print(f"\nDistribucion de ticks: {dict(sorted(Counter(t['ticks'] for t in T).items()))}")
