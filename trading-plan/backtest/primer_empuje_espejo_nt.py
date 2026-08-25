#!/usr/bin/env python3
"""Espejo FIEL del NinjaScript PrimerEmpuje2, para diagnosticar NT vs Python.
Replica: SMA200 sobre el continuo 1min, ORB 09:30-10:00 ET, frac=(hi-lo)/hi,
mediana de las ultimas 20 (con >=10 historia), volOK=frac>med, prevDayDir,
breakout por cierre, maOK=close vs sma, dirOK=direccion dia previo, 1 trade/dia,
aplanado 15:55 ET. Imprime por dia lo MISMO que el debug .cs."""
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import deque, defaultdict

import os
UTC = ZoneInfo('UTC'); NY = ZoneInfo('America/New_York')
FN = os.environ.get('MES_M1', os.path.join(os.environ.get('CL_DATA_DIR', 'data'), 'MES_M1_continuo.csv'))
START = datetime(2026,6,1).date(); END = datetime(2026,8,25).date()
MA=200; ORB_MIN=30; VOL_LB=20; RTH_OPEN=930; FLAT=1555

rows=[]
with open(FN) as f:
    next(f)
    for ln in f:
        p=ln.split(',')
        dt=datetime.strptime(p[0],'%Y-%m-%d %H:%M:%S')
        rows.append((dt,float(p[1]),float(p[2]),float(p[3]),float(p[4])))

# SMA200 sobre TODAS las barras (como NinjaScript sobre el continuo)
closes=deque(maxlen=MA); sma_at={}
running=[]
sma_series=[None]*len(rows)
s=0.0
buf=deque()
for i,r in enumerate(rows):
    buf.append(r[4]); s+=r[4]
    if len(buf)>MA: s-=buf.popleft()
    if len(buf)==MA: sma_series[i]=s/MA

et=lambda dt: dt.replace(tzinfo=UTC).astimezone(NY)
by=defaultdict(list)
for i,r in enumerate(rows):
    e=et(r[0])
    by[e.date()].append((i,r,e))

rthOpenMin=(RTH_OPEN//100)*60+(RTH_OPEN%100)
orbEndMin=rthOpenMin+ORB_MIN
rangeHist=[]
prevDayDir=0
ntrades=0; diag=[]
for day in sorted(by):
    day_bars=by[day]
    # --- direccion del dia (RTH 09:30-16:00) para usar como prevDayDir manana ---
    sessOpen=None; sessClose=None
    orbHi=-1e18; orbLo=1e18; orbActive=False
    frac=0.0; med=-1.0; volOK=False; orbSet=False; evaluated=False
    traded=False; broke=None
    for (i,r,e) in day_bars:
        mins=e.hour*60+e.minute; hhmm=e.hour*100+e.minute
        o,h,l,c=r[1],r[2],r[3],r[4]
        inRth = mins>=rthOpenMin and hhmm<1600
        if inRth:
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
                last=sorted(rangeHist[-VOL_LB:])
                med=last[len(last)//2]; volOK=frac>med
            rangeHist.append(frac); orbSet=volOK
        if hhmm>=FLAT: break
        if not orbSet or traded or mins<orbEndMin: continue
        smav=sma_series[i]
        if smav is None: continue
        up=c>orbHi; down=c<orbLo
        if not up and not down: continue
        isLong=up
        maOK=(c>smav) if isLong else (c<smav)
        dirOK=(prevDayDir==1) if isLong else (prevDayDir==-1)
        broke=(e.strftime('%H:%M'),'UP' if isLong else 'DOWN',c,smav,maOK,dirOK)
        traded=True
        if maOK and dirOK and START<=day<=END: ntrades+=1
    if START<=day<=END and evaluated:
        line=f"{day} ORB lo={orbLo:.2f} hi={orbHi:.2f} frac={frac:.5f} med={med:.5f} n={len(rangeHist)} volOK={volOK} prevDir={prevDayDir}"
        if broke:
            hm,dr,c,smav,mo,do=broke
            line+=f"\n   {hm} BREAK {dr} close={c:.2f} sma={smav:.2f} maOK={mo} dirOK={do} -> {'ENTRA' if (mo and do) else 'descarta'}"
        elif orbSet:
            line+="   (volOK pero sin ruptura)"
        else:
            line+="   (volOK=False, no busca ruptura)"
        diag.append(line)
    # set prevDayDir para el proximo dia
    if sessOpen is not None:
        prevDayDir = 1 if sessClose>sessOpen else -1

print('\n'.join(diag))
print(f"\n=== TRADES en {START}..{END}: {ntrades} ===")
