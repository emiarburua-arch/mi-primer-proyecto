# Ejemplos de calibración – Manipulación (regla 8.1)

Valores **estimados desde capturas** (error ±10–20 pts en NQ). Se confirman con datos exportados.
Profundidad, retroceso y giro se expresan en % del rango de referencia.

| # | Captura | Instrumento | Nivel | Rango ref. | Profundidad | Perforaciones | Giro (alejamiento desde el nivel) | Veredicto trader |
|---|---|---|---|---|---|---|---|---|
| C1 | `c1_crudo_manip_max_europa_valida.png` | Crudo | Máx. Europa ~83,75 | ~2,08 | ~8% | 1 (oscila pegado al nivel) | ~24% en 2–3 velas, con volumen | ✅ válida |
| C2 | `c2_nq_manip_min_europa_2perf_valida.png` | NQ | Mín. Europa ~27600 | ~445 | ~18% | 2 (rebote intermedio ~9–12%) | ~34% en ~8 velas | ✅ válida |
| C3 | `c3_nq_20261109_max_sesion_usa_invalida.png` | NQ | Máx. sesión USA ~28010 | ~720 | ~16% | 4+ | ninguno: ~5% en 12 velas, lateral, poco volumen | ❌ no válida |
| C4a | `c4_nq_manip_max_y_min_europa_validas.png` | NQ | Máx. Europa ~28045 | ~445 | ~10% | 1 | ~31% en ~6 velas, con volumen | ✅ válida |
| C4b | (misma captura, mismo día que C2) | NQ | Mín. Europa ~27600 | ~445 | ~18% | 2 | ~34% en ~8 velas | ✅ válida |

## Aprendizajes

- Oscilar pegado al nivel = **una sola perforación** (C1).
- La **profundidad** sola no separa casos (C2 18% válida, C3 16% inválida) → límite fijado en 20% como filtro grueso.
- Lo que separa válidas de inválidas es el **giro claro**: en las válidas el precio se aleja ≥ ~24% del rango en ≤ 8
  velas de 5m; en la inválida, ~5% en 12 velas.

---

# Ejemplos de calibración – Ejecución

| # | Captura | Tipo | Secuencia leída (estimada) | Stop / Target | Resultado | Veredicto trader |
|---|---|---|---|---|---|---|
| C5 | `c5_mnq_trade_giro_valido.png` | Giro (tipo 1) sobre mín. Europa ~27600 (mismo día que C2/C4) | Perforación 1 (~27519) → reingreso fuerte (~27650) → retroceso = perforación 2 (~27590) → primera vela verde (máx. ~27634) → confirmación rompe su máximo → limit ~27633 | 300 ticks (~27558) / 600 ticks (~27783), 1 micro | Target alcanzado (+2R) | ✅ válido (horario ignorado) |
| C6 | `c6_mnq_estructura_y_pivote_stop.png` | Mismo trade que C5, con la estructura marcada | Bajista: ~27950 → ~27740 → ~27850 → ~27620 → ~27700 → ~27525. Alcista: ~27640 → **pivote ~27580–27590 (zona 13:05–13:35, cubierto por el stop)** → ~27760 → ~27690 → ~27790 → ~27690 → ~27830 → ~27775 → ~27910 | Stop 300 ticks cubre el pivote; 150 ticks (~27595) no lo cubriría | — | ✅ |
| C7 | `c7_crudo_stop_no_cubre_descartado.png` | Crudo (solo ilustrativo) | Para cubrir el mínimo previo (~79,05) desde la entrada (~79,55) hacía falta un stop de 60 ticks; el stop máximo en CL es 30 ticks | 30 ticks no cubre el pivote | — | ❌ se descarta |

## Aprendizajes de ejecución

- El retroceso previo a la entrada de giro puede ser la propia segunda perforación de la manipulación (C5).
- El trader marca **swings significativos**, no cada micro-pivote: los retrocesos que cuenta son de ~55–115 pts;
  las oscilaciones de ~20–30 pts dentro de una zona (13:05–13:35) las toma como **un solo pivote** (C6).
  → La regla de 2 velas a cada lado (8.2) probablemente marca pivotes de más. A calibrar con datos.
