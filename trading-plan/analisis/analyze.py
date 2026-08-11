import json, csv, io, re, statistics as st
from collections import Counter, defaultdict
from datetime import datetime

FILES = {
 'BACKTEST_CL (feb24-ene25)': '/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453607816.txt',
 'REAL TPP EA n01 (feb-mar25)': '/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453611346.txt',
 'REAL E2T 22-04 (abr-may25)': '/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453586271.txt',
}
def money(s):
    s=s.replace('$','').replace(',','').strip()
    if not s: return None
    neg = s.startswith('-')
    s=s.lstrip('-')
    try: return (-1 if neg else 1)*float(s)
    except: return None

def load(path):
    c = json.load(open(path))['fileContent']
    idxs=[m.start() for m in re.finditer(r'Entrada de Datos ,', c)]
    seg = c[idxs[-1]: c.find('Detalle por bloques', idxs[-1])]
    T=[]
    for r in seg.split(' ,'):
        f=next(csv.reader(io.StringIO(r)))
        if len(f)>20 and f[2].strip() and re.match(r'\d{2}/\d{2}/\d{2}', f[3].strip() or ''):
            T.append(dict(sym=f[2], fecha=f[3], hora=f[4], dir=f[5], contr=f[6], patron=f[7],
                          ticks=int(f[19]) if f[19].strip() else 0,
                          neto=money(f[21]), dur=int(f[18]) if f[18].strip() else None,
                          disc=f[16], motivo=f[17]))
    return T

DIAS=['Lun','Mar','Mie','Jue','Vie','Sab','Dom']
def stats(T, label):
    print('\n'+'='*78); print(label, f'— {len(T)} operaciones'); print('='*78)
    pnl=[t['neto'] for t in T]
    wins=[p for p in pnl if p>0]; losses=[p for p in pnl if p<=0]
    tot=sum(pnl)
    print(f"P&L neto total: ${tot:,.2f}   |  media/op: ${tot/len(T):,.2f}")
    print(f"Winrate: {len(wins)/len(T)*100:.1f}%  ({len(wins)}W / {len(losses)}L)")
    if wins: print(f"Ganancia media: ${st.mean(wins):,.2f}   max ${max(wins):,.2f}")
    if losses: print(f"Perdida media : ${st.mean(losses):,.2f}   max ${min(losses):,.2f}")
    gp=sum(wins); gl=abs(sum(losses))
    print(f"Profit factor: {gp/gl:.2f}" if gl else "PF: inf")
    if wins and losses:
        R = st.mean(wins)/abs(st.mean(losses))
        be = 1/(1+R)
        print(f"Ratio R real (gan.media/perd.media): {R:.2f}  -> winrate de breakeven: {be*100:.1f}%")
    # distribucion de ticks
    print("\nDistribucion de resultados (ticks):", dict(sorted(Counter(t['ticks'] for t in T).items())))
    # racha maxima
    mx=cur=0
    for p in pnl:
        cur = cur+1 if p<=0 else 0
        mx=max(mx,cur)
    print(f"Racha maxima de perdidas consecutivas: {mx}")
    # drawdown
    eq=0; peak=0; dd=0
    for p in pnl:
        eq+=p; peak=max(peak,eq); dd=min(dd, eq-peak)
    print(f"Max drawdown: ${dd:,.2f}")

    def group(keyfn, title, order=None):
        g=defaultdict(list)
        for t in T: g[keyfn(t)].append(t['neto'])
        print(f"\n--- Por {title} ---")
        keys = order if order else sorted(g, key=lambda k:-sum(g[k]))
        for k in keys:
            if k not in g: continue
            v=g[k]; w=len([x for x in v if x>0])
            print(f"  {str(k):<16} n={len(v):>3}  WR={w/len(v)*100:>5.1f}%  P&L=${sum(v):>9,.2f}  media=${sum(v)/len(v):>8,.2f}")
    group(lambda t:t['patron'],'PATRON')
    group(lambda t:t['dir'] or '?','DIRECCION (L=largo C=corto)')
    group(lambda t:t['hora'][:2]+':00','HORA de entrada')
    group(lambda t: DIAS[datetime.strptime(t['fecha'],'%d/%m/%y').weekday()],'DIA de la semana', DIAS)
    group(lambda t: datetime.strptime(t['fecha'],'%d/%m/%y').strftime('%Y-%m'),'MES',
          sorted({datetime.strptime(t['fecha'],'%d/%m/%y').strftime('%Y-%m') for t in T}))
    # nro de operaciones por dia
    perday=Counter(t['fecha'] for t in T)
    print(f"\nDias operados: {len(perday)}  |  ops/dia medio: {len(T)/len(perday):.2f}  |  max ops en un dia: {max(perday.values())}")
    seq=defaultdict(list)
    for t in T: seq[t['fecha']].append(t['neto'])
    for i in range(0, max(perday.values())):
        v=[d[i] for d in seq.values() if len(d)>i]
        if v: print(f"  Operacion #{i+1} del dia: n={len(v):>3}  WR={len([x for x in v if x>0])/len(v)*100:>5.1f}%  P&L=${sum(v):>9,.2f}")
    disc=Counter(t['disc'] for t in T)
    if any(k.strip() for k in disc):
        print("\n--- Disciplina ---", dict(disc))
        g=defaultdict(list)
        for t in T: g[t['disc'] or 'n/d'].append(t['neto'])
        for k,v in g.items(): print(f"  {k:<6} n={len(v):>3} P&L=${sum(v):>9,.2f}")
        mot=Counter(t['motivo'] for t in T if t['motivo'].strip())
        if mot: print("  Motivos indisciplina:", dict(mot))
    durs=[t['dur'] for t in T if t['dur'] is not None]
    if durs:
        print(f"\nDuracion media: {st.mean(durs):.1f} min | mediana {st.median(durs):.0f} | max {max(durs)}")
        gw=[t['dur'] for t in T if t['neto']>0]; gl2=[t['dur'] for t in T if t['neto']<=0]
        if gw: print(f"  ganadoras: media {st.mean(gw):.1f} min")
        if gl2: print(f"  perdedoras: media {st.mean(gl2):.1f} min")
    return T

ALL={}
for k,v in FILES.items():
    ALL[k]=stats(load(v), k)

real = ALL['REAL TPP EA n01 (feb-mar25)'] + ALL['REAL E2T 22-04 (abr-may25)']
stats(real, 'TODO EL REAL COMBINADO')
