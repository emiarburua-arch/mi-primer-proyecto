import connors_rsi2 as C
from collections import defaultdict
UTC=C.UTC; NY=C.NY
DPP=5.0; COST=2.5
def et(dt): return dt.replace(tzinfo=UTC).astimezone(NY)
def utcmin(dt): return dt.hour*60+dt.minute
def run(rows, trail=None):
    """trail = distancia en PUNTOS. None = sin trailing (mantener hasta 13:00 con stop en extremo)."""
    by=defaultdict(list)
    for i,r in enumerate(rows): by[et(r[0]).date()].append(i)
    trades=[]
    for day in sorted(by):
        idx=by[day]
        rhi=-1e18; rlo=1e18; haveref=False
        for i in idx:
            e=et(rows[i][0]); mm=e.hour*60+e.minute
            if 570<=mm<600:
                haveref=True
                if rows[i][2]>rhi: rhi=rows[i][2]
                if rows[i][3]<rlo: rlo=rows[i][3]
        if not haveref or rhi<=rlo: continue
        pos=0; entry=0; exitpx=None; stop=0; maxfav=0
        for i in idx:
            e=et(rows[i][0]); mm=e.hour*60+e.minute
            if mm<600: continue
            if utcmin(rows[i][0])>=960:
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
                if pos==1: stop=rlo; maxfav=entry
                elif pos==-1: stop=rhi; maxfav=entry
            else:
                # 1) chequear stop con valor previo
                if pos==1 and l<=stop: exitpx=stop; break
                if pos==-1 and h>=stop: exitpx=stop; break
                # 2) extender trailing
                if trail is not None:
                    if pos==1:
                        if h>maxfav: maxfav=h
                        if maxfav>=entry+trail: stop=max(stop, maxfav-trail)
                    else:
                        if l<maxfav: maxfav=l
                        if maxfav<=entry-trail: stop=min(stop, maxfav+trail)
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
    pd=min(byday.values())
    yr='  '.join(f'{y}:${sum(x*DPP for x in byy[y])-len(byy[y])*COST:+.0f}' for y in sorted(byy))
    print(f'{name}: n={n} WR {100*len(ww)/n:.0f}% NETO ${net:+.0f} PF {gw/gl if gl else 9:.2f} DD ${mdd:+.0f} peorDia ${pd:+.0f}')
    print(f'      {yr}')
mes=C.load('/tmp/claude-0/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/scratchpad/data/MES_M1_continuo.csv')
print('=== ORB apertura USA + TRAILING (MES continuo, PURA, miercoles incl.) ===')
rep('  sin trailing (base)', run(mes, trail=None))
rep('  trailing 20t (5.0pt)', run(mes, trail=5.0))
rep('  trailing 30t (7.5pt)', run(mes, trail=7.5))
rep('  trailing 40t (10 pt)', run(mes, trail=10.0))

def run_be(rows, be_trig):
    """mover a break-even cuando avanza be_trig puntos a favor; luego mantener hasta 13:00. Sin trailing."""
    by=defaultdict(list)
    for i,r in enumerate(rows): by[et(r[0]).date()].append(i)
    trades=[]
    for day in sorted(by):
        idx=by[day]
        rhi=-1e18; rlo=1e18; haveref=False
        for i in idx:
            e=et(rows[i][0]); mm=e.hour*60+e.minute
            if 570<=mm<600:
                haveref=True
                if rows[i][2]>rhi: rhi=rows[i][2]
                if rows[i][3]<rlo: rlo=rows[i][3]
        if not haveref or rhi<=rlo: continue
        pos=0; entry=0; exitpx=None; stop=0
        for i in idx:
            e=et(rows[i][0]); mm=e.hour*60+e.minute
            if mm<600: continue
            if utcmin(rows[i][0])>=960:
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
                if pos==1: stop=rlo
                elif pos==-1: stop=rhi
            else:
                if pos==1 and l<=stop: exitpx=stop; break
                if pos==-1 and h>=stop: exitpx=stop; break
                if pos==1 and h>=entry+be_trig: stop=max(stop, entry)
                if pos==-1 and l<=entry-be_trig: stop=min(stop, entry)
        if pos!=0 and exitpx is None: exitpx=rows[idx[-1]][4]
        if pos!=0:
            p=(exitpx-entry) if pos==1 else (entry-exitpx)
            trades.append((day,p,rhi-rlo))
    return trades
print()
print('=== punto medio: break-even a +Xt, luego correr hasta 13:00 (sin trailing) ===')
rep('  BE a +20t', run_be(mes,5.0))
rep('  BE a +30t', run_be(mes,7.5))
rep('  BE a +40t', run_be(mes,10.0))
rep('  sin BE (base)', run(mes, trail=None))
