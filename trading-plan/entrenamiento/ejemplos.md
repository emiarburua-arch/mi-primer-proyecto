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
