import connors_rsi2 as C
from datetime import time
from collections import defaultdict
UTC=C.UTC; BA=C.BA; NY=C.NY
# vela de referencia: 9:30-10:00 ET (apertura real USA, sigue DST). Entrada tras cierre (10:00 ET).
# salida por tiempo: 13:00 ART = 16:00 UTC fija.
DPP=5.0; COST=2.5
def et(dt): return dt.replace(tzinfo=UTC).astimezone(NY)
def utcmin(dt): return dt.hour*60+dt.minute
def run(rows, excl_wed=False):
    by=defaultdict(list)
    for i,r in enumerate(rows): by[et(r[0]).date()].append(i)
    trades=[]
    for day in sorted(by):
        idx=by[day]
        rhi=-1e18; rlo=1e18; haveref=False
        for i in idx:
            e=et(rows[i][0]); mm=e.hour*60+e.minute
            if 570<=mm<600:   # 9:30-10:00 ET
                haveref=True
                if rows[i][2]>rhi: rhi=rows[i][2]
                if rows[i][3]<rlo: rlo=rows[i][3]
        if not haveref or rhi<=rlo: continue
        if excl_wed and et(rows[idx[0]][0]).weekday()==2: continue
        pos=0; entry=0; exitpx=None
        for i in idx:
            e=et(rows[i][0]); mm=e.hour*60+e.minute
            if mm<600: continue                 # esperar cierre de la vela ref (10:00 ET)
            if utcmin(rows[i][0])>=960:          # 16:00 UTC = 13:00 ART: salida
                if pos!=0: exitpx=rows[i][4]
                break
            h=rows[i][2]; l=rows[i][3]; o=rows[i][1]
            if pos==0:
                hitU=h>=rhi; hitD=l<=rlo
                if hitU and hitD:
                    if abs(o-rhi)<=abs(o-rlo): pos=1; entry=rhi
                    else: pos=-1; entry=rlo
                elif hitU: pos=1; entry=rhi
                elif hitD: pos=-1; entry=rlo
            else:
                if pos==1 and l<=rlo: exitpx=rlo; break
                if pos==-1 and h>=rhi: exitpx=rhi; break
        if pos!=0 and exitpx is None: exitpx=rows[idx[-1]][4]
        if pos!=0:
            p=(exitpx-entry) if pos==1 else (entry-exitpx)
            trades.append((day,p,rhi-rlo))
    return trades
def rep(name,tr):
    if not tr: print(name+': 0'); return
    n=len(tr); net=sum(p*DPP for _,p,_ in tr)-n*COST
    ww=[p for _,p,_ in tr if p>0]; gw=sum(p*DPP for _,p,_ in tr if p>0); gl=-sum(p*DPP for _,p,_ in tr if p<=0)
    byy=defaultdict(list)
    for d,p,r in tr: byy[d.year].append(p)
    eq=0;pk=0;mdd=0; byday=defaultdict(float)
    for d,p,r in sorted(tr): v=p*DPP-COST; eq+=v;pk=max(pk,eq);mdd=min(mdd,eq-pk); byday[d]+=v
    pd=min(byday.values()); avgR=sum(r for _,_,r in tr)/n
    yr='  '.join(f'{y}:{len(byy[y])}op/${sum(x*DPP for x in byy[y])-len(byy[y])*COST:+.0f}' for y in sorted(byy))
    print(f'{name}: n={n} WR {100*len(ww)/n:.0f}% NETO ${net:+.0f} PF {gw/gl if gl else 9:.2f} DD ${mdd:+.0f} peorDia ${pd:+.0f} rangoMed {avgR:.1f}pt')
    print(f'      {yr}')
mes=C.load('/tmp/claude-0/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/scratchpad/data/MES_M1_continuo.csv')
print('=== ORB apertura USA 9:30 ET (MES continuo, PURA, ambos lados, miercoles incl., salida 13:00 ART) ===')
rep('  apertura USA', run(mes))
print()
print('  (comparacion: version anterior 10:30 ART fija = +$2.431)')
