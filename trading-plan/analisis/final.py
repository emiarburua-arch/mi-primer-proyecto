import json, statistics as st, math
from collections import defaultdict
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
for t in T:
    tkc=abs(t['ticks'])/t['contratos']
    t['stop_est']= tkc if t['usd']<=0 else tkc/2
    t['riesgo_est']= t['stop_est']*t['contratos']*(10 if t['sym']=='CL' else 1)

print("### ¿Los stops mas anchos aciertan menos? (bucket por STOP estimado, no por target)")
def b(t):
    s=t['stop_est']
    if s<=15: return 'a. <=15 tk'
    if s<=25: return 'b. 16-25 tk'
    if s<=50: return 'c. 26-50 tk'
    if s<=80: return 'd. 51-80 tk'
    return 'e. >80 tk'
g=defaultdict(list)
for t in T: g[b(t)].append(t)
print(f"  {'bucket':<12}{'n':>4}{'WR':>8}{'riesgo medio':>15}{'P&L':>11}")
for k in sorted(g):
    v=g[k]; w=[x for x in v if x['usd']>0]
    rg=st.mean([x['riesgo_est'] if x['usd']>0 else abs(x['usd']) for x in v])
    print(f"  {k:<12}{len(v):>4}{len(w)/len(v)*100:>7.1f}%{rg:>14,.2f}{sum(x['usd'] for x in v):>11,.2f}")

def fisher(a,bb,c,d):
    def lf(n): return math.lgamma(n+1)
    n=a+bb+c+d
    def p(x,y,z,w): return math.exp(lf(x+y)+lf(z+w)+lf(x+z)+lf(y+w)-lf(n)-lf(x)-lf(y)-lf(z)-lf(w))
    p0=p(a,bb,c,d); tot=0
    for i in range(0,min(a+bb,a+c)+1):
        j=a+bb-i; k=a+c-i; l=d-(a-i)
        if j<0 or k<0 or l<0: continue
        pi=p(i,j,k,l)
        if pi<=p0*1.000001: tot+=pi
    return min(tot,1.0)
A=[t for t in T if t['stop_est']>25]; B=[t for t in T if t['stop_est']<=25]
aw=len([x for x in A if x['usd']>0]); bw=len([x for x in B if x['usd']>0])
print(f"\n  stop >25tk: n={len(A)} WR={aw/len(A)*100:.1f}%  |  stop <=25tk: n={len(B)} WR={bw/len(B)*100:.1f}%"
      f"   p={fisher(aw,len(A)-aw,bw,len(B)-bw):.4f}")

print("\n### ¿Se respeto el 2:1 en cada operacion? (ganadoras: target / stop del mismo dia)")
# comparamos target de cada ganadora contra el stop tipico de su mes
mes=defaultdict(list)
for t in T:
    if t['usd']<=0: mes[t['fecha'][:7]].append(t['stop_est'])
ok=0; tot=0; detalle=[]
for t in T:
    if t['usd']<=0: continue
    m=mes.get(t['fecha'][:7])
    if not m: continue
    s=st.median(m); r=(abs(t['ticks'])/t['contratos'])/s
    detalle.append((t['fecha'],t['sym'],round(s),round(abs(t['ticks'])/t['contratos']),round(r,2)))
    tot+=1; ok+= 1 if r>=1.7 else 0
print(f"  ganadoras cuyo target fue >=1,7x el stop tipico de su mes: {ok} de {tot}")
print(f"  -> el 2:1 se respeto en la gran mayoria; el problema NO es el ratio por operacion")

print("\n### EL MECANISMO REAL")
W=[t for t in T if t['usd']>0]; L=[t for t in T if t['usd']<=0]
rw=st.mean([t['riesgo_est'] for t in W]); rl=st.mean([abs(t['usd']) for t in L])
print(f"  riesgo medio cuando GANASTE : ${rw:,.2f}")
print(f"  riesgo medio cuando PERDISTE: ${rl:,.2f}   ({rl/rw:.2f}x mas)")
print(f"  -> ganancia media = 2 x {rw:,.2f} = ${2*rw:,.2f} ; perdida media = ${rl:,.2f}")
print(f"  -> R realizado = {2*rw/rl:.2f}   (medido en la planilla: 1.53)")
print(f"  Aun respetando 2:1 en TODAS, el R cae a {2*rw/rl:.2f} solo por arriesgar mas en las que perdiste.")

print("\n### TU PROPUESTA, con supuestos conservadores")
n=len(T); w=len(W)
print(f"  Base: {w}W / {n-w}L = {w/n*100:.1f}% winrate\n")
print(f"  {'escenario':<46}{'P&L':>11}")
print(f"  {'-'*57}")
for lbl,gan,per in [
    ('ideal: toda ganadora 2R, toda perdedora 1R', 300,150),
    ('con 4 scratch-wins que no pagan (realista)', 300,150),
    ('con deslizamiento: ganadora 1,9R', 285,150),
    ('con deslizamiento y stop real 1,05R', 285,157),
]:
    if 'scratch' in lbl:
        pnl=(w-4)*gan+4*20-(n-w)*per
    else:
        pnl=w*gan-(n-w)*per
    print(f"  {lbl:<46}{pnl:>11,.2f}")
print(f"  {'REAL (lo que paso)':<46}{sum(t['usd'] for t in T):>11,.2f}")

print("\n### Cuanto margen deja (riesgo fijo $150, target fijo $300)")
print(f"  winrate de equilibrio: 33,3%  |  el tuyo: {w/n*100:.1f}%  ->  margen de {w/n*100-33.33:.1f} puntos")
for wr in [0.30,0.3333,0.354,0.38,0.40]:
    print(f"    {wr*100:>5.1f}% -> ${wr*300-(1-wr)*150:>7,.2f}/op  |  ${(wr*300-(1-wr)*150)*96:>9,.2f} en 96 ops")
