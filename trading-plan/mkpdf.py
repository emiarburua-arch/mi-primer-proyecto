import markdown, re, datetime

src = open('/home/user/mi-primer-proyecto/trading-plan/TPP-v2.md').read()

# quitar la linea de estado "en construccion/completo" del encabezado para el PDF final
src = re.sub(r'^> Estado:.*?\(§7\.1\)\.\n', '', src, flags=re.MULTILINE|re.DOTALL)
src = re.sub(r'\*\*Emiliano Arburua\*\* · CL / MCL · Metodología Ankora\nBasado en el TPP vigente.*?\n', '', src)
# quitar el blockquote [PENDIENTE de confirmar] -> convertirlo en nota mas suave ya esta como blockquote, lo dejamos

html_body = markdown.markdown(src, extensions=['tables','sane_lists','fenced_code'])

CSS = r'''
@page {
  size: A4;
  margin: 20mm 18mm 18mm 18mm;
  @bottom-center { content: counter(page) " / " counter(pages); }
}
:root{
  --ink:#16201d; --ink-2:#3c4a46; --muted:#6a7873;
  --line:#d6ddd9; --line-2:#c2cac6;
  --accent:#9a5b0c; --accent-soft:#f3ead9;
  --pos:#2a6349; --neg:#9e3226;
  --band:#eef2f0;
}
* { box-sizing:border-box; }
html { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
body{
  font-family:"Iowan Old Style","Palatino Linotype",Georgia,serif;
  color:var(--ink); font-size:10.3pt; line-height:1.5; margin:0;
}
.cover{
  text-align:left; border-bottom:2.5pt solid var(--ink); padding-bottom:14pt; margin-bottom:20pt;
}
.cover .kick{ font-family:"Helvetica Neue",Arial,sans-serif; font-size:8pt; letter-spacing:.22em;
  text-transform:uppercase; color:var(--accent); margin:0 0 8pt; }
.cover h1{ font-size:26pt; line-height:1.04; margin:0 0 6pt; letter-spacing:-.01em; }
.cover .sub{ font-family:"Helvetica Neue",Arial,sans-serif; font-size:9pt; color:var(--muted); margin:0; }

h1{ font-size:0; margin:0; } /* el # del md se ignora, usamos portada */
h2{
  font-family:"Helvetica Neue",Arial,sans-serif; font-size:13pt; letter-spacing:-.01em;
  color:var(--ink); border-bottom:1pt solid var(--line-2); padding-bottom:3pt;
  margin:20pt 0 9pt; break-after:avoid;
}
h3{ font-family:"Helvetica Neue",Arial,sans-serif; font-size:10.5pt; color:var(--accent);
  margin:13pt 0 5pt; break-after:avoid; }
h4{ font-family:"Helvetica Neue",Arial,sans-serif; font-size:10pt; color:var(--ink);
  margin:11pt 0 4pt; break-after:avoid; }
p{ margin:0 0 7pt; }
strong{ color:#0f1815; }
em{ color:var(--ink-2); }
ul,ol{ margin:0 0 8pt; padding-left:17pt; }
li{ margin:0 0 3pt; }
hr{ border:none; border-top:1pt solid var(--line); margin:16pt 0; }
a{ color:var(--accent); text-decoration:none; }

table{
  border-collapse:collapse; width:100%; margin:8pt 0 11pt; font-size:9pt;
  break-inside:avoid;
}
th,td{ border:0.5pt solid var(--line-2); padding:4pt 7pt; text-align:left; vertical-align:top; }
thead th strong, thead th em{ color:#fff; }
thead th{
  background:var(--ink); color:#fff; font-family:"Helvetica Neue",Arial,sans-serif;
  font-size:7.6pt; letter-spacing:.05em; text-transform:uppercase; font-weight:600;
}
tbody tr:nth-child(even){ background:var(--band); }
td:first-child, th:first-child{ }

code{ font-family:"SF Mono",Menlo,Consolas,monospace; font-size:8.6pt;
  background:var(--band); padding:0.5pt 3pt; border-radius:2pt; }
pre{
  background:#f6f3ec; border:0.5pt solid var(--line-2); border-left:2.5pt solid var(--accent);
  padding:8pt 11pt; margin:8pt 0 11pt; font-size:8.7pt; line-height:1.45;
  white-space:pre-wrap; break-inside:avoid;
}
pre code{ background:none; padding:0; }
blockquote{
  margin:9pt 0; padding:8pt 12pt; background:var(--accent-soft);
  border-left:2.5pt solid var(--accent); font-size:9pt;
}
blockquote p{ margin:0; }

h2, h3 { string-set: none; }
'''

doc = f'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<style>{CSS}</style></head><body>
<div class="cover">
  <p class="kick">Trading Plan Personal · versión 2</p>
  <h1>Sistema CL / MCL — Metodología Ankora</h1>
  <p class="sub">Emiliano Arburua · construido sobre el análisis de 97 operaciones reales
  (22/10/2025 – 26/06/2026) · {datetime.date.today().strftime("%d/%m/%Y")}</p>
</div>
{html_body}
</body></html>'''
import os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(HERE, 'plan.html')
pdf_path  = os.path.join(HERE, 'TPP-v2.pdf')
open(html_path, 'w').write(doc)
print('html generado,', len(doc), 'chars')

# Render a PDF con Chromium headless (pw-browsers)
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
subprocess.run([CHROME, '--headless', '--no-sandbox', '--disable-gpu',
    '--no-pdf-header-footer', '--print-to-pdf=' + pdf_path,
    'file://' + html_path], check=True, stderr=subprocess.DEVNULL)
print('PDF generado ->', pdf_path)
