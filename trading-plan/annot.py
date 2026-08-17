from PIL import Image, ImageDraw, ImageFont

src = Image.open('giro_up/Captura de pantalla (25).png').convert('RGB')
# recorte de la operacion en M5
crop = src.crop((995, 250, 1580, 610))
S = 2.6
im = crop.resize((int(crop.width*S), int(crop.height*S)), Image.LANCZOS)
W, H = im.size
ov = Image.new('RGBA', (W, H), (0,0,0,0))
d = ImageDraw.Draw(ov)
def F(sz, bold=True):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''), sz)
def orig(x,y):  # original coords -> scaled crop coords
    return ((x-995)*S, (y-250)*S)

AC=(232,150,40); POS=(70,200,120); NEG=(210,70,60); WH=(240,240,240); BOX=(20,26,24)

# --- badge helper
def badge(x,y,n,col):
    r=18
    d.ellipse([x-r,y-r,x+r,y+r], fill=col+(255,), outline=(255,255,255,255), width=3)
    f=F(22); tb=d.textbbox((0,0),str(n),font=f)
    d.text((x-(tb[2]-tb[0])/2, y-(tb[3]-tb[1])/2-2), str(n), font=f, fill=(20,20,20,255))

def callout(x,y,txt,col,anchor='l',dy=0):
    f=F(21)
    tb=d.textbbox((0,0),txt,font=f); tw=tb[2]-tb[0]; th=tb[3]-tb[1]
    pad=7
    bx = x if anchor=='l' else x-tw-2*pad
    d.rounded_rectangle([bx, y-th-2*pad, bx+tw+2*pad, y+pad], radius=6, fill=BOX+(230,), outline=col+(255,), width=2)
    d.text((bx+pad, y-th-pad+dy), txt, font=f, fill=col+(255,))
    return bx

# coordenadas (original) de los hitos leidos de la captura
ex,ey = orig(1188,478)   # entrada 0
sx,sy = orig(1188,537)   # stop 30
tx,ty = orig(1188,356)   # target 60
bx0,by0 = orig(1012,424) # caja barrido (esq sup izq)
bx1,by1 = orig(1122,592) # caja barrido (esq inf der)

# 1 · barrido: resaltar caja y bracket
d.rectangle([bx0,by0,bx1,by1], outline=NEG+(255,), width=4)
badge(bx0+22, by0+22, 1, NEG)
callout(bx0-6, by0-14, '1 · Barrido del mínimo de Europa + mecha de rechazo', NEG, 'l')

# 2 · reingreso (flecha desde la caja hacia arriba-derecha)
rx,ry = orig(1095,455)
ax,ay = orig(1150,430)
d.line([ (bx1, by0+ (by1-by0)*0.35), (ax,ay) ], fill=POS+(255,), width=4)
badge(ax, ay, 2, POS)
callout(ax+16, ay+6, '2 · Reingreso al rango', POS, 'l')

# 3·4·5 cluster de entrada -> bracket con leader
lx,ly = orig(1176,470)
d.line([(lx,ly),(lx, orig(1176,300)[1])], fill=WH+(220,), width=2)
callout(lx+10, orig(1176,300)[1]+2, '3 retroceso (vela roja) → 4 vela verde → 5 entrada al romper su máximo', WH, 'l')
badge(*orig(1170,455), 3, NEG)
badge(*orig(1183,462), 4, POS)
badge(ex, ey, 5, AC)

# niveles de la operacion
callout(tx+34, ty+8, 'TARGET  +60 tk  (2:1)', POS, 'l')
callout(ex+34, ey+8, 'ENTRADA  0', AC, 'l')
callout(sx+34, sy+8, 'STOP  −30 tk', NEG, 'l')

# titulo
tf=F(24)
d.rectangle([0,0,W,44], fill=(15,20,18,235))
d.text((14,9), 'GIRO+VC · 15/08/2026 · MCL · escenario B (ATR 0,598)  —  ejemplo de referencia', font=tf, fill=(235,235,235,255))

out = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
out.save('giro-ejemplo.png')
print('ok', out.size)
