import json,csv,io,re
from datetime import datetime
F={'BT':'/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453607816.txt',
   'R1':'/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453611346.txt',
   'R2':'/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453586271.txt'}
def money(s):
    s=s.replace('$','').replace(',','').strip()
    if not s: return None
    n=s.startswith('-'); s=s.lstrip('-')
    try: return (-1 if n else 1)*float(s)
    except: return None
def load(p):
    c=json.load(open(p))['fileContent']; i=[m.start() for m in re.finditer(r'Entrada de Datos ,',c)][-1]
    T=[]
    for r in c[i:c.find('Detalle por bloques',i)].split(' ,'):
        f=next(csv.reader(io.StringIO(r)))
        if len(f)>20 and f[2].strip() and re.match(r'\d{2}/\d{2}/\d{2}',f[3].strip() or ''):
            T.append(dict(fecha=f[3],hora=f[4],neto=money(f[21])))
    return T
BT=load(F['BT']); R=load(F['R1'])+load(F['R2'])
R=sorted(R,key=lambda t:(datetime.strptime(t['fecha'],'%d/%m/%y'),t['hora']))

def eq(T):
    e=0;o=[0.0]
    for t in T: e+=t['neto']; o.append(round(e,2))
    return o
be,re_=eq(BT),eq(R)
print('BT n=',len(be),'min',min(be),'max',max(be))
print('R  n=',len(re_),'min',min(re_),'max',max(re_))

# normalizamos ambos al eje x 0..100 y eje y con escala compartida
lo,hi=min(min(be),min(re_)), max(max(be),max(re_))
def path(vals,W=100.0,H=100.0):
    n=len(vals)-1
    pts=[]
    for i,v in enumerate(vals):
        x=i/n*W
        y=H-(v-lo)/(hi-lo)*H
        pts.append(f"{x:.2f},{y:.2f}")
    return " ".join(pts)
print('\nZERO_Y =',round(100-(0-lo)/(hi-lo)*100,2))
print('\nBT_PATH:'); print(path(be))
print('\nR_PATH:'); print(path(re_))
print('\nW/L real:', ''.join('W' if t['neto']>0 else ('s' if t['neto']>-50 else 'L') for t in R))
print('fechas real:', R[0]['fecha'],'->',R[-1]['fecha'])
