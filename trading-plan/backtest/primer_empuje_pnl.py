#!/usr/bin/env python3
"""Backtest completo y fiel del NinjaScript PrimerEmpuje (con salida stop/target/flatten)
sobre MES, con P&L en dolares y desglose por ano. Regla D3: la primera ruptura cierra el dia."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import deque, defaultdict

UTC=ZoneInfo('UTC'); NY=ZoneInfo('America/New_York')
FN=os.environ.get('MES_M1', os.path.join(os.environ.get('CL_DATA_DIR','data'),'MES_M1_continuo.csv'))
MA=200; ORB_MIN=30; VOL_LB=20; RTH_OPEN=930; FLAT=1555
DOLLARS_PER_PT=5.0          # MES = $5 por punto
COST_PER_TRADE=2.50         # comision ida+vuelta aprox (MES ~ $1.24 x2) + un poco de slippage

rows=[]
with open(FN) as f:
    next(f)
    for ln in f:
        p=ln.split(',')
        rows.append((datetime.strptime(p[0],'%Y-%m-%d %H:%M:%S'),float(p[1]),float(p[2]),float(p[3]),float(p[4])))
buf=deque(); s=0.0; sma_series=[None]*len(rows)
for i,r in enumerate(rows):
    buf.append(r[4]); s+=r[4]
    if len(buf)>MA: s-=buf.popleft()
    if len(buf)==MA: sma_series[i]=s/MA
et=lambda dt: dt.replace(tzinfo=UTC).astimezone(NY)
by=defaultdict(list)
for i,r in enumerate(rows):
    e=et(r[0]); by[e.date()].append((i,r,e))
rthOpenMin=(RTH_OPEN//100)*60+(RTH_OPEN%100); orbEndMin=rthOpenMin+ORB_MIN
flatMin=(FLAT//100)*60+(FLAT%100)
rangeHist=[]; prevDayDir=0
trades=[]
for day in sorted(by):
    db=by[day]
    sessOpen=None; sessClose=None; orbHi=-1e18; orbLo=1e18; orbActive=False
    volOK=False; evaluated=False; decided=False
    entry=None; isLong=None; stop=None; tgt=None; ei=None
    for (i,r,e) in db:
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
        # gestion de la posicion abierta
        if entry is not None:
            if mins>=flatMin:
                out=(c-entry) if isLong else (entry-c)
                trades.append((day,out)); entry=None; continue
            hitS = l<=stop if isLong else h>=stop
            hitT = h>=tgt if isLong else l<=tgt
            if hitS: trades.append((day,-(abs(entry-stop)))); entry=None; continue
            if hitT: trades.append((day,abs(tgt-entry))); entry=None; continue
        # busqueda de entrada (una vez por dia)
        if decided or not evaluated or not volOK or mins<orbEndMin: continue
        if entry is not None: continue
        smav=sma_series[i]
        if smav is None: continue
        up=c>orbHi; down=c<orbLo
        if not up and not down: continue
        decided=True   # D3: primera ruptura cierra el dia
        isLong=up
        maOK=(c>smav) if isLong else (c<smav)
        dirOK=(prevDayDir==1) if isLong else (prevDayDir==-1)
        if not (maOK and dirOK): continue
        R=orbHi-orbLo; entry=c; ei=i
        stop=orbLo if isLong else orbHi
        tgt=entry+R if isLong else entry-R
    if entry is not None:  # no cerro (raro): marcar a ultimo close
        trades.append((day,0.0)); entry=None
    if sessOpen is not None:
        prevDayDir=1 if sessClose>sessOpen else -1

def rep(name, ts):
    if not ts: print(f'{name}: sin trades'); return
    n=len(ts); dollars=sum(pt*DOLLARS_PER_PT-COST_PER_TRADE for _,pt in ts)
    gross=sum(pt*DOLLARS_PER_PT for _,pt in ts)
    wins=[pt for _,pt in ts if pt>0]; losses=[pt for _,pt in ts if pt<=0]
    wr=100*len(wins)/n
    gw=sum(pt*DOLLARS_PER_PT for pt in wins); gl=-sum(pt*DOLLARS_PER_PT for pt in losses)
    pf=gw/gl if gl>0 else 9
    print(f'{name}: n={n}  WR {wr:.0f}%  neto ${dollars:+.0f}  bruto ${gross:+.0f}  PF {pf:.2f}  media ${dollars/n:+.1f}/op')

print('=== MES Primer Empuje (fiel, con costos ~$2.5/op) ===\n')
rep('TOTAL          ', trades)
byyr=defaultdict(list)
for d,pt in trades: byyr[d.year].append((d,pt))
for y in sorted(byyr): rep(f'  {y}         ', byyr[y])
win=[(d,pt) for d,pt in trades if datetime(2026,6,1).date()<=d<=datetime(2026,8,25).date()]
print()
rep('Jun-Ago 2026   ', win)

print('\n=== Mis operaciones jun-ago 2026 (dir, entrada, resultado en pts) ===')
# reconstruir con detalle
det=[]
rangeHist=[]; prevDayDir=0
for day in sorted(by):
    db=by[day]
    sessOpen=None; sessClose=None; orbHi=-1e18; orbLo=1e18; orbActive=False
    volOK=False; evaluated=False; decided=False
    entry=None; isLong=None; stop=None; tgt=None; edir=None; een=None
    res=None
    for (i,r,e) in db:
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
        if entry is not None:
            if mins>=flatMin: res=('flat',(c-entry) if isLong else (entry-c)); entry=None; continue
            hitS=l<=stop if isLong else h>=stop
            hitT=h>=tgt if isLong else l<=tgt
            if hitS: res=('STOP',-(abs(een-stop))); entry=None; continue
            if hitT: res=('TGT',abs(tgt-een)); entry=None; continue
        if decided or not evaluated or not volOK or mins<orbEndMin: continue
        if entry is not None: continue
        smav=sma_series[i]
        if smav is None: continue
        up=c>orbHi; down=c<orbLo
        if not up and not down: continue
        decided=True; isLong=up
        maOK=(c>smav) if isLong else (c<smav)
        dirOK=(prevDayDir==1) if isLong else (prevDayDir==-1)
        if not (maOK and dirOK): continue
        R=orbHi-orbLo; entry=c; een=c; edir='UP' if isLong else 'DOWN'
        stop=orbLo if isLong else orbHi; tgt=entry+R if isLong else entry-R
    if datetime(2026,6,1).date()<=day<=datetime(2026,8,25).date() and edir is not None:
        det.append((day,edir,een,stop,tgt,res))
    if sessOpen is not None:
        prevDayDir=1 if sessClose>sessOpen else -1
for d,dr,en,st,tg,rs in det:
    print(f'  {d} {dr:4s} entry={en:.2f} stop={st:.2f} tgt={tg:.2f}  -> {rs[0]:4s} {rs[1]*DOLLARS_PER_PT:+.0f}$')
