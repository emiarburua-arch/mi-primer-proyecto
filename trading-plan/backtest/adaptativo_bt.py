#!/usr/bin/env python3
"""Backtest del sistema ADAPTATIVO, fiel al NinjaScript corregido, sobre contratos MES sueltos.
Señal = resultado REAL de cada operación convertido a equivalente-fade (faded? pnl : -pnl).
SMA200 y mediana de volatilidad se resetean por contrato; la señal de régimen es continua."""
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import deque, defaultdict

UTC=ZoneInfo('UTC'); NY=ZoneInfo('America/New_York')
MA=200; ORB_MIN=30; VOL_LB=20; RTH_OPEN=930; FLAT=1555; K=10
DPP=5.0; C=2.5
rthOpenMin=(RTH_OPEN//100)*60+(RTH_OPEN%100); orbEndMin=rthOpenMin+ORB_MIN
flatMin=(FLAT//100)*60+(FLAT%100)

def load(fn):
    rows=[]
    for ln in open(fn):
        p=ln.strip().split(';')
        if len(p)<5: continue
        dt=datetime.strptime(p[0],'%Y%m%d %H%M%S')
        rows.append((dt,float(p[1]),float(p[2]),float(p[3]),float(p[4])))
    rows.sort()
    return rows

# día operable de un contrato: devuelve (fecha, fade_dir, breakout_outcomes)
# Para cada día con ruptura filtrada, calculamos: dir de ruptura, entry, R, y qué pasa
# con las dos barreras (reversión=extremo opuesto, continuación=1R) => fade gana/pierde.
def contract_days(rows):
    # SMA200 sobre todas las barras del contrato
    buf=deque(); s=0.0; sma=[None]*len(rows)
    for i,r in enumerate(rows):
        buf.append(r[4]); s+=r[4]
        if len(buf)>MA: s-=buf.popleft()
        if len(buf)==MA: sma[i]=s/MA
    et=lambda dt: dt.replace(tzinfo=UTC).astimezone(NY)
    by=defaultdict(list)
    for i,r in enumerate(rows):
        e=et(r[0]); by[e.date()].append((i,r,e))
    rangeHist=[]; prevDayDir=0
    out=[]  # (fecha, breakoutUp, entry, R, orbLo, orbHi, bars_after)
    for day in sorted(by):
        db=by[day]
        sessOpen=None; sessClose=None; orbHi=-1e18; orbLo=1e18; orbActive=False
        volOK=False; evaluated=False; decided=False; got=None
        for k,(i,r,e) in enumerate(db):
            mins=e.hour*60+e.minute; hhmm=e.hour*100+e.minute
            o,h,l,c=r[1],r[2],r[3],r[4]
            if mins>=rthOpenMin and hhmm<1600:
                if sessOpen is None: sessOpen=o
                sessClose=c
            if rthOpenMin<=mins<orbEndMin:
                orbActive=True
                if h>orbHi: orbHi=h
                if l<orbLo: orbLo=l
            elif orbActive and not evaluated and mins>=orbEndMin:
                evaluated=True
                frac=(orbHi-orbLo)/orbHi if orbHi>0 else 0
                if len(rangeHist)>=10:
                    last=sorted(rangeHist[-VOL_LB:]); med=last[len(last)//2]; volOK=frac>med
                rangeHist.append(frac)
            if decided or not evaluated or not volOK or mins<orbEndMin: continue
            smav=sma[i]
            if smav is None: continue
            up=c>orbHi; down=c<orbLo
            if not up and not down: continue
            decided=True
            maOK=(c>smav) if up else (c<smav)
            dirOK=(prevDayDir==1) if up else (prevDayDir==-1)
            if not (maOK and dirOK): continue
            got=(day,up,c,orbHi-orbLo,orbLo,orbHi,db[k+1:])
        if got: out.append(got)
        if sessOpen is not None:
            prevDayDir=1 if sessClose>sessOpen else -1
    return out

def simulate(day_infos):
    """day_infos: lista global ordenada por fecha. Corre el adaptativo con señal continua."""
    hist=[]; trades=[]
    for (day,up,entry,R,orbLo,orbHi,after) in day_infos:
        chooseFade = True if len(hist)==0 else (sum(hist[-K:])>=0)
        goLong = (not up) if chooseFade else up
        if not chooseFade:
            stop = orbLo if up else orbHi
            tgt  = entry+R if up else entry-R
        else:
            tgt  = orbLo if up else orbHi
            stop = entry+R if up else entry-R
        # simular salida sobre las barras siguientes
        realized=None
        for (i,r,e) in after:
            hh=e.hour*100+e.minute; h=r[2]; l=r[3]; c=r[4]
            if hh>=FLAT:
                realized=(c-entry) if goLong else (entry-c); break
            hitS = l<=stop if goLong else h>=stop
            hitT = h>=tgt if goLong else l<=tgt
            if hitS: realized=-abs(entry-stop); break
            if hitT: realized=abs(tgt-entry); break
        if realized is None: realized=0.0
        faded = chooseFade
        trades.append((day,realized))
        hist.append(realized if faded else -realized)
    return trades

FILES=[('b68ed482-MES_0322'),('79d80351-MES_0622'),('e60dcbc8-MES_0922'),
       ('7a5b2592-MES_1222'),('1c001371-MES_0323'),('4a8c4c4b-MES_0623'),('73944704-MES_0923')]
base='/root/.claude/uploads/34cce73d-0c23-533e-95a7-ef3cccabda66/'
alldays=[]
for fn in FILES:
    di=contract_days(load(base+fn+'.Last.txt'))
    alldays+=di
    print(f'{fn}: {len(di)} días operables, {di[0][0]} -> {di[-1][0]}' if di else f'{fn}: 0')
alldays.sort(key=lambda x:x[0])
tr=simulate(alldays)
net=sum(p*DPP-C for _,p in tr); w=[p for _,p in tr if p>0]
gw=sum(p*DPP for _,p in tr if p>0); gl=-sum(p*DPP for _,p in tr if p<=0)
print(f'\n=== ADAPTATIVO MES 2022-2023 (continuo, con costos) ===')
print(f'n={len(tr)}  WR {100*len(w)/len(tr):.0f}%  neto \${net:+.0f}  PF {gw/gl:.2f}  media \${net/len(tr):+.1f}/op')
byy=defaultdict(list)
for d,p in tr: byy[d.year].append(p)
for y in sorted(byy):
    v=byy[y]; ww=len([x for x in v if x>0])
    print(f'  {y}: n={len(v):2d} neto \${sum(x*DPP-C for x in v):+.0f} WR {100*ww/len(v):.0f}%')
eq=0;pk=0;mdd=0
for d,p in tr: eq+=p*DPP-C;pk=max(pk,eq);mdd=min(mdd,eq-pk)
print(f'  max drawdown 1 lote: \${mdd:+.0f}')
