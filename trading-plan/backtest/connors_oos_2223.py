import connors_rsi2 as C
from datetime import time, datetime
from collections import defaultdict
UTC=C.UTC; BA=C.BA
def load_raw(fn):
    rows=[]
    for ln in open(fn):
        p=ln.strip().split(';')
        if len(p)<5: continue
        try: dt=datetime.strptime(p[0],'%Y%m%d %H%M%S')
        except: continue
        rows.append([dt,float(p[1]),float(p[2]),float(p[3]),float(p[4])])
    rows.sort(); return rows
def adx(rows, period=14):
    n=len(rows); tr=[0.0]*n; pdm=[0.0]*n; mdm=[0.0]*n
    for i in range(1,n):
        h,l=rows[i][2],rows[i][3]; ph,pl,pc=rows[i-1][2],rows[i-1][3],rows[i-1][4]
        up=h-ph; dn=pl-l
        pdm[i]=up if (up>dn and up>0) else 0.0
        mdm[i]=dn if (dn>up and dn>0) else 0.0
        tr[i]=max(h-l,abs(h-pc),abs(l-pc))
    def wild(x):
        o=[None]*n; s=None
        for i in range(1,n):
            s=x[i] if s is None else s-s/period+x[i]; o[i]=s
        return o
    str_,spdm,smdm=wild(tr),wild(pdm),wild(mdm); pdi=[None]*n; mdi=[None]*n; dx=[None]*n
    for i in range(n):
        if str_[i]:
            pdi[i]=100*spdm[i]/str_[i]; mdi[i]=100*smdm[i]/str_[i]
            s=pdi[i]+mdi[i]; dx[i]=100*abs(pdi[i]-mdi[i])/s if s else 0.0
    adxl=[None]*n; a=None; cnt=0; acc=0.0
    for i in range(n):
        if dx[i] is None: continue
        cnt+=1; acc+=dx[i]
        if cnt<period: continue
        a=acc/period if a is None else (a*(period-1)+dx[i])/period
        adxl[i]=a
    return adxl
def bt(rows, stop, tgt, adx_min, win, months, year, excl_wed=True):
    et=lambda dt: dt.replace(tzinfo=UTC).astimezone(BA)
    cl=[r[4] for r in rows]; s10=C.sma(cl,10); s200=C.sma(cl,200); rsi=C.rsi_nt(cl,2,3); ax=adx(rows,14)
    inwin=lambda tm: win[0]<=tm<win[1]
    pos=0; entry=0; trades=[]; edate=None
    for i in range(1,len(rows)):
        if s200[i] is None or s10[i] is None or rsi[i] is None or rsi[i-1] is None or ax[i] is None: continue
        dt=et(rows[i][0]); tm=dt.time(); c=cl[i]; h=rows[i][2]; l=rows[i][3]
        if pos!=0:
            if pos>0:
                if l<=entry-stop: trades.append((edate,-stop)); pos=0
                elif h>=entry+tgt: trades.append((edate,tgt)); pos=0
                elif c>s10[i]: trades.append((edate,c-entry)); pos=0
                elif not inwin(tm): trades.append((edate,c-entry)); pos=0
            else:
                if h>=entry+stop: trades.append((edate,-stop)); pos=0
                elif l<=entry-tgt: trades.append((edate,tgt)); pos=0
                elif c<s10[i]: trades.append((edate,entry-c)); pos=0
                elif not inwin(tm): trades.append((edate,entry-c)); pos=0
            if pos!=0: continue
        # entradas solo en el trimestre front-month de este contrato
        if not (dt.year==year and dt.month in months): continue
        if excl_wed and dt.weekday()==2: continue
        if not inwin(tm): continue
        axok = ax[i]>adx_min if adx_min is not None else True
        longsig = c>s200[i] and c<s10[i] and rsi[i]>10 and rsi[i-1]<10 and axok
        shortsig= c<s200[i] and c>s10[i] and rsi[i]<90 and rsi[i-1]>90 and axok
        if longsig: pos=1; entry=c; edate=dt.date()
        elif shortsig: pos=-1; entry=c; edate=dt.date()
    return trades

base='/root/.claude/uploads/34cce73d-0c23-533e-95a7-ef3cccabda66/'
CT=[('b68ed482-MES_0322',2022,{1,2,3}),('79d80351-MES_0622',2022,{4,5,6}),
    ('e60dcbc8-MES_0922',2022,{7,8,9}),('7a5b2592-MES_1222',2022,{10,11,12}),
    ('1c001371-MES_0323',2023,{1,2,3}),('4a8c4c4b-MES_0623',2023,{4,5,6}),
    ('73944704-MES_0923',2023,{7,8,9}),('120beb7d-MES_1223',2023,{10,11,12})]
w=(time(9,0),time(13,0)); COST=2.5; DPP=5.0
def run(adx_min,stop,tgt,label):
    allt=[]
    for fn,yr,mo in CT:
        r=C.resample(load_raw(base+fn+'.Last.txt'),15)
        allt+=bt(r,stop,tgt,adx_min,w,mo,yr)
    n=len(allt); net=sum(p*DPP for _,p in allt)-n*COST
    ww=[p for _,p in allt if p>0]; gw=sum(p*DPP for _,p in allt if p>0); gl=-sum(p*DPP for _,p in allt if p<=0)
    byy=defaultdict(list)
    for d,p in allt: byy[d.year].append(p)
    yr='  '.join(f'{y}:{len(byy[y])}op/${sum(x*DPP for x in byy[y])-len(byy[y])*COST:+.0f}' for y in sorted(byy))
    print(f'{label}: n={n} WR {100*len(ww)/n:.0f}% NETO ${net:+.0f} PF {gw/gl if gl else 9:.2f}')
    print(f'      {yr}')
print('=== OOS MES 2022-2023 (front-month por trimestre, ventana 9-13 ARG, sin miercoles) ===')
run(20,7.5,7.5, 'CAMPEON RSI+ADX>20 30t 1:1  ')
run(None,7.5,7.5,'  solo RSI       30t 1:1    ')
run(20,10,15,   '  RSI+ADX>20     40t/60t    ')
run(None,10,15, '  solo RSI       40t/60t    ')
