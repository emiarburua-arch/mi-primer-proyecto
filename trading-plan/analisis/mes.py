import json,csv,io,re
from collections import defaultdict,Counter
p='/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453844853.txt'
def money(s):
    s=s.replace('$','').replace(',','').strip()
    if not s: return None
    n=s.startswith('-'); s=s.lstrip('-')
    try: return (-1 if n else 1)*float(s)
    except: return None
c=json.load(open(p))['fileContent']
i=[m.start() for m in re.finditer(r'Entrada de Datos ,',c)][-1]
T=[]
for r in c[i:c.find('Detalle por bloques',i)].split(' ,'):
    f=next(csv.reader(io.StringIO(r)))
    if len(f)>20 and f[2].strip() and re.match(r'\d{2}/\d{2}/\d{2}',f[3].strip() or ''):
        T.append(dict(sym=f[2].strip(),fecha=f[3],hora=f[4],dir=f[5],contr=f[6],patron=f[7],
            ticks=int(f[19]) if f[19].strip() else 0, neto=money(f[21])))
print('MES BACKTEST — ops:',len(T))
if T:
    pnl=[t['neto'] for t in T]; w=[x for x in pnl if x>0]; l=[x for x in pnl if x<=0]
    print(f"P&L ${sum(pnl):,.2f} | WR {len(w)/len(T)*100:.1f}% ({len(w)}/{len(T)}) | PF {sum(w)/abs(sum(l)):.2f}")
    print(f"gan media ${sum(w)/len(w):,.2f} | perd media ${sum(l)/len(l):,.2f}")
    print('ticks:',dict(sorted(Counter(t['ticks'] for t in T).items())))
    print('rango fechas:',T[0]['fecha'],'->',T[-1]['fecha'])
    g=defaultdict(list)
    for t in T: g[t['patron']].append(t['neto'])
    for k,v in sorted(g.items(),key=lambda x:-sum(x[1])):
        print(f"  {k:<12} n={len(v):>3} WR={len([x for x in v if x>0])/len(v)*100:>5.1f}% P&L=${sum(v):>9,.2f}")
    dd=0;eq=0;pk=0
    for x in pnl:
        eq+=x;pk=max(pk,eq);dd=min(dd,eq-pk)
    print(f"max DD ${dd:,.2f}")
