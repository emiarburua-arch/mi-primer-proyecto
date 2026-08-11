import json, math, statistics as st
from collections import defaultdict
from datetime import datetime, date
T=json.load(open('beta.json'))
T=[t for t in T if t['fecha'].startswith('202')]      # descarta la fila con fecha corrupta
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
DST=[(date(2025,3,9),date(2025,11,2)),(date(2026,3,8),date(2026,11,1))]
def ap(d):
    for a,b in DST:
        if a<=d<b: return 10
    return 11
def rel(t):
    d=datetime.strptime(t['fecha'],'%Y-%m-%d').date(); h,m=map(int,t['hora'].split(':'))
    return h*60+m-ap(d)*60
for t in T: t['rel']=rel(t)

def fisher(a,b,c,d):
    # tabla 2x2: [[a,b],[c,d]] -> p de dos colas
    def lf(n): return math.lgamma(n+1)
    n=a+b+c+d
    def p(a2,b2,c2,d2):
        return math.exp(lf(a2+b2)+lf(c2+d2)+lf(a2+c2)+lf(b2+d2)-lf(n)-lf(a2)-lf(b2)-lf(c2)-lf(d2))
    p0=p(a,b,c,d); tot=0
    for i in range(0,min(a+b,a+c)+1):
        j=a+b-i; k=a+c-i; l=d-(a-i)
        if j<0 or k<0 or l<0: continue
        pi=p(i,j,k,l)
        if pi<=p0*1.000001: tot+=pi
    return min(tot,1.0)

def split(name,f):
    A=[t for t in T if f(t)]; B=[t for t in T if not f(t)]
    aw=len([x for x in A if x['usd']>0]); al=len(A)-aw
    bw=len([x for x in B if x['usd']>0]); bl=len(B)-bw
    p=fisher(aw,al,bw,bl)
    print(f"  {name:<34} grupo n={len(A):>3} WR={aw/len(A)*100:>5.1f}% ${sum(x['usd'] for x in A):>9,.2f}"
          f" | resto n={len(B):>3} WR={bw/len(B)*100:>5.1f}%   p={p:.4f} {'*SIGNIFICATIVO*' if p<0.05 else ''}")

print("### Tests de significancia (Fisher exacto, dos colas) sobre el winrate")
split('familia GIRO', lambda t:t['patron'].startswith('Giro'))
split('Giro+FV', lambda t:t['patron']=='Giro+FV')
split('primeros 30 min tras apertura', lambda t:0<=t['rel']<30)
split('mas de 2h tras apertura', lambda t:t['rel']>=120)
split('operaciones en corto', lambda t:t['dir']=='C')
split('instrumento MCL', lambda t:t['sym']=='MCL')
split('lunes', lambda t:datetime.strptime(t['fecha'],'%Y-%m-%d').weekday()==0)
split('con parciales', lambda t:t['l2'] is not None)

print("\n### Estabilidad temporal: primera mitad vs segunda mitad")
mid=len(T)//2
H1,H2=T[:mid],T[mid:]
print(f"  1a mitad ({H1[0]['fecha']} a {H1[-1]['fecha']}): n={len(H1)} WR={len([x for x in H1 if x['usd']>0])/len(H1)*100:.1f}% P&L=${sum(x['usd'] for x in H1):,.2f}")
print(f"  2a mitad ({H2[0]['fecha']} a {H2[-1]['fecha']}): n={len(H2)} WR={len([x for x in H2 if x['usd']>0])/len(H2)*100:.1f}% P&L=${sum(x['usd'] for x in H2):,.2f}")

def probe(name,f):
    r=[]
    for lbl,H in [('1a',H1),('2a',H2)]:
        A=[t for t in H if f(t)]
        if A: r.append(f"{lbl}: n={len(A):>2} WR={len([x for x in A if x['usd']>0])/len(A)*100:>5.1f}% ${sum(x['usd'] for x in A):>8,.2f}")
        else: r.append(f"{lbl}: n= 0")
    print(f"  {name:<30} " + "  |  ".join(r))
print("\n  ¿Los cortes se sostienen en las dos mitades?")
probe('familia ESTRUCTURA', lambda t:t['patron'].startswith('ESTRUC'))
probe('familia GIRO', lambda t:t['patron'].startswith('Giro'))
probe('primeros 30 min', lambda t:0<=t['rel']<30)
probe('pasados 60 min', lambda t:t['rel']>=60)
probe('largos', lambda t:t['dir']=='L')
probe('cortos', lambda t:t['dir']=='C')

print("\n### Validacion temporal honesta: regla derivada de la 1a mitad, aplicada a la 2a")
# regla candidata: solo ESTRUCTURA y no entrar en los primeros 30 min
def regla(t): return t['patron'].startswith('ESTRUC') and t['rel']>=30
for lbl,H in [('1a mitad (donde se derivo)',H1),('2a mitad (fuera de muestra)',H2)]:
    A=[t for t in H if regla(t)]
    if A:
        w=len([x for x in A if x['usd']>0]); s=sum(x['usd'] for x in A)
        gp=sum(x['usd'] for x in A if x['usd']>0); gl=abs(sum(x['usd'] for x in A if x['usd']<=0))
        print(f"  {lbl:<30} n={len(A):>3} WR={w/len(A)*100:>5.1f}% P&L=${s:>9,.2f} PF={gp/gl:.2f}")

print("\n### Curva mensual de la regla candidata vs lo que paso")
g=defaultdict(lambda:[0,0])
for t in T:
    g[t['fecha'][:7]][0]+=t['usd']
    if regla(t): g[t['fecha'][:7]][1]+=t['usd']
print(f"  {'mes':<10} {'real':>11} {'con regla':>11}")
ca=cb=0
for k in sorted(g):
    ca+=g[k][0]; cb+=g[k][1]
    print(f"  {k:<10} {g[k][0]:>11,.2f} {g[k][1]:>11,.2f}")
print(f"  {'TOTAL':<10} {ca:>11,.2f} {cb:>11,.2f}")

print("\n### Cuanto falta para el breakeven")
W=[t['usd'] for t in T if t['usd']>0]; L=[t['usd'] for t in T if t['usd']<=0]
R=st.mean(W)/abs(st.mean(L))
print(f"  R actual {R:.2f} -> breakeven {1/(1+R)*100:.1f}% | winrate actual {len(W)/len(T)*100:.1f}%")
print(f"  faltan {1/(1+R)*100-len(W)/len(T)*100:.1f} puntos de winrate")
wr=len(W)/len(T)
print(f"  ...o subir el R de {R:.2f} a {(1-wr)/wr:.2f} manteniendo el winrate ({((1-wr)/wr/R-1)*100:.0f}% mas de recorrido medio por ganadora)")
