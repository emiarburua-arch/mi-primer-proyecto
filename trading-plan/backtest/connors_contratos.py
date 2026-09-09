import connors_rsi2 as C
from datetime import datetime, time
from collections import defaultdict
UTC=C.UTC; NY=C.NY
DPP=5.0; COST=2.5; STOP=7.5; TGT=7.5   # 30 ticks MES
def et(dt): return dt.replace(tzinfo=UTC).astimezone(NY)
def load_raw(fn):
    rows=[]
    for ln in open(fn):
        p=ln.strip().split(';')
        if len(p)<5: continue
        try: dt=datetime.strptime(p[0],'%Y%m%d %H%M%S')
        except: continue
        rows.append([dt,float(p[1]),float(p[2]),float(p[3]),float(p[4])])
    rows.sort(); return rows
def bt(rows, year, months):
    r15=C.resample(rows,15)
    closes=[b[4] for b in r15]
    s10=C.sma(closes,10); s200=C.sma(closes,200); rsi=C.rsi_nt(closes,2,3)
    W0=time(8,0); W1=time(12,0)   # ET fijo (= NinjaScript con NT en US Eastern)
    pos=0; entry=0; trades=[]; edate=None
    for i in range(1,len(r15)):
        if s200[i] is None or s10[i] is None or rsi[i] is None or rsi[i-1] is None: continue
        dt=et(r15[i][0]); tm=dt.time(); c=closes[i]; h=r15[i][2]; l=r15[i][3]
        inwin = W0<=tm<W1
        if pos!=0:
            if pos>0:
                if l<=entry-STOP: trades.append((edate,-STOP)); pos=0
                elif h>=entry+TGT: trades.append((edate,TGT)); pos=0
                elif c>s10[i]: trades.append((edate,c-entry)); pos=0
                elif not inwin: trades.append((edate,c-entry)); pos=0
            else:
                if h>=entry+STOP: trades.append((edate,-STOP)); pos=0
                elif l<=entry-TGT: trades.append((edate,TGT)); pos=0
                elif c<s10[i]: trades.append((edate,entry-c)); pos=0
                elif not inwin: trades.append((edate,entry-c)); pos=0
            if pos!=0: continue
        if not inwin: continue
        if dt.weekday()==2: continue           # miercoles excluido
        if not (dt.year==year and dt.month in months): continue
        longsig = c>s200[i] and c<s10[i] and rsi[i]>10 and rsi[i-1]<10
        shortsig= c<s200[i] and c>s10[i] and rsi[i]<90 and rsi[i-1]>90
        if longsig: pos=1; entry=c; edate=dt.date()
        elif shortsig: pos=-1; entry=c; edate=dt.date()
    return trades
base='/root/.claude/uploads/34cce73d-0c23-533e-95a7-ef3cccabda66/'
CT=[('b68ed482-MES_0322',2022,{1,2,3}),('79d80351-MES_0622',2022,{4,5,6}),('e60dcbc8-MES_0922',2022,{7,8,9}),('7a5b2592-MES_1222',2022,{10,11,12}),
    ('1c001371-MES_0323',2023,{1,2,3}),('4a8c4c4b-MES_0623',2023,{4,5,6}),('73944704-MES_0923',2023,{7,8,9}),('120beb7d-MES_1223',2023,{10,11,12}),
    ('683df816-MES_0324',2024,{1,2,3}),('f2175dbf-MES_0624',2024,{4,5,6}),('2e39367d-MES_0924',2024,{7,8,9}),('0c31f4c3-MES_1224',2024,{10,11,12}),
    ('1b08ec2f-MES_0325',2025,{1,2,3}),('316f8247-MES_0625',2025,{4,5,6}),('6a7afbde-MES_0925',2025,{7,8,9}),('30abd8a2-MES_1225',2025,{10,11,12}),
    ('0e3f750b-MES_0326',2026,{1,2,3}),('5c058cf9-MES_0626',2026,{4,5,6}),('d2d68b72-MES_0926',2026,{7,8,9})]
lbl={1:'Q1',4:'Q2',7:'Q3',10:'Q4'}
sym={1:'03',4:'06',7:'09',10:'12'}
allt=[]; posq=0; byy=defaultdict(float); cy=defaultdict(int)
print('=== CONNORS RSI(2) 30t/30t, 15m, ventana 8-12 ET, sin miercoles — contrato a contrato ===')
for fn,yr,mo in CT:
    tr=bt(load_raw(base+fn+'.Last.txt'), yr, mo); allt+=tr
    net=sum(p*DPP for _,p in tr)-len(tr)*COST
    if net>0: posq+=1
    for d,p in tr: byy[d.year]+=p*DPP; cy[d.year]+=1
    w=sum(1 for _,p in tr if p>0)
    print(f'  MES {sym[min(mo)]}-{str(yr)[2:]} ({yr} {lbl[min(mo)]}): n={len(tr):2d} WR {100*w/len(tr) if tr else 0:.0f}% neto ${net:+.0f}')
n=len(allt); net=sum(p*DPP for _,p in allt)-n*COST
gw=sum(p*DPP for _,p in allt if p>0); gl=-sum(p*DPP for _,p in allt if p<=0)
eq=0;pk=0;mdd=0
for d,p in sorted(allt): eq+=p*DPP-COST;pk=max(pk,eq);mdd=min(mdd,eq-pk)
yr='  '.join(f'{y}:${byy[y]-cy[y]*COST:+.0f}' for y in sorted(byy))
print(f'  === TOTAL n={n} WR {100*sum(1 for _,p in allt if p>0)/n:.0f}% NETO ${net:+.0f} PF {gw/gl if gl else 9:.2f} DD ${mdd:+.0f} trim+ {posq}/19')
print(f'      {yr}')
