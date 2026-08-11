import random
random.seed(7)
WIN, LOSS = 194.68, -105.32          # CL 1 contrato, neto de comision
OBJ, DD, DIA = 3000.0, 2000.0, 1100.0
OPS_DIA = 1.3

def run(wr, win=WIN, loss=LOSS, n=40000, maxdays=250):
    ok=fail=0
    for _ in range(n):
        eq=0.0; peak=0.0
        for d in range(maxdays):
            dia=0.0
            for _ in range(2):                       # tope 2 stops/dia
                r = win if random.random()<wr else loss
                eq+=r; dia+=r; peak=max(peak,eq)
                if eq-peak <= -DD: break
                if dia <= -min(DIA, 2*abs(loss)+1): break
                if eq>=OBJ: break
            if eq-peak<=-DD: fail+=1; break
            if eq>=OBJ: ok+=1; break
        else: fail+=1
    return ok/n

print("Probabilidad de superar la prueba (obj +$3.000, DD -$2.000), CL 1 contrato, R=1.85")
print(f"{'winrate':>10} {'P(pasar)':>10}")
for wr in [0.222,0.25,0.30,0.35,0.40,0.45,0.50,0.577]:
    print(f"{wr*100:>9.1f}% {run(wr)*100:>9.1f}%")

print("\nMismo sistema con riesgo a la mitad (2 MCL: stop ~$50, target ~$100 neto)")
for wr in [0.35,0.40,0.45,0.50]:
    print(f"{wr*100:>9.1f}% {run(wr,97.0,-52.7)*100:>9.1f}%")

print("\nEsperanza matematica por operacion segun winrate (R=1.85, riesgo $105):")
for wr in [0.222,0.30,0.35,0.40,0.45,0.50,0.577]:
    e=wr*WIN+(1-wr)*LOSS
    print(f"  WR {wr*100:>5.1f}%  ->  ${e:>7.2f}/op   ({e*1.3*21:>8,.0f} $/mes a 1,3 ops/dia)")

# cuantas ops para validar con secuencial
print("\nOperaciones necesarias para concluir (test de una cola, alfa=5%, potencia=80%) vs breakeven 35%:")
import math
for t in [0.42,0.45,0.50,0.55]:
    n=math.ceil((1.645*math.sqrt(.35*.65)+0.84*math.sqrt(t*(1-t)))**2/(t-.35)**2)
    print(f"   si el winrate verdadero fuese {t*100:.0f}%: ~{n} operaciones  (~{n/1.3/21:.1f} meses a 1,3 ops/dia)")
