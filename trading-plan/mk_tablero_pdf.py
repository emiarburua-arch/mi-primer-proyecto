#!/usr/bin/env python3
"""Genera Tablero-Operativo-A4.pdf (A4 apaisado, una hoja) a partir de tablero.html.
Requiere: chromium (pw-browsers), pillow, reportlab.
Uso: python3 mk_tablero_pdf.py"""
import subprocess, os
from PIL import Image, ImageOps
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
CHROME="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# 1) variante para imagen: fondo blanco
src=open(os.path.join(HERE,'tablero.html')).read()
src=src.replace('</style>','\n  :root{ --ground:#ffffff; }\n  body{ padding:14px 18px; }\n  .sheet{ gap:9px; }\n</style>')
open(os.path.join(HERE,'tablero_img.html'),'w').write(src)

# 2) render 2x
subprocess.run([CHROME,'--headless','--no-sandbox','--disable-gpu','--hide-scrollbars',
  '--force-device-scale-factor=2','--window-size=1200,860',
  '--screenshot='+os.path.join(HERE,'tablero_hi.png'),
  'file://'+os.path.join(HERE,'tablero_img.html')], check=True, stderr=subprocess.DEVNULL)

# 3) autocrop + margen blanco
im=Image.open(os.path.join(HERE,'tablero_hi.png')).convert('RGB')
a=np.array(im.convert('L'))
rows=np.where((a<250).any(1))[0]; cols=np.where((a<250).any(0))[0]
im=im.crop((cols.min(),rows.min(),cols.max()+1,rows.max()+1))
im=ImageOps.expand(im,border=24,fill='white')
card=os.path.join(HERE,'tablero_card.png'); im.save(card)

# 4) A4 apaisado
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
iw,ih=im.size; W,H=landscape(A4); m=16
sc=min((W-2*m)/iw,(H-2*m)/ih); w,h=iw*sc,ih*sc
c=canvas.Canvas(os.path.join(HERE,'Tablero-Operativo-A4.pdf'), pagesize=landscape(A4))
c.setTitle('Tablero Operativo CL/MCL - Ankora')
c.drawImage(ImageReader(card),(W-w)/2,(H-h)/2,w,h,preserveAspectRatio=True,mask='auto')
c.showPage(); c.save()
print('OK -> Tablero-Operativo-A4.pdf')
