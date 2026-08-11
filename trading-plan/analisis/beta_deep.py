import json, statistics as st
from collections import defaultdict, Counter
from datetime import datetime, date
T=json.load(open('beta.json'))
# ---- fecha corrupta
print("### Filas con fecha sospechosa")
for t in T:
    if not t['fecha'].startswith('202'): print('  ', t)

# ---- riesgo por operacion
print("\n### Riesgo real por operacion (perdedoras)")
L=[t for t in T if t['usd']<=0]
per=[abs(t['usd']) for t in L]
print(f"  perdida mediana ${st.median(per):,.2f} | media ${st.mean(per):,.2f} | max ${max(per):,.2f}")
big=[t for t in L if abs(t['usd'])>200]
print(f"  perdidas > $200: {len(big)} operaciones, total ${sum(t['usd'] for t in big):,.2f}")
print("  detalle de las perdidas grandes:")
for t in sorted(big,key=lambda x:x['usd'])[:20]:
    print(f"    {t['fecha']} {t['hora']} {t['sym']:<3} {t['contratos']}c {t['dir']} {t['patron']:<10} {t['ticks']:>5}tk  ${t['usd']:>9,.2f}  disc={t['disc']}")

# ---- 2% del capital seria
print("\n### Consistencia del riesgo (el plan dice 1-2%)")
for t in T:
    t['riesgo_pct']=abs(t['usd'])/ (t['acum']-t['usd']) *100 if t['usd']<0 else None
rp=[t['riesgo_pct'] for t in L if t['riesgo_pct']]
print(f"  perdida como % del capital: mediana {st.median(rp):.2f}%  media {st.mean(rp):.2f}%  max {max(rp):.2f}%")
print(f"  operaciones que perdieron mas del 2%: {len([x for x in rp if x>2])}")
print(f"  operaciones que perdieron mas del 3%: {len([x for x in rp if x>3])}")

# ---- hora relativa a apertura cash (DST USA)
DST=[(date(2025,3,9),date(2025,11,2)),(date(2026,3,8),date(2026,11,1))]
def ap(d):
    for a,b in DST:
        if a<=d<b: return 10
    return 11
def rel(t):
    d=datetime.strptime(t['fecha'],'%Y-%m-%d').date()
    h,m=map(int,t['hora'].split(':'))
    return h*60+m-ap(d)*60
print("\n### Minutos desde la apertura cash (ajustado por horario USA)")
def buck(t):
    r=rel(t)
    if r<0: return 'a. antes de apertura'
    if r<30: return 'b. 0-29 min'
    if r<60: return 'c. 30-59 min'
    if r<90: return 'd. 60-89 min'
    if r<120:return 'e. 90-119 min'
    return 'f. mas de 2h'
g=defaultdict(list)
for t in T: g[buck(t)].append(t)
for k in sorted(g):
    v=g[k]; w=[x for x in v if x['usd']>0]
    print(f"  {k:<22} n={len(v):>3} WR={len(w)/len(v)*100:>5.1f}% P&L=${sum(x['usd'] for x in v):>9,.2f}")

# ---- patron x direccion
print("\n### Set up x direccion")
g=defaultdict(list)
for t in T: g[(t['patron'],t['dir'])].append(t)
for k in sorted(g,key=lambda k:-sum(x['usd'] for x in g[k])):
    v=g[k]; w=[x for x in v if x['usd']>0]
    print(f"  {k[0]:<10} {k[1]:<2} n={len(v):>3} WR={len(w)/len(v)*100:>5.1f}% P&L=${sum(x['usd'] for x in v):>9,.2f}")

# ---- familia estructura vs giro
print("\n### Familia de set up")
for fam,f in [('ESTRUCTURA',lambda t:t['patron'].startswith('ESTRUC')),('GIRO',lambda t:t['patron'].startswith('Giro'))]:
    v=[t for t in T if f(t)]; w=[x for x in v if x['usd']>0]
    s=sum(x['usd'] for x in v)
    gp=sum(x['usd'] for x in v if x['usd']>0); gl=abs(sum(x['usd'] for x in v if x['usd']<=0))
    print(f"  {fam:<11} n={len(v):>3} WR={len(w)/len(v)*100:>5.1f}% P&L=${s:>9,.2f}  PF={gp/gl:.2f}")

# ---- que pasaria filtrando
print("\n### Simulacion de filtros sobre las mismas 97 operaciones")
def resumen(v,label):
    if not v: return
    w=[x for x in v if x['usd']>0]; s=sum(x['usd'] for x in v)
    gp=sum(x['usd'] for x in v if x['usd']>0); gl=abs(sum(x['usd'] for x in v if x['usd']<=0))
    R=(st.mean([x['usd'] for x in w])/abs(st.mean([x['usd'] for x in v if x['usd']<=0]))) if w and len(w)<len(v) else float('nan')
    print(f"  {label:<44} n={len(v):>3} WR={len(w)/len(v)*100:>5.1f}% P&L=${s:>9,.2f} PF={gp/gl:.2f} R={R:.2f}")
resumen(T,'SIN FILTROS (lo que pasó)')
resumen([t for t in T if t['patron']!='Giro+FV'],'sin Giro+FV')
resumen([t for t in T if not t['patron'].startswith('Giro')],'sin ningun Giro (solo ESTRUCTURA)')
resumen([t for t in T if t['dir']=='L'],'solo largos')
resumen([t for t in T if t['patron']!='Giro+FV' and t['dir']=='L'],'sin Giro+FV y solo largos')
resumen([t for t in T if not t['patron'].startswith('Giro') and t['dir']=='L'],'solo ESTRUCTURA y solo largos')
resumen([t for t in T if t['disc']=='SI'],'solo operaciones disciplinadas')
resumen([t for t in T if t['patron']!='Giro+FV' and t['disc']=='SI'],'sin Giro+FV y disciplinadas')
resumen([t for t in T if abs(t['usd'])<=250],'excluyendo las perdidas > $250')
resumen([t for t in T if t['sym']=='CL'],'solo CL')
resumen([t for t in T if t['patron']!='Giro+FV' and t['sym']=='CL'],'sin Giro+FV y solo CL')
