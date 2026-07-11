# mi-primer-proyecto

Bot de trading para futuros Micro E-mini S&P 500 (MES) sobre NinjaTrader 8.

- Estrategia: cruce de medias móviles exponenciales (EMA) con gestión de riesgo
  (stop-loss/take-profit por operación, límite de pérdida diaria, límite de operaciones
  por día, ventana horaria de sesión).
- Implementación: `NinjaTrader/Strategies/EmaCrossoverMES.cs` (NinjaScript / C#).
- Instalación, configuración y checklist de seguridad antes de operar con dinero real:
  ver [`docs/SETUP.md`](docs/SETUP.md).

⚠️ Este bot puede ejecutar órdenes con dinero real. Leé `docs/SETUP.md` antes de conectarlo
a una cuenta real.
