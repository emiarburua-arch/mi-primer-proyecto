import json, csv, io, re, math
from collections import Counter, defaultdict
from datetime import datetime, date

F={'BT':'/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453607816.txt',
   'R1':'/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453611346.txt',
   'R2':'/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453586271.txt'}
def money(s):
    s=s.replace('$','').replace(',','').strip()
    if not s: return None
    n=s.startswith('-'); s=s.lstrip('-')
    try: return (-1 if n else 1)*float(s)
    except: return None
def load(p):
    c=json.load(open(p))['fileContent']; i=[m.start() for m in re.finditer(r'Entrada de Datos ,',c)][-1]
    T=[]
    for r in c[i:c.find('Detalle por bloques',i)].split(' ,'):
        f=next(csv.reader(io.StringIO(r)))
        if len(f)>20 and f[2].strip() and re.match(r'\d{2}/\d{2}/\d{2}',f[3].strip() or ''):
            T.append(dict(sym=f[2].strip(),fecha=f[3],hora=f[4],dir=f[5],contr=f[6],patron=f[7],
                ticks=int(f[19]) if f[19].strip() else 0, neto=money(f[21])))
    return T
BT=load(F['BT']); R=load(F['R1'])+load(F['R2'])

# --- DST USA: apertura cash CL = 9:00 ET ; BA=UTC-3
DST=[(date(2024,3,10),date(2024,11,3)),(date(2025,3,9),date(2025,11,2))]
def apertura(d):
    for a,b in DST:
        if a<=d<b: return 10   # ET+1
    return 11                  # ET+2
def rel(t):
    d=datetime.strptime(t['fecha'],'%d/%m/%y').date()
    h,m=map(int,t['hora'].split(':'))
    return (h*60+m)-apertura(d)*60

def bucket(t):
    r=rel(t)
    if r<0: return 'ANTES de apertura'
    if r<60: return 'H1 (0-59 min)'
    if r<120:return 'H2 (60-119 min)'
    return 'FUERA de ventana (>2h)'
ORD=['ANTES de apertura','H1 (0-59 min)','H2 (60-119 min)','FUERA de ventana (>2h)']

for lbl,T in [('BACKTEST',BT),('REAL',R)]:
    print(f"\n### {lbl} — minutos desde apertura cash (ajustado por horario USA)")
    g=defaultdict(list)
    for t in T: g[bucket(t)].append(t['neto'])
    for k in ORD:
        if k in g:
            v=g[k]; w=len([x for x in v if x>0])
            print(f"  {k:<24} n={len(v):>3}  WR={w/len(v)*100:>5.1f}%  P&L=${sum(v):>9,.2f}  media=${sum(v)/len(v):>8,.2f}")

# --- simbolo en backtest
print("\n### BACKTEST por simbolo")
g=defaultdict(list)
for t in BT: g[t['sym']].append(t['neto'])
for k,v in g.items():
    print(f"  {k:<6} n={len(v):>3} WR={len([x for x in v if x>0])/len(v)*100:>5.1f}% P&L=${sum(v):>9,.2f}")

# --- test binomial: real vs winrate del backtest
def binom_cdf(k,n,p):
    return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k+1))
p=45/78; n=len(R); k=len([t for t in R if t['neto']>0])
print(f"\n### Test de significancia")
print(f"  Winrate backtest p={p*100:.1f}%  |  real: {k} ganadoras de {n}  (={k/n*100:.1f}%)")
print(f"  P(obtener <= {k} ganadoras en {n} ops si el sistema fuera realmente {p*100:.1f}%) = {binom_cdf(k,n,p)*100:.3f}%")
# intervalo de confianza wilson para el backtest
def wilson(k,n,z=1.96):
    ph=k/n; d=1+z*z/n
    c=(ph+z*z/(2*n))/d; e=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/d
    return c-e,c+e
lo,hi=wilson(45,78); print(f"  IC95% winrate backtest (n=78): {lo*100:.1f}% – {hi*100:.1f}%")
lo,hi=wilson(k,n);   print(f"  IC95% winrate real     (n={n}): {lo*100:.1f}% – {hi*100:.1f}%")
print(f"  Winrate de breakeven necesario (R=1.85 neto de comisiones): 35.1%")
print(f"  -> Los IC NO se solapan: la caida no se explica solo por azar." if hi<lo else "")

# --- cuantas ops necesito para saber si el sistema sirve
print(f"\n### Potencia estadistica: n necesario para distinguir 35% de 45% con 95% conf:")
for target in [0.40,0.45,0.50]:
    nn=math.ceil((1.96*math.sqrt(0.35*0.65)+1.28*math.sqrt(target*(1-target)))**2/(target-0.35)**2)
    print(f"   para detectar winrate real de {target*100:.0f}% vs breakeven 35%: ~{nn} operaciones")

# --- que pasaria con distintos ratios / stops en el REAL
print("\n### Simulacion sobre las 27 ops REALES: efecto de cambiar el target")
# real: 6 wins de 27. Todas las wins llegaron a +20. No tenemos MFE, asi que solo podemos
# evaluar el efecto del ratio suponiendo winrate constante (cota superior optimista)
for R_ratio,wr in [(1.85,0.222)]:
    pass
for tgt_ticks in [15,20,25,30,40]:
    # asumiendo que un target mas corto se alcanza mas seguido no es medible sin MFE -> mostramos breakeven
    be=(10+0.53)/((tgt_ticks-0.53)+(10+0.53))
    print(f"   target {tgt_ticks} ticks / stop 10 -> R neto={(tgt_ticks-0.53)/10.53:.2f}  winrate breakeven={be*100:.1f}%")
for stop,tgt in [(10,20),(15,30),(20,40),(10,30)]:
    be=(stop+0.53)/((tgt-0.53)+(stop+0.53))
    print(f"   stop {stop} / target {tgt} -> R neto={(tgt-0.53)/(stop+0.53):.2f}  winrate breakeven={be*100:.1f}%")

# --- coste de comisiones
print(f"\n### Peso de comisiones (CL 1 contrato, $5.32 round turn)")
tot_com=len(R)*5.32
print(f"  Real: {len(R)} ops x $5.32 = ${tot_com:.2f} de un P&L de ${sum(t['neto'] for t in R):,.2f} ({tot_com/abs(sum(t['neto'] for t in R))*100:.1f}% de la perdida)")

# --- secuencia cronologica real
print("\n### Secuencia real completa (orden cronologico)")
Rs=sorted(R,key=lambda t:(datetime.strptime(t['fecha'],'%d/%m/%y'),t['hora']))
eq=0
for t in Rs:
    eq+=t['neto']
    print(f"  {t['fecha']} {t['hora']} {t['dir'] or '?':<1} {t['patron']:<10} {t['ticks']:>4}tk  ${t['neto']:>8,.2f}  acum ${eq:>9,.2f}")
