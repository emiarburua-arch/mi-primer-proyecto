COM={'CL':5.32,'MCL':1.84}; TICK={'CL':10.0,'MCL':1.0}
def fila(sym,ct,stop,ratio):
    tv=TICK[sym]; c=COM[sym]*ct
    riesgo=stop*ct*tv; tgt=round(stop*ratio)
    gan=tgt*ct*tv-c; per=riesgo+c
    return riesgo, tgt, gan, per, gan/per, 1/(1+gan/per)*100, c

print("Objetivo: mismo riesgo en dolares en los 3 escenarios (~$150 = 1,5% de $10.000)\n")
for ratio in [2.0, 2.5]:
    print(f"{'='*86}\nRATIO {ratio}:1 BRUTO\n{'='*86}")
    print(f"  {'escenario':<26}{'stop':>7}{'target':>8}{'riesgo':>9}{'comis':>8}{'gana':>9}{'pierde':>9}{'R neto':>8}{'equil.':>8}")
    for lbl,sym,ct,stop in [('A · ATR bajo   CL 1c','CL',1,15),
                            ('B · ATR medio  MCL 5c','MCL',5,30),
                            ('C · ATR alto   MCL 3c','MCL',3,50),
                            ('D · ATR muy alto MCL 2c','MCL',2,75)]:
        r,tg,g,p,R,be,c=fila(sym,ct,stop,ratio)
        print(f"  {lbl:<26}{stop:>5}tk{tg:>6}tk{r:>9,.0f}{c:>8,.2f}{g:>9,.2f}{p:>9,.2f}{R:>8.2f}{be:>7.1f}%")
    print()

print("="*86)
print("QUE SIGNIFICA PARA VOS (winrate medido: 35,4%)")
print("="*86)
for ratio,Rn,be in [(2.0,1.87,34.8),(2.5,2.35,29.9)]:
    e=0.354*Rn*155-0.646*155
    print(f"  ratio {ratio}:1 -> R neto ~{Rn:.2f}, equilibrio ~{be:.1f}%, margen {35.4-be:+.1f} puntos"
          f" -> esperanza ${e:+.2f}/op = ${e*96:+,.0f} en 96 ops")
print("""
  El 2:1 bruto, despues de comisiones, deja apenas medio punto de margen.
  El 2,5:1 deja 5,5 puntos. Esa es la diferencia entre depender de que el
  winrate no baje ni un punto, y tener colchon para una mala racha.""")
