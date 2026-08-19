// =====================================================================================
// GiroSystem — estrategia NinjaScript (NinjaTrader 8) del sistema auto-giro CL/MCL.
//
// Implementa lo validado en el backtest de Python (trading-plan/backtest, docs 10 y 11):
//   - niveles de sesión Asia / Europa / rango de apertura de NY (máx/mín del mismo día),
//   - GIRO+VC: manipulación (perfora el nivel) -> confirmación (1ª vela a favor) ->
//     entrada al romper su extremo, stop del escenario debajo del pivote, objetivo 2R,
//   - sizing por tabla ATR(14) M60 con riesgo configurable (default $50),
//   - topes: máx 2/día y −3R semanal; aplanado no-overnight 17:00 BA (20:00 UTC).
//
// IMPORTANTE — zona horaria: este código asume que las marcas de tiempo de las barras
// están en UTC. Configurá NinjaTrader en Tools > Options > General > Time zone = "(UTC)"
// para que Time[0] sea UTC y la lógica de sesiones coincida con el backtest.
//
// Estado: v1 para compilar y validar en Sim101. No fue compilado por su autor; esperá
// iterar sobre errores de compilación. Objetivo de la validación: que reproduzca el
// backtest de Python antes de confiar en él.
// =====================================================================================
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Indicators;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class GiroSystem : Strategy
    {
        // ---------------- Inputs ----------------
        [NinjaScriptProperty]
        [Range(1, double.MaxValue)]
        [Display(Name = "Riesgo por operación ($)", Order = 1, GroupName = "Parámetros")]
        public double RiskPerTrade { get; set; } = 50;

        [NinjaScriptProperty]
        [Range(0.5, 10)]
        [Display(Name = "Objetivo (R)", Order = 2, GroupName = "Parámetros")]
        public double TargetR { get; set; } = 2.0;

        [NinjaScriptProperty]
        [Range(1, 10)]
        [Display(Name = "Máx operaciones/día", Order = 3, GroupName = "Parámetros")]
        public int MaxTradesDay { get; set; } = 2;

        [NinjaScriptProperty]
        [Display(Name = "Tope semanal (R)", Order = 4, GroupName = "Parámetros")]
        public double WeeklyStopR { get; set; } = -3.0;

        // Valor del tick de MCL en dólares por contrato (Micro WTI = $1,00 por tick de 0,01).
        [NinjaScriptProperty]
        [Display(Name = "Valor tick MCL ($)", Order = 5, GroupName = "Parámetros")]
        public double TickValueMcl { get; set; } = 1.0;

        // ---------------- Estado interno ----------------
        private ATR atr60;

        // acumuladores de niveles de sesión (se resetean al inicio de cada sesión)
        private double asiaHi, asiaLo, euHi, euLo, nyorHi, nyorLo;
        private bool prevInAsia, prevInEu, prevInNyor;
        private bool asiaReady, euReady, nyorReady;

        // topes / estado de cuenta
        private DateTime curDay = DateTime.MinValue;
        private int curWeek = -1;
        private int tradesToday = 0;
        private double weekR = 0;
        private double entryRiskDollars = 0;   // riesgo $ de la operación abierta (para calcular R)
        private int lastCountedTrade = 0;       // cuántos trades ya contabilizamos en R

        private static readonly TimeZoneInfo Et =
            TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time");

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "GiroSystem";
                Description = "Sistema auto-giro CL/MCL sobre niveles de sesión (Asia/Europa/NY).";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;
                BarsRequiredToTrade = 20;
            }
            else if (State == State.Configure)
            {
                // serie secundaria de 60 min para el ATR
                AddDataSeries(BarsPeriodType.Minute, 60);
            }
            else if (State == State.DataLoaded)
            {
                atr60 = ATR(BarsArray[1], 14);
            }
        }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0) return;                 // operar sobre la serie de 5 min
            if (CurrentBars[0] < 20 || CurrentBars[1] < 14) return;

            DateTime tUtc = Time[0];                          // se asume UTC (ver cabecera)
            double h = tUtc.Hour + tUtc.Minute / 60.0;

            UpdateSessionLevels(tUtc, h);
            UpdateDayWeekState(tUtc);
            AccountRFromClosedTrades();

            // aplanado no-overnight 17:00 BA = 20:00 UTC
            if (h >= 20.0)
            {
                if (Position.MarketPosition != MarketPosition.Flat)
                    ExitLongOrShort("Aplanado");
                return;
            }

            // ventana del giro: 08:00–11:30 ET (apertura cash 09:00, −60/+150)
            DateTime tEt = TimeZoneInfo.ConvertTimeFromUtc(tUtc, Et);
            double etH = tEt.Hour + tEt.Minute / 60.0;
            bool inGiroWindow = etH >= 8.0 && etH <= 11.5;
            if (!inGiroWindow) return;

            // ya en posición o topes tocados → no buscar nuevas entradas
            if (Position.MarketPosition != MarketPosition.Flat) return;
            if (tradesToday >= MaxTradesDay) return;
            if (weekR <= WeeklyStopR) return;

            // escenario por ATR(14) M60 (escala plataforma = ATR$ * 1000)
            int stopTicks; int contracts;
            if (!ScenarioSizing(out stopTicks, out contracts)) return;

            // probar las tres fuentes en orden (Asia el más fuerte); NY-OR solo tras cerrar (14:00 UTC)
            if (asiaReady && TryGiro(asiaLo, asiaHi, stopTicks, contracts, "asia")) return;
            if (euReady && TryGiro(euLo, euHi, stopTicks, contracts, "europa")) return;
            if (nyorReady && h >= 14.0 && TryGiro(nyorLo, nyorHi, stopTicks, contracts, "nyor")) return;
        }

        // ---------- niveles de sesión (UTC): Asia 18:30–07:00, Europa 07:00–13:00, NY-OR 13:00–14:00 ----------
        private void UpdateSessionLevels(DateTime tUtc, double h)
        {
            bool inAsia = (h >= 18.5) || (h < 7.0);
            bool inEu = (h >= 7.0 && h < 13.0);
            bool inNyor = (h >= 13.0 && h < 14.0);

            if (inAsia && !prevInAsia) { asiaHi = High[0]; asiaLo = Low[0]; }
            else if (inAsia) { asiaHi = Math.Max(asiaHi, High[0]); asiaLo = Math.Min(asiaLo, Low[0]); }
            if (!inAsia && prevInAsia) asiaReady = true;      // Asia cerró → nivel listo

            if (inEu && !prevInEu) { euHi = High[0]; euLo = Low[0]; }
            else if (inEu) { euHi = Math.Max(euHi, High[0]); euLo = Math.Min(euLo, Low[0]); }
            if (!inEu && prevInEu) euReady = true;

            if (inNyor && !prevInNyor) { nyorHi = High[0]; nyorLo = Low[0]; }
            else if (inNyor) { nyorHi = Math.Max(nyorHi, High[0]); nyorLo = Math.Min(nyorLo, Low[0]); }
            if (!inNyor && prevInNyor) nyorReady = true;

            prevInAsia = inAsia; prevInEu = inEu; prevInNyor = inNyor;
        }

        private void UpdateDayWeekState(DateTime tUtc)
        {
            if (tUtc.Date != curDay)
            {
                curDay = tUtc.Date;
                tradesToday = 0;
                // niveles del día nuevo: se vuelven a marcar "listos" cuando cada sesión cierre
                asiaReady = euReady = nyorReady = false;
            }
            // clave de semana = fecha del lunes de esa semana (evita ISOWeek, ausente en .NET 4.8)
            DateTime monday = tUtc.Date.AddDays(-(((int)tUtc.DayOfWeek + 6) % 7));
            int wkKey = monday.Year * 10000 + monday.Month * 100 + monday.Day;
            if (wkKey != curWeek) { curWeek = wkKey; weekR = 0; }
        }

        // ---------- tabla ATR → stop del escenario + contratos por riesgo ----------
        private bool ScenarioSizing(out int stopTicks, out int contracts)
        {
            stopTicks = 0; contracts = 0;
            double u = atr60[0] * 1000.0;                     // escala plataforma
            if (u < 500) stopTicks = 15;
            else if (u < 1000) stopTicks = 30;
            else if (u < 1250) stopTicks = 50;
            else if (u < 1500) stopTicks = 75;
            else return false;                                 // atr ≥ 1500: no se opera
            // contratos MCL para ~RiskPerTrade (riesgo = stopTicks * valor tick * contratos)
            contracts = Math.Max(1, (int)Math.Round(RiskPerTrade / (stopTicks * TickValueMcl)));
            return true;
        }

        // ---------- detección del giro sobre un nivel; entra si hay señal ----------
        private bool TryGiro(double lo, double hi, int stopTicks, int contracts, string tag)
        {
            // alcista sobre el mínimo; corto espejo sobre el máximo
            for (int dir = 0; dir < 2; dir++)
            {
                bool isLong = dir == 0;
                double level = isLong ? lo : hi;

                // manipulación: perforación del nivel en las últimas 12 velas
                int manip = -1;
                for (int j = 1; j <= 12; j++)
                {
                    bool perf = isLong ? (Low[j] < level - TickSize) : (High[j] > level + TickSize);
                    if (perf && (manip < 0 || (isLong ? Low[j] < Low[manip] : High[j] > High[manip])))
                        manip = j;
                }
                if (manip < 0) continue;

                // confirmación: 1ª vela a favor entre la manipulación y ahora
                int trig = -1;
                for (int j = manip; j >= 1; j--)
                {
                    bool favor = isLong ? (Close[j] > Open[j]) : (Close[j] < Open[j]);
                    if (favor) { trig = j; break; }
                }
                if (trig < 0) continue;

                // ruptura del extremo de la vela de confirmación en la barra actual
                double brk = isLong ? High[trig] : Low[trig];
                bool broke = isLong ? (High[0] > brk) : (Low[0] < brk);
                if (!broke) continue;

                double entry = brk + (isLong ? TickSize : -TickSize);
                double dist = stopTicks * TickSize;
                double manipPx = isLong ? Low[manip] : High[manip];
                // el pivote (manipulación) debe caer dentro del stop del escenario (§1.3)
                double pivDist = isLong ? (entry - manipPx) : (manipPx - entry);
                if (pivDist > dist + 2 * TickSize) continue;

                // sizing por riesgo y bracket
                entryRiskDollars = stopTicks * TickValueMcl * contracts;
                SetStopLoss(CalculationMode.Ticks, stopTicks);
                SetProfitTarget(CalculationMode.Ticks, TargetR * stopTicks);
                if (isLong) EnterLong(contracts, "giro_" + tag);
                else EnterShort(contracts, "giro_" + tag);
                tradesToday++;
                return true;
            }
            return false;
        }

        private void ExitLongOrShort(string reason)
        {
            if (Position.MarketPosition == MarketPosition.Long) ExitLong(reason);
            else if (Position.MarketPosition == MarketPosition.Short) ExitShort(reason);
        }

        // ---------- contabilizar R de las operaciones cerradas para los topes ----------
        private void AccountRFromClosedTrades()
        {
            var trades = SystemPerformance.AllTrades;
            while (lastCountedTrade < trades.Count)
            {
                var t = trades[lastCountedTrade];
                double risk = entryRiskDollars > 0 ? entryRiskDollars : RiskPerTrade;
                double r = t.ProfitCurrency / risk;
                weekR += r;
                lastCountedTrade++;
            }
        }
    }
}
