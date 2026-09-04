#!/usr/bin/env python3
"""Connors RSI(2) mean-reversion intradia — backtest fiel a las 10 pestañas del usuario.
Nucleo: SMA200 (tendencia) + SMA10 (retroceso/salida) + RSI(2) cruce 10/90.
Salida Connors: precio vuelve a cruzar la SMA10. Sin overnight.
Parametros opcionales: stop y target (en puntos), ventanas horarias, excluir miercoles.
"""
import sys, os
from datetime import datetime, time
from zoneinfo import ZoneInfo
from collections import defaultdict

UTC=ZoneInfo('UTC'); NY=ZoneInfo('America/New_York'); BA=ZoneInfo('America/Argentina/Buenos_Aires')

def load(fn):
    rows=[]
    with open(fn) as f:
        next(f)
        for ln in f:
            p=ln.split(',')
            rows.append([datetime.strptime(p[0],'%Y-%m-%d %H:%M:%S'),
                         float(p[1]),float(p[2]),float(p[3]),float(p[4])])
    return rows

def resample(rows, minutes):
    """Agrupa velas de 1 min en velas de N min (por bloque de reloj UTC)."""
    out=[]; cur=None; bkt=None
    for dt,o,h,l,c in rows:
        b=(dt.hour*60+dt.minute)//minutes
        key=(dt.date(), b)
        if key!=cur:
            if bkt: out.append(bkt)
            cur=key; bkt=[dt,o,h,l,c]
        else:
            if h>bkt[2]: bkt[2]=h
            if l<bkt[3]: bkt[3]=l
            bkt[4]=c
    if bkt: out.append(bkt)
    return out

def sma(vals, n):
    out=[None]*len(vals); s=0.0
    from collections import deque
    q=deque()
    for i,v in enumerate(vals):
        q.append(v); s+=v
        if len(q)>n: s-=q.popleft()
        if len(q)==n: out[i]=s/n
    return out

def rsi_nt(closes, period=2, smooth=3):
    """Aproximacion a la RSI de NinjaTrader: Wilder RSI(period) + EMA(smooth)."""
    n=len(closes); rraw=[None]*n
    avgUp=avgDn=None
    for i in range(1,n):
        d=closes[i]-closes[i-1]
        up=d if d>0 else 0.0; dn=-d if d<0 else 0.0
        if avgUp is None: avgUp=up; avgDn=dn
        else:
            avgUp=(avgUp*(period-1)+up)/period
            avgDn=(avgDn*(period-1)+dn)/period
        rraw[i]=100.0 if avgDn==0 else (0.0 if avgUp==0 else 100-100/(1+avgUp/avgDn))
    # EMA smoothing
    out=[None]*n; k=2/(smooth+1); e=None
    for i in range(n):
        if rraw[i] is None: continue
        e=rraw[i] if e is None else rraw[i]*k+e*(1-k)
        out[i]=e
    return out

def atr(rows, period=14):
    """ATR de Wilder sobre las velas dadas (usa H/L/C)."""
    n=len(rows); out=[None]*n; a=None
    for i in range(n):
        h=rows[i][2]; l=rows[i][3]
        if i==0: tr=h-l
        else:
            pc=rows[i-1][4]; tr=max(h-l, abs(h-pc), abs(l-pc))
        a=tr if a is None else (a*(period-1)+tr)/period
        out[i]=a
    return out

def backtest(rows, stop_pts=None, tgt_pts=None, win1=None, win2=None,
             excl_wed=True, use_windows=True, tz=BA, rsi_lo=10, rsi_hi=90,
             atr_s=None, atr_t=None, atr_period=14):
    et=lambda dt: dt.replace(tzinfo=UTC).astimezone(tz)
    closes=[r[4] for r in rows]
    s10=sma(closes,10); s200=sma(closes,200); rsi=rsi_nt(closes,2,3)
    av=atr(rows,atr_period) if atr_s is not None else None
    def inwin(tm):
        if not use_windows: return True
        for w in (win1,win2):
            if w and w[0]<=tm<w[1]: return True
        return False
    def any_win_end(tm):
        # fuera de toda ventana (para aplanar por tiempo)
        return not inwin(tm)
    pos=0; entry=0.0; trades=[]; edate=None; sd=None; td=None
    for i in range(len(rows)):
        if s200[i] is None or s10[i] is None or rsi[i] is None or rsi[i-1] is None: continue
        dt=et(rows[i][0]); tm=dt.time(); c=closes[i]; h=rows[i][2]; l=rows[i][3]
        # gestion de posicion (sd/td = distancias de stop/target de ESTA operacion)
        if pos!=0:
            if pos>0:
                if sd and l<=entry-sd: trades.append((edate,-sd)); pos=0
                elif td and h>=entry+td: trades.append((edate,td)); pos=0
                elif c>s10[i]: trades.append((edate,c-entry)); pos=0          # salida Connors
                elif use_windows and any_win_end(tm): trades.append((edate,c-entry)); pos=0
            else:
                if sd and h>=entry+sd: trades.append((edate,-sd)); pos=0
                elif td and l<=entry-td: trades.append((edate,td)); pos=0
                elif c<s10[i]: trades.append((edate,entry-c)); pos=0
                elif use_windows and any_win_end(tm): trades.append((edate,entry-c)); pos=0
            if pos!=0: continue
        # entradas (solo flat)
        if pos==0:
            if excl_wed and dt.weekday()==2: continue   # 2=miercoles
            if not inwin(tm): continue
            longsig = c>s200[i] and c<s10[i] and rsi[i]>rsi_lo and rsi[i-1]<rsi_lo
            shortsig= c<s200[i] and c>s10[i] and rsi[i]<rsi_hi and rsi[i-1]>rsi_hi
            if longsig or shortsig:
                # distancias: por ATR si atr_s dado; si no, fijas en puntos
                if av is not None and av[i]:
                    sd=atr_s*av[i]; td=(atr_t*av[i]) if atr_t else None
                else:
                    sd=stop_pts; td=tgt_pts
                if longsig: pos=1; entry=c; edate=dt.date()
                else: pos=-1; entry=c; edate=dt.date()
    return trades

def rep(name, trades, dpp):
    if not trades: print(f'{name}: sin trades'); return
    n=len(trades); pts=sum(t[1] for t in trades)
    w=[t for t in trades if t[1]>0]
    gw=sum(t[1] for t in w); gl=-sum(t[1] for t in trades if t[1]<=0)
    net=pts*dpp
    byy=defaultdict(float)
    for d,p in trades: byy[d.year]+=p*dpp
    yr='  '.join(f'{y}:${byy[y]:+.0f}' for y in sorted(byy))
    print(f'{name}: n={n} WR {100*len(w)/n:.0f}% neto ${net:+.0f} PF {gw/gl if gl else 9:.2f} media ${net/n:+.1f}/op | {yr}')

if __name__=='__main__':
    base='/tmp/claude-0/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/scratchpad/data/'
    # === MES: $5/punto. Ventana 9-13 hora Argentina (UTC-3). Miercoles excluido. ===
    print('=== MES (continuo) — NUCLEO Connors RSI(2), ventana 9-13 ARG, sin miercoles ===')
    print('    (salida = precio vuelve a cruzar SMA10, como Connors; SIN stop/target aun)')
    mes=load(base+'MES_M1_continuo.csv')
    w=(time(9,0),time(13,0))   # hora de Buenos Aires
    rep('MES nucleo', backtest(mes, win1=w, win2=None, use_windows=True), 5.0)
    print()
    print('=== Referencia: MISMO nucleo SIN excluir miercoles ===')
    rep('MES nucleo c/miercoles', backtest(mes, win1=w, win2=None, use_windows=True, excl_wed=False), 5.0)

    # === BARRIDO stop/target (con costo realista MES ~$2.5/op: comision+medio tick) ===
    print()
    print('=== BARRIDO stop x target (MES, ventana 9-13 ARG, sin miercoles, NETO de $2.5/op) ===')
    COST=2.5
    def repc(name, trades, dpp, cost):
        if not trades: print(f'{name}: sin trades'); return None
        n=len(trades); net=sum(t[1]*dpp for t in trades)-n*cost
        w=[t for t in trades if t[1]>0]
        gw=sum(t[1]*dpp for t in trades if t[1]>0); gl=-sum(t[1]*dpp for t in trades if t[1]<=0)
        byy=defaultdict(float)
        for d,p in trades: byy[d.year]+=p*dpp-cost
        # drawdown sobre curva de equity por operacion (orden cronologico)
        eq=0;pk=0;mdd=0
        for d,p in sorted(trades):
            eq+=p*dpp-cost; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        yr='  '.join(f'{y}:${byy[y]:+.0f}' for y in sorted(byy))
        pf=gw/gl if gl else 9
        print(f'{name}: n={n} WR {100*len(w)/n:.0f}% NETO ${net:+.0f} PF {pf:.2f} DD ${mdd:+.0f} | {yr}')
        return net
    best=None
    for stop in (3,4,5,6,8,10,12):
        for tgt in (2,3,4,5,6,8,10):
            tr=backtest(mes, stop_pts=stop, tgt_pts=tgt, win1=w, use_windows=True)
            net=repc(f'  stop {stop:>2} / tgt {tgt:>2}', tr, 5.0, COST)
            if net is not None and (best is None or net>best[0]): best=(net,stop,tgt)
    if best: print(f'\n>>> MEJOR: stop {best[1]} / target {best[2]} -> NETO ${best[0]:+.0f}')

    # === MISMO nucleo en velas de 5 y 15 min (RSI(2) tiene sentido en TF mas alto) ===
    print()
    print('=== NUCLEO en 5m y 15m (sin stop/target, salida SMA10) — BRUTO y NETO $2.5/op ===')
    for tf in (5,15,20,30,60):
        rr=resample(mes, tf)
        tr=backtest(rr, win1=w, use_windows=True)
        rep(f'MES {tf:>2}m bruto', tr, 5.0)
        repc(f'MES {tf:>2}m NETO ', tr, 5.0, COST)

    # === stop/target sobre 30m (el TF con edge) ===
    print()
    print('=== BARRIDO stop x target en 30m (NETO $2.5/op) ===')
    r30=resample(mes,30); best=None
    for stop in (6,8,10,12,15,20):
        for tgt in (4,6,8,10,12,15):
            tr=backtest(r30, stop_pts=stop, tgt_pts=tgt, win1=w, use_windows=True)
            net=repc(f'  stop {stop:>2} / tgt {tgt:>2}', tr, 5.0, COST)
            if net is not None and (best is None or net>best[0]): best=(net,stop,tgt)
    if best: print(f'\n>>> MEJOR 30m: stop {best[1]} / target {best[2]} -> NETO ${best[0]:+.0f}')

    # === confirmacion cross-instrumento del nucleo 30m (sin stop/target) ===
    print()
    print('=== NUCLEO 30m en otros instrumentos (mismo codigo, ventana 9-13 ARG, sin miercoles) ===')
    for fn,dpp,lbl in (('MNQ_M1_continuo.csv',2.0,'MNQ $2/pt'),
                       ('CL_M1_continuo.csv',10.0,'CL micro MCL $10/pt')):
        d=load(base+fn); r=resample(d,30)
        tr=backtest(r, win1=w, use_windows=True)
        rep(f'{lbl:>18} bruto', tr, dpp)
        repc(f'{lbl:>18} NETO ', tr, dpp, COST)
