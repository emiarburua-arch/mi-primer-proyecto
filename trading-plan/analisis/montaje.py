from PIL import Image, ImageDraw
import numpy as np, json, re, os
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
caps={}
for f in os.listdir('caps'):
    m=re.match(r'(\d{1,2})-(\d{1,2})-(\d{2})',f)
    if m:
        d,mo,y=m.groups(); caps.setdefault(f"20{y}-{int(mo):02d}-{int(d):02d}",[]).append(f)

def lineas(m5,col,tol=70,minlen=140):
    d=np.abs(m5.astype(int)-np.array(col)).sum(2)<tol
    return [(y,int(d[y].sum()),int(np.argmax(d[y])),int(m5.shape[1]-np.argmax(d[y][::-1])))
            for y in range(700) if d[y].sum()>minlen]

def celda(f, trade, W=430, H=430):
    a=np.array(Image.open('caps/'+f).convert('RGB')); m5=a[:,:1740]
    ent=lineas(m5,(230,160,30)); stp=lineas(m5,(220,40,60))
    if not ent or not stp: return None
    ey=ent[0][0]; x0=ent[0][2]; x1=ent[0][3]
    sy=min(stp,key=lambda r:abs(r[0]-ey))[0]
    R=abs(sy-ey)
    if R<15: return None
    largo = sy>ey        # stop por debajo -> largo
    # ventana: 2,6R a favor y 1,4R en contra
    if largo: top=ey-int(2.6*R); bot=ey+int(1.4*R)
    else:     top=ey-int(1.4*R); bot=ey+int(2.6*R)
    xa=max(0,x0-int(R*1.2)); xb=min(1740, x1+int(R*3.5))
    im=Image.open('caps/'+f).convert('RGB').crop((xa,max(0,top),xb,min(1080,bot)))
    if not largo: im=im.transpose(Image.FLIP_TOP_BOTTOM)
    im=im.resize((W,H), Image.LANCZOS)
    # marcamos escala en R: entrada y niveles
    d=ImageDraw.Draw(im); h=im.size[1]; tot=2.6+1.4
    for mult,c in [(0,(255,190,60)),(1,(255,80,80)),(2,(90,230,150)),(2.5,(120,190,255))]:
        yy=int(h*(2.6-mult)/tot) if mult>=0 else 0
        if 0<=yy<h: d.line([(0,yy),(W,yy)], fill=c, width=1)
    return im, R, largo

cands=[]
for t in T:
    if t['fecha'] in caps and t['usd']<=0 and t['sym']=='MCL':
        r=celda(caps[t['fecha']][0], t)
        if r: cands.append((t,r[0],r[1],r[2]))
print('perdedoras MCL procesadas:', len(cands))
cols=4; rows=(len(cands)+cols-1)//cols; W=H=430; PAD=26
M=Image.new('RGB',(cols*W, rows*(H+PAD)),(16,20,20)); dr=ImageDraw.Draw(M)
for i,(t,im,R,largo) in enumerate(cands):
    cx=(i%cols)*W; cy=(i//cols)*(H+PAD)
    M.paste(im,(cx,cy+PAD))
    dr.text((cx+5,cy+7), f"{t['fecha']} {t['contratos']}c {'LARGO' if largo else 'CORTO(inv)'} {t['patron']} stop {abs(t['ticks'])//t['contratos']}tk  ${t['usd']:.0f}", fill=(235,235,235))
M.save('montaje_mcl.png'); print('montaje', M.size)
