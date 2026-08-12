import random
random.seed(11)
RISK=150.0
def sim(wr, R, n_target, dd_max, trailing, obj=3000.0, runs=60000, tope_dia=2):
    ok=fail=inc=0
    for _ in range(runs):
        eq=0.0; peak=0.0; n=0
        while n<n_target:
            dia=0.0
            for _ in range(tope_dia):
                if n>=n_target: break
                g = RISK*R if random.random()<wr else -RISK
                eq+=g; dia+=g; n+=1
                if trailing: peak=max(peak,eq)
                if eq-(peak if trailing else 0) <= -dd_max: break
                if eq>=obj: break
                if dia<=-2*RISK: break
            base = peak if trailing else 0.0
            if eq-base<=-dd_max: fail+=1; break
            if eq>=obj: ok+=1; break
        else: inc+=1
    return ok/runs, fail/runs, inc/runs

print("Riesgo $150/op · tope 2 operaciones por dia · objetivo de la prueba +$3.000\n")
print(f"{'escenario':<40}{'llega a +3000':>14}{'revienta DD':>13}{'sigue vivo':>12}")
print('-'*79)
for lbl,wr,R in [('winrate 35,4% · R 1,87 (hoy, con C1)',0.354,1.87),
                 ('winrate 39,8% · R 1,87 (con C1+C4)',0.398,1.87),
                 ('winrate 42% · R 1,87 (optimista)',0.42,1.87)]:
    for dd,tr,dn in [(2000,True,'DD $2.000 trailing'),(2000,False,'DD $2.000 estatico'),(3000,True,'DD $3.000 trailing')]:
        o,f,i=sim(wr,R,60,dd,tr)
        print(f"  {lbl[:34]:<34}{dn:<22}{o*100:>6.1f}%{f*100:>12.1f}%{i*100:>11.1f}%")
    print()

print("\n### Solo la validacion: probabilidad de completar 50 operaciones sin reventar el DD")
print(f"{'winrate':<12}{'DD 2000 trailing':>20}{'DD 2000 estatico':>20}{'DD 3000 trailing':>20}")
for wr in [0.354,0.398,0.42]:
    fila=f"  {wr*100:>5.1f}%     "
    for dd,tr in [(2000,True),(2000,False),(3000,True)]:
        o,f,i=sim(wr,1.87,50,dd,tr,obj=1e9)   # sin objetivo: solo sobrevivir
        fila+=f"{(1-f)*100:>19.1f}%"
    print(fila)

print("\n### Cuanto capital propio haria falta para las mismas 50 ops sin riesgo de corte")
for wr in [0.354,0.398]:
    peor=[]
    for _ in range(20000):
        eq=0;mn=0
        for _ in range(50):
            eq+= RISK*1.87 if random.random()<wr else -RISK
            mn=min(mn,eq)
        peor.append(mn)
    peor.sort()
    print(f"  winrate {wr*100:.1f}%: drawdown p50 ${peor[len(peor)//2]:,.0f} | p90 ${peor[len(peor)//10]:,.0f} | p99 ${peor[len(peor)//100]:,.0f}")
