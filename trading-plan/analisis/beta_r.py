import json, statistics as st
from collections import defaultdict
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
# ticks POR CONTRATO (la columna U es el total sumando contratos)
for t in T:
    t['tk_c']=t['ticks']/t['contratos']
print("### Stop y target en ticks POR CONTRATO (= centavos de movimiento del crudo)")
for lbl,f in [('CL',lambda t:t['sym']=='CL'),('MCL',lambda t:t['sym']=='MCL')]:
    v=[t for t in T if f(t)]
    L=[abs(t['tk_c']) for t in v if t['usd']<=0]; W=[t['tk_c'] for t in v if t['usd']>0]
    print(f"  {lbl:<4} n={len(v):>3}  stop mediano {st.median(L):>6.1f} tk  |  target mediano {st.median(W):>6.1f} tk"
          f"  ->  ratio {st.median(W)/st.median(L):.2f}")
print("\n### Evolución mensual del stop por contrato (proxy de la volatilidad asumida)")
g=defaultdict(list); gw=defaultdict(list)
for t in T:
    (g if t['usd']<=0 else gw)[t['fecha'][:7]].append(abs(t['tk_c']))
for k in sorted(set(g)|set(gw)):
    s=st.median(g[k]) if g[k] else float('nan')
    w=st.median(gw[k]) if gw[k] else float('nan')
    inst='/'.join(sorted({t['sym'] for t in T if t['fecha'][:7]==k}))
    print(f"  {k}  stop {s:>6.1f} tk | target {w:>6.1f} tk | ratio {w/s if s==s and w==w else float('nan'):>5.2f}  [{inst}]")

print("\n### Resultado agrupado por el ratio target/stop planificado")
# estimamos el R planificado de cada operacion: para perdedoras = stop; buscamos el target tipico del mes
# forma robusta: agrupamos por tamaño del stop por contrato
def bucket(t):
    s=abs(t['tk_c'])
    if t['usd']>0: return None
    if s<=15: return 'a. stop <=15 tk'
    if s<=25: return 'b. stop 16-25 tk'
    if s<=60: return 'c. stop 26-60 tk'
    return 'd. stop >60 tk'
# mejor: separar por instrumento+contratos, que define el esquema
print("\n### Esquema de operación (instrumento x contratos): el R que produce cada uno")
g=defaultdict(list)
for t in T: g[(t['sym'],t['contratos'])].append(t)
print(f"  {'esquema':<12} {'n':>3} {'WR':>7} {'gan.med':>9} {'perd.med':>10} {'R':>6} {'breakeven':>10} {'P&L':>10}")
for k in sorted(g,key=lambda k:(k[0],k[1])):
    v=g[k]; W=[x['usd'] for x in v if x['usd']>0]; L=[x['usd'] for x in v if x['usd']<=0]
    if not W or not L: 
        print(f"  {k[0]+' '+str(k[1])+'c':<12} {len(v):>3}   (sin ambos lados)  P&L=${sum(x['usd'] for x in v):>9,.2f}")
        continue
    R=st.mean(W)/abs(st.mean(L))
    print(f"  {k[0]+' '+str(k[1])+'c':<12} {len(v):>3} {len(W)/len(v)*100:>6.1f}% {st.mean(W):>9,.2f} {st.mean(L):>10,.2f} {R:>6.2f} {1/(1+R)*100:>9.1f}% {sum(x['usd'] for x in v):>10,.2f}")

print("\n### Contraste directo: CL 1 contrato vs todo lo demás")
A=[t for t in T if t['sym']=='CL' and t['contratos']==1]
B=[t for t in T if not (t['sym']=='CL' and t['contratos']==1)]
for lbl,v in [('CL 1 contrato',A),('resto (MCL / multi-contrato)',B)]:
    W=[x['usd'] for x in v if x['usd']>0]; L=[x['usd'] for x in v if x['usd']<=0]
    R=st.mean(W)/abs(st.mean(L))
    gp=sum(W); gl=abs(sum(L))
    print(f"  {lbl:<28} n={len(v):>3} WR={len(W)/len(v)*100:>5.1f}% R={R:.2f} breakeven={1/(1+R)*100:>5.1f}% PF={gp/gl:.2f} P&L=${sum(x['usd'] for x in v):>9,.2f}")

print("\n### ¿Y si en la 2a mitad hubiese seguido con CL 1 contrato y R=2.04?")
H2=T[len(T)//2:]
wr=len([t for t in H2 if t['usd']>0])/len(H2)
riesgo=155.32
print(f"  winrate real de la 2a mitad: {wr*100:.1f}%  ({len(H2)} operaciones)")
for R in [1.10,1.50,2.04]:
    e=wr*riesgo*R-(1-wr)*riesgo
    print(f"    con R={R:.2f}: esperanza ${e:>7,.2f}/op  ->  ${e*len(H2):>9,.2f} en 48 operaciones")
