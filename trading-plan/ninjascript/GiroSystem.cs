// =====================================================================================
// GiroSystem — estrategia NinjaScript (NinjaTrader 8) del sistema auto-giro CL/MCL.
//
// Implementa lo validado en el backtest de Python (trading-plan/backtest, docs 10 y 11):
//   - niveles de sesión Asia / Europa / rango de apertura de NY (máx/mín del mismo día),
//   - GIRO+VC: manipulación (perfora el nivel) -> confirmación (1ª vela a favor) ->
//     ENTRADA CON ORDEN STOP EN EL NIVEL DE RUPTURA (no a mercado; esto es clave para el edge),
//   - stop del escenario debajo del pivote, objetivo 2R,
//   - sizing por tabla ATR(14) M60 con riesgo configurable (default $50),
//   - topes: máx 2/día y −3R semanal; aplanado no-overnight 17:00 BA (20:00 UTC).
//
// v2 — La entrada ahora es una orden STOP que descansa en el nivel de ruptura. En v1 se
// entraba a mercado al cierre de la vela, lo que entra tarde y se come todo el edge
// (backtest: entrada límite +0,63 R/trade vs entrada a mercado +0,04 R/trade).
//
// IMPORTANTE — zona horaria: se asume que las marcas de tiempo están en UTC. Configurá
// NinjaTrader en Tools > Options > General > Time zone = "(UTC)".
//
// Estado: para compilar y validar en Sim101. La gestión de órdenes (arme/cancelación) es
// lo más delicado; esperá iterar en Sim.
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

        [NinjaScriptProperty]
        [Display(Name = "Valor tick MCL ($)", Order = 5, GroupName = "Parámetros")]
        public double TickValueMcl { get; set; } = 1.0;

        [NinjaScriptProperty]
        [Range(1, 12)]
        [Display(Name = "Vida de la orden (velas)", Order = 6, GroupName = "Parámetros")]
        public int OrderLifeBars { get; set; } = 3;

        // ---------------- Estado interno ----------------
        private ATR atr60;

        private double asiaHi, asiaLo, euHi, euLo, nyorHi, nyorLo;
        private bool prevInAsia, prevInEu, prevInNyor;
        private bool asiaReady, euReady, nyorReady;

        private DateTime curDay = DateTime.MinValue;
        private int curWeek = -1;
        private int tradesToday = 0;
        private double weekR = 0;
        private double entryRiskDollars = 0;
        private int lastCountedTrade = 0;

        // orden de entrada pendiente (stop en el nivel de ruptura)
        private Order giroEntryOrder = null;
        private int armBar = -1;
        private bool armLong = false;
        private double armManip = 0;

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
                AddDataSeries(BarsPeriodType.Minute, 60);   // serie de 60 min para el ATR
            }
            else if (State == State.DataLoaded)
            {
                atr60 = ATR(BarsArray[1], 14);
            }
        }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0) return;
            if (CurrentBars[0] < 20 || CurrentBars[1] < 14) return;

            DateTime tUtc = Time[0];
            double h = tUtc.Hour + tUtc.Minute / 60.0;

            UpdateSessionLevels(tUtc, h);
            UpdateDayWeekState(tUtc);
            AccountRFromClosedTrades();

            // aplanado no-overnight 17:00 BA = 20:00 UTC
            if (h >= 20.0)
            {
                CancelPendingEntry();
                if (Position.MarketPosition != MarketPosition.Flat) ExitLongOrShort("Aplanado");
                return;
            }

            DateTime tEt = TimeZoneInfo.ConvertTimeFromUtc(tUtc, Et);
            double etH = tEt.Hour + tEt.Minute / 60.0;
            bool inGiroWindow = etH >= 8.0 && etH <= 11.5;

            // si hay una entrada pendiente, gestionar su cancelación
            if (giroEntryOrder != null)
            {
                bool invalidated = armLong ? Close[0] < armManip : Close[0] > armManip;
                if (!inGiroWindow || (CurrentBar - armBar) > OrderLifeBars || invalidated)
                    CancelPendingEntry();
                return;   // no armar otra mientras haya una pendiente
            }

            if (!inGiroWindow) return;
            if (Position.MarketPosition != MarketPosition.Flat) return;
            if (tradesToday >= MaxTradesDay) return;
            if (weekR <= WeeklyStopR) return;

            int stopTicks, contracts;
            if (!ScenarioSizing(out stopTicks, out contracts)) return;

            // probar las tres fuentes en orden (Asia el más fuerte); NY-OR solo tras cerrar (14:00 UTC)
            if (asiaReady && ArmGiro(asiaLo, asiaHi, stopTicks, contracts, "asia")) return;
            if (euReady && ArmGiro(euLo, euHi, stopTicks, contracts, "europa")) return;
            if (nyorReady && h >= 14.0) ArmGiro(nyorLo, nyorHi, stopTicks, contracts, "nyor");
        }

        // ---------- niveles de sesión (UTC) ----------
        private void UpdateSessionLevels(DateTime tUtc, double h)
        {
            bool inAsia = (h >= 18.5) || (h < 7.0);
            bool inEu = (h >= 7.0 && h < 13.0);
            bool inNyor = (h >= 13.0 && h < 14.0);

            if (inAsia && !prevInAsia) { asiaHi = High[0]; asiaLo = Low[0]; }
            else if (inAsia) { asiaHi = Math.Max(asiaHi, High[0]); asiaLo = Math.Min(asiaLo, Low[0]); }
            if (!inAsia && prevInAsia) asiaReady = true;

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
                asiaReady = euReady = nyorReady = false;
            }
            DateTime monday = tUtc.Date.AddDays(-(((int)tUtc.DayOfWeek + 6) % 7));
            int wkKey = monday.Year * 10000 + monday.Month * 100 + monday.Day;
            if (wkKey != curWeek) { curWeek = wkKey; weekR = 0; }
        }

        private bool ScenarioSizing(out int stopTicks, out int contracts)
        {
            stopTicks = 0; contracts = 0;
            double u = atr60[0] * 1000.0;
            if (u < 500) stopTicks = 15;
            else if (u < 1000) stopTicks = 30;
            else if (u < 1250) stopTicks = 50;
            else if (u < 1500) stopTicks = 75;
            else return false;
            contracts = Math.Max(1, (int)Math.Round(RiskPerTrade / (stopTicks * TickValueMcl)));
            return true;
        }

        // ---------- arma una orden STOP de entrada en el nivel de ruptura ----------
        private bool ArmGiro(double lo, double hi, int stopTicks, int contracts, string tag)
        {
            for (int dir = 0; dir < 2; dir++)
            {
                bool isLong = dir == 0;
                double level = isLong ? lo : hi;

                // manipulación: perforación más extrema en las últimas 12 velas
                int manipK = -1;
                for (int k = 1; k <= 12; k++)
                {
                    bool perf = isLong ? (Low[k] < level - TickSize) : (High[k] > level + TickSize);
                    if (perf && (manipK < 0 || (isLong ? Low[k] < Low[manipK] : High[k] > High[manipK])))
                        manipK = k;
                }
                if (manipK < 0) continue;

                // confirmación: 1ª vela a favor después de la manipulación (más reciente que manipK)
                int trigK = -1;
                for (int k = manipK - 1; k >= 0; k--)
                {
                    bool favor = isLong ? (Close[k] > Open[k]) : (Close[k] < Open[k]);
                    if (favor) { trigK = k; break; }
                }
                if (trigK < 0) continue;

                double brk = isLong ? High[trigK] : Low[trigK];
                // que todavía NO haya sido rota (para entrar EN el nivel, no tarde)
                bool broken = false;
                for (int k = trigK - 1; k >= 0; k--)
                    if (isLong ? High[k] > brk : Low[k] < brk) { broken = true; break; }
                if (broken) continue;

                double entry = brk + (isLong ? TickSize : -TickSize);
                double dist = stopTicks * TickSize;
                double manipPx = isLong ? Low[manipK] : High[manipK];
                double pivDist = isLong ? (entry - manipPx) : (manipPx - entry);
                if (pivDist > dist + 2 * TickSize) continue;

                // arma la orden stop en el nivel + bracket (stop/target se adjuntan al llenarse)
                entryRiskDollars = stopTicks * TickValueMcl * contracts;
                SetStopLoss(CalculationMode.Ticks, stopTicks);
                SetProfitTarget(CalculationMode.Ticks, TargetR * stopTicks);
                giroEntryOrder = isLong
                    ? EnterLongStopMarket(0, true, contracts, entry, "giro_" + tag)
                    : EnterShortStopMarket(0, true, contracts, entry, "giro_" + tag);
                armBar = CurrentBar;
                armLong = isLong;
                armManip = manipPx;
                return true;
            }
            return false;
        }

        private void CancelPendingEntry()
        {
            if (giroEntryOrder != null)
            {
                CancelOrder(giroEntryOrder);
                giroEntryOrder = null;
            }
        }

        private void ExitLongOrShort(string reason)
        {
            if (Position.MarketPosition == MarketPosition.Long) ExitLong(reason);
            else if (Position.MarketPosition == MarketPosition.Short) ExitShort(reason);
        }

        // ---------- ciclo de vida de la orden de entrada ----------
        protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice,
            int quantity, int filled, double averageFillPrice, OrderState orderState,
            DateTime time, ErrorCode error, string nativeError)
        {
            if (giroEntryOrder != null && order == giroEntryOrder)
            {
                if (orderState == OrderState.Filled) { tradesToday++; giroEntryOrder = null; }
                else if (orderState == OrderState.Cancelled || orderState == OrderState.Rejected)
                    giroEntryOrder = null;
            }
        }

        // ---------- contabilizar R de operaciones cerradas para los topes ----------
        private void AccountRFromClosedTrades()
        {
            var trades = SystemPerformance.AllTrades;
            while (lastCountedTrade < trades.Count)
            {
                var t = trades[lastCountedTrade];
                double risk = entryRiskDollars > 0 ? entryRiskDollars : RiskPerTrade;
                weekR += t.ProfitCurrency / risk;
                lastCountedTrade++;
            }
        }
    }
}
