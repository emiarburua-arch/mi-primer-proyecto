#region Using declarations
using System;
using NinjaTrader.Cbi;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Indicators;
using NinjaTrader.NinjaScript.Strategies;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// EMA crossover trend-following strategy for Micro E-mini S&amp;P 500 futures (MES).
    /// Enters long when the fast EMA crosses above the slow EMA, short on the reverse cross.
    /// Includes hard risk controls: per-trade stop/target, daily loss limit, daily trade
    /// limit, trading-session window and forced flatten at session end.
    /// </summary>
    public class EmaCrossoverMES : Strategy
    {
        private EMA fastEma;
        private EMA slowEma;

        private double dailyRealizedPnL;
        private int dailyTradeCount;
        private bool tradingHaltedForDay;
        private DateTime currentSessionDate;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "EMA crossover trend strategy for Micro E-mini S&P 500 (MES) with built-in risk controls.";
                Name = "EmaCrossoverMES";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsFillLimitOnTouch = false;
                MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
                OrderFillResolution = OrderFillResolution.Standard;
                Slippage = 0;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Gtc;
                TraceOrders = false;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 30;
                IsInstantiatedOnEachOptimizationIteration = true;

                // --- Strategy parameters (tune these in NinjaTrader before going live) ---
                FastEmaPeriod = 9;
                SlowEmaPeriod = 21;
                Contracts = 1;
                StopLossTicks = 40;      // 40 ticks = 10 points on MES (tick = 0.25)
                TakeProfitTicks = 80;    // 80 ticks = 20 points on MES
                MaxDailyLossDollars = 500;
                MaxDailyTrades = 10;
                SessionStartHHMM = 930;  // 09:30
                SessionEndHHMM = 1555;   // 15:55, leaves room to flatten before the close
            }
            else if (State == State.Configure)
            {
            }
            else if (State == State.DataLoaded)
            {
                fastEma = EMA(FastEmaPeriod);
                slowEma = EMA(SlowEmaPeriod);

                AddChartIndicator(fastEma);
                AddChartIndicator(slowEma);
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < BarsRequiredToTrade)
                return;

            // Reset daily counters at the start of each new session.
            if (Bars.IsFirstBarOfSession)
            {
                dailyRealizedPnL = 0;
                dailyTradeCount = 0;
                tradingHaltedForDay = false;
                currentSessionDate = Time[0].Date;
            }

            int nowHHMM = Time[0].Hour * 100 + Time[0].Minute;
            bool withinSession = nowHHMM >= SessionStartHHMM && nowHHMM < SessionEndHHMM;

            // Force-flatten outside the trading window or if the daily loss limit was hit.
            if (!withinSession || tradingHaltedForDay)
            {
                if (Position.MarketPosition != MarketPosition.Flat)
                    ExitAllPositions("SessionOrRiskFlatten");
                return;
            }

            // Kill switch: stop trading for the day once the loss limit is breached.
            double openPnL = Position.MarketPosition == MarketPosition.Flat
                ? 0
                : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);

            if (dailyRealizedPnL + openPnL <= -Math.Abs(MaxDailyLossDollars))
            {
                Print(string.Format("{0}: Daily loss limit hit ({1:C}). Flattening and halting trading for the day.",
                    Time[0], dailyRealizedPnL + openPnL));
                tradingHaltedForDay = true;
                if (Position.MarketPosition != MarketPosition.Flat)
                    ExitAllPositions("DailyLossLimit");
                return;
            }

            if (dailyTradeCount >= MaxDailyTrades)
                return;

            bool crossedUp = CrossAbove(fastEma, slowEma, 1);
            bool crossedDown = CrossBelow(fastEma, slowEma, 1);

            if (crossedUp && Position.MarketPosition != MarketPosition.Long)
            {
                if (Position.MarketPosition == MarketPosition.Short)
                    ExitShort("ReverseToLong", "");

                EnterLong(Contracts, "EmaCrossLong");
                SetStopLoss("EmaCrossLong", CalculationMode.Ticks, StopLossTicks, false);
                SetProfitTarget("EmaCrossLong", CalculationMode.Ticks, TakeProfitTicks);
            }
            else if (crossedDown && Position.MarketPosition != MarketPosition.Short)
            {
                if (Position.MarketPosition == MarketPosition.Long)
                    ExitLong("ReverseToShort", "");

                EnterShort(Contracts, "EmaCrossShort");
                SetStopLoss("EmaCrossShort", CalculationMode.Ticks, StopLossTicks, false);
                SetProfitTarget("EmaCrossShort", CalculationMode.Ticks, TakeProfitTicks);
            }
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price,
            int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order == null || execution.Order.OrderState != OrderState.Filled)
                return;

            // Count a completed round trip (an exit fill) as one trade for the daily trade cap.
            if (execution.Order.Name != null && execution.Order.Name.StartsWith("Enter"))
                return;

            if (SystemPerformance.AllTrades.Count > 0)
            {
                var lastTrade = SystemPerformance.AllTrades[SystemPerformance.AllTrades.Count - 1];
                if (lastTrade.Exit.Time == time)
                {
                    dailyRealizedPnL += lastTrade.ProfitCurrency;
                    dailyTradeCount++;
                }
            }
        }

        #region Properties

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Fast EMA Period", Order = 1, GroupName = "Strategy Parameters")]
        public int FastEmaPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(2, int.MaxValue)]
        [Display(Name = "Slow EMA Period", Order = 2, GroupName = "Strategy Parameters")]
        public int SlowEmaPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Contracts", Order = 3, GroupName = "Strategy Parameters")]
        public int Contracts { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Stop Loss (ticks)", Order = 4, GroupName = "Risk Management")]
        public int StopLossTicks { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Take Profit (ticks)", Order = 5, GroupName = "Risk Management")]
        public int TakeProfitTicks { get; set; }

        [NinjaScriptProperty]
        [Range(1, double.MaxValue)]
        [Display(Name = "Max Daily Loss ($)", Order = 6, GroupName = "Risk Management")]
        public double MaxDailyLossDollars { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Max Trades Per Day", Order = 7, GroupName = "Risk Management")]
        public int MaxDailyTrades { get; set; }

        [NinjaScriptProperty]
        [Range(0, 2359)]
        [Display(Name = "Session Start (HHMM)", Order = 8, GroupName = "Session")]
        public int SessionStartHHMM { get; set; }

        [NinjaScriptProperty]
        [Range(0, 2359)]
        [Display(Name = "Session End (HHMM)", Order = 9, GroupName = "Session")]
        public int SessionEndHHMM { get; set; }

        #endregion
    }
}
