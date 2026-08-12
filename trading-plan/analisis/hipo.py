import json, statistics as st
from collections import defaultdict
T=[t for t in json.load(open('beta.json')) if t['fecha'].startswith('202')]
T.sort(key=lambda t:(t['fecha'],t['hora'] or ''))
# stop planificado estimado: perdedoras = ticks reales; ganadoras = target/2 (si el 2:1 se respeto)
for t in T:
    tkc=abs(t['ticks'])/t['contratos']
    t['stop_est'] = tkc if t['usd']<=0 else tkc/2
    t['riesgo_est'] = t['stop_est']*t['contratos']*(10 if t['sym']=='CL' else 1)
L=[t for t in T if t['usd']<=0]; W=[t for t in T if t['usd']>0]

print("### TEST DE TU HIPOTESIS: ¿los stops eran mas grandes en las perdedoras?")
for lbl,f in [('CL',lambda t:t['sym']=='CL'),('MCL',lambda t:t['sym']=='MCL'),('todas',lambda t:True)]:
    lw=[t['stop_est'] for t in W if f(t)]; ll=[t['stop_est'] for t in L if f(t)]
    if not lw or not ll: continue
    print(f"  {lbl:<6} stop medio en GANADORAS {st.mean(lw):>6.1f} tk  |  en PERDEDORAS {st.mean(ll):>6.1f} tk"
          f"   -> {'perdedoras con stop MAYOR' if st.mean(ll)>st.mean(lw) else 'ganadoras con stop mayor'}"
          f" ({st.mean(ll)/st.mean(lw):.2f}x)")

print("\n### Riesgo en DOLARES: ¿se arriesgo mas en las perdedoras?")
for lbl,f in [('CL',lambda t:t['sym']=='CL'),('MCL',lambda t:t['sym']=='MCL'),('todas',lambda t:True)]:
    rw=[t['riesgo_est'] for t in W if f(t)]; rl=[abs(t['usd']) for t in L if f(t)]
    if not rw or not rl: continue
    print(f"  {lbl:<6} riesgo medio en GANADORAS ${st.mean(rw):>7,.2f}  |  en PERDEDORAS ${st.mean(rl):>7,.2f}"
          f"   ratio {st.mean(rl)/st.mean(rw):.2f}")

print("\n### Dispersion del riesgo en dolares (lo que tu propuesta quiere eliminar)")
r=[abs(t['usd']) for t in L]
print(f"  perdedoras: media ${st.mean(r):,.2f} | desv ${st.pstdev(r):,.2f} | CV {st.pstdev(r)/st.mean(r)*100:.0f}%")
rw=[t['riesgo_est'] for t in W]
print(f"  ganadoras (riesgo estimado): media ${st.mean(rw):,.2f} | desv ${st.pstdev(rw):,.2f} | CV {st.pstdev(rw)/st.mean(rw)*100:.0f}%")

print("\n### DONDE SE PIERDE DE VERDAD: ganadoras que no llegaron a 2R")
RISK=st.mean(r)
corta=[t for t in W if t['usd'] < 1.75*t['riesgo_est']]
print(f"  ganadoras que cobraron menos de 1,75x su propio riesgo: {len(corta)} de {len(W)}")
print(f"  {'fecha':<12}{'sym':<5}{'ct':>3} {'stop est':>9} {'riesgo':>9} {'cobrado':>9} {'x su riesgo':>12}")
for t in sorted(corta,key=lambda x:x['usd']/x['riesgo_est']):
    print(f"  {t['fecha']:<12}{t['sym']:<5}{t['contratos']:>3} {t['stop_est']:>8.0f}tk ${t['riesgo_est']:>8,.2f} ${t['usd']:>8,.2f} {t['usd']/t['riesgo_est']:>11.2f}x")
falta=sum(2*t['riesgo_est']-t['usd'] for t in corta)
print(f"\n  Si esas {len(corta)} hubiesen cobrado 2x su propio riesgo: +${falta:,.2f}")
print(f"  P&L pasaria de ${sum(t['usd'] for t in T):,.2f} a ${sum(t['usd'] for t in T)+falta:,.2f}")

print("\n### Simulacion de TU PROPUESTA: 3 stops fijos, riesgo constante de $150")
print("  (mismo winrate y misma secuencia, pero cada ganadora cobra 2x150 y cada perdedora pierde 150)")
for wr_lbl,ops in [('todas las 96',T)]:
    w=len([t for t in ops if t['usd']>0]); n=len(ops)
    pnl=w*300-(n-w)*150
    print(f"  {wr_lbl}: {w}W/{n-w}L  ->  ${pnl:,.2f}   (real: ${sum(t['usd'] for t in ops):,.2f})")
print("\n  Sensibilidad: cuanto tolera esa configuracion")
for wr in [0.30,0.3333,0.354,0.36,0.40]:
    e=wr*300-(1-wr)*150
    print(f"    winrate {wr*100:>5.1f}% -> esperanza ${e:>7,.2f}/op  ->  ${e*96:>9,.2f} en 96 operaciones")
