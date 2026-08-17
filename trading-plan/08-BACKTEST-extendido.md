# Backtest sobre 2,5 años (dic-2023 → jul-2026)

Actualización de `06-BACKTEST-v0.md` con la muestra completa: 31 contratos mensuales de CL
empalmados, **112.427 barras M5**, período **dic-2023 → jul-2026**. Con este volumen los
resultados ya son defendibles. El hallazgo central: **el GIRO tiene un edge real y estable;
el gatillo de ESTRUC, no.**

## Hallazgo central — año por año

Es la prueba que separa un edge real de una casualidad de muestra: ¿se repite cada año?

### GIRO+VC sobre nivel de Europa (2R) — positivo TODOS los años

| Año | n | Winrate | R/trade | Profit factor |
|---|---|---|---|---|
| 2024 | 102 | 50 % | **+0,488** | 1,98 |
| 2025 | 169 | 41 % | **+0,243** | 1,41 |
| 2026 | 116 | 52 % | **+0,537** | 2,11 |
| **Total** | **392** | **47 %** | **+0,393** | **1,74** |

Positivo en los tres años completos, con PF 1,4–2,1. Es un edge **temporalmente estable**.

### ESTRUC+VC gatillo mecánico (2R) — depende del año

| Año | n | R/trade | PF |
|---|---|---|---|
| 2024 | 263 | **−0,134** | 0,81 |
| 2025 | 269 | +0,142 | 1,23 |
| 2026 | 228 | +0,073 | 1,11 |
| **Total** | **778** | **+0,025** | **1,04** |

Negativo en 2024, positivo después. **El gatillo de ESTRUC, solo, es breakeven y no confiable.**

## Lo que se cayó al sumar 2024 (era ruido)

- **Dirección:** en 13,5 meses los largos parecían mejores; en 2,5 años se dieron vuelta
  (cortos +0,105, largos −0,046). No es robusto → no operar por dirección.
- **Escenario A:** de +0,182 (13,5 m) a +0,048 (2,5 a). Se diluyó.
- **Filtro M60:** confirmado sin aporte (baseline +0,025 vs ema50 +0,013). Muerto.

Todo esto es exactamente lo que se esperaba de cortes hechos sobre muestras chicas: se evaporan
con más datos. El giro, en cambio, se **fortaleció**.

## Qué implica para el plan

1. **El GIRO es el setup fuerte, con evidencia dura.** El detector dispara ~392 giros vs los
   ~30 que se toman selectivamente; aun así la regla mecánica cruda es positiva todos los años.
   La selección discrecional se monta **encima** de un edge que ya existe.
2. **El gatillo de ESTRUC es breakeven.** La lectura discrecional podría salvarlo, pero la regla
   sola no tiene edge confiable. Material para revisar el peso de cada setup en el plan.

## Advertencias vigentes

- El detector del giro **sobre-dispara** vs la selección real; mide el edge mecánico, no la
  selección fina.
- Giro **solo sobre Europa** (falta el ⅓ sobre pivotes dinámicos).
- Datos con **huecos de segunda quincena** (contratos exportados a ~15 días) y festivos; no
  rompen el backtest pero reducen la cobertura.
- Modelo v0: stop pesimista intrabar, sin parciales. Un CL, un período macro (2024-2026).
- El split por año es robusto, pero un walk-forward estricto lo confirmaría aún mejor.

## Próximos pasos naturales

1. **Modelar parciales** (l1/l2/l3) para acercar el simulador a la gestión real.
2. **Giro sobre pivotes dinámicos** (el ⅓ faltante), si se decide que son intencionales.
3. **Régimen ESTRUC↔GIRO:** ahora con 2,5 años se puede empezar a testear si hay períodos que
   favorecen a cada uno.
