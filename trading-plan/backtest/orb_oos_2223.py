import connors_rsi2 as C
from datetime import datetime
from collections import defaultdict
UTC=C.UTC; NY=C.NY
DPP=5.0; COST=2.5
def et(dt): return dt.replace(tzinfo=UTC).astimezone(NY)
def utcmin(dt): return dt.hour*60+dt.minute
def load_raw(fn):
    rows=[]
    for ln in open(fn):
        p=ln.strip().split(';')
        if len(p)<5: continue
        try: dt=datetime.strptime(p[0],'%Y%m%d %H%M%S')
        except: continue
        rows.append([dt,float(p[1]),float(p[2]),float(p[3]),float(p[4])])
    rows.sort(); return rows
def bt(rows, be_trig, months, year):
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
        if not (day.year==year and day.month in months): continue   # solo trimestre front-month
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
                if be_trig is not None:
                    if pos==1 and h>=entry+be_trig: stop=max(stop, entry)
                    if pos==-1 and l<=entry-be_trig: stop=min(stop, entry)
        if pos!=0 and exitpx is None: exitpx=rows[idx[-1]][4]
        if pos!=0:
            p=(exitpx-entry) if pos==1 else (entry-exitpx)
            trades.append((day,p))
    return trades
base='/root/.claude/uploads/34cce73d-0c23-533e-95a7-ef3cccabda66/'
CT=[('b68ed482-MES_0322',2022,{1,2,3}),('79d80351-MES_0622',2022,{4,5,6}),
    ('e60dcbc8-MES_0922',2022,{7,8,9}),('7a5b2592-MES_1222',2022,{10,11,12}),
    ('1c001371-MES_0323',2023,{1,2,3}),('4a8c4c4b-MES_0623',2023,{4,5,6}),
    ('73944704-MES_0923',2023,{7,8,9}),('120beb7d-MES_1223',2023,{10,11,12})]
def run(be, label):
    allt=[]
    for fn,yr,mo in CT: allt+=bt(load_raw(base+fn+'.Last.txt'), be, mo, yr)
    n=len(allt); net=sum(p*DPP for _,p in allt)-n*COST
    ww=[p for _,p in allt if p>0]; gw=sum(p*DPP for _,p in allt if p>0); gl=-sum(p*DPP for _,p in allt if p<=0)
    byy=defaultdict(list)
    for d,p in allt: byy[d.year].append(p)
    eq=0;pk=0;mdd=0; byday=defaultdict(float)
    for d,p in sorted(allt): v=p*DPP-COST; eq+=v;pk=max(pk,eq);mdd=min(mdd,eq-pk); byday[d]+=v
    pd=min(byday.values())
    yr='  '.join(f'{y}:{len(byy[y])}op/${sum(x*DPP for x in byy[y])-len(byy[y])*COST:+.0f}' for y in sorted(byy))
    print(f'{label}: n={n} WR {100*len(ww)/n:.0f}% NETO ${net:+.0f} PF {gw/gl if gl else 9:.2f} DD ${mdd:+.0f} peorDia ${pd:+.0f}')
    print(f'      {yr}')
print('=== OOS MES 2022-2023 — ORB apertura USA (front-month por trimestre, miercoles incl.) ===')
run(12.5, 'CAMPEON BE +50t ')
run(15.0, '  BE +60t      ')
run(None, '  base sin BE   ')
