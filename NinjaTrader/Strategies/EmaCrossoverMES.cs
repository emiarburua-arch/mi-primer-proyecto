#region Using declarations
using System;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Indicators;
using NinjaTrader.NinjaScript.Strategies;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// Short-term (scalping) EMA-crossover trend strategy for Micro E-mini S&amp;P 500 (MES),
    /// designed for a 1-minute chart during the first two hours after the US cash open.
    ///
    /// A trade is only taken when three conditions agree:
    ///   1. Trend direction: fast EMA crosses the slow EMA.
    ///   2. Trend strength:  ADX is above <see cref="TrendAdxThreshold"/> (defines "trend").
    ///   3. Volatility:      ATR is inside [MinAtrTicks, MaxAtrTicks] (defines "volatility").
    ///
    /// Risk is managed with ATR-based stop/target, break-even, a time stop, a per-day loss
    /// limit, a trade-count cap, a consecutive-loss cap, a cooldown between trades and a
    /// forced flatten outside the trading window.
    /// </summary>
    public class EmaCrossoverMES : Strategy
    {
        private EMA fastEma;
        private EMA slowEma;
        private ADX adx;
        private ATR atr;

        private double dailyRealizedPnL;
        private int dailyTradeCount;
        private int consecutiveLosses;
        private bool tradingHaltedForDay;

        private int entryBar;
        private int lastExitBar;
        private bool movedToBreakeven;
        private MarketPosition previousPosition;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Short-term EMA-crossover trend scalper for MES (1-min, first 2 hours after US open) with ADX/ATR filters and layered risk controls.";
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

                // --- Trend / signal parameters ---
                FastEmaPeriod = 8;
                SlowEmaPeriod = 21;
                Contracts = 1;

                // --- Trend-strength definition (this is what "a trend" means) ---
                TrendAdxPeriod = 14;
                TrendAdxThreshold = 20;         // ADX above this = trending; below = chop, no trade
                MinEmaSeparationAtr = 0.10;     // EMAs must be at least this * ATR apart

                // --- Volatility definition / filter ---
                AtrPeriod = 14;
                MinAtrTicks = 4;                // ~1 MES point; below this the market is too dead
                MaxAtrTicks = 40;               // ~10 MES points; above this it is too erratic to scalp

                // --- ATR-based exits ---
                StopAtrMultiple = 1.0;
                TargetAtrMultiple = 1.5;
                BreakevenTriggerAtrMultiple = 1.0;  // move stop to entry after +1 ATR (0 = disabled)
                MaxBarsInTrade = 15;                // time stop: exit after N bars if neither stop nor target hit

                // --- Daily risk controls ---
                MaxDailyLossDollars = 300;
                MaxDailyTrades = 15;
                MaxConsecutiveLosses = 3;
                CooldownBars = 1;                   // bars to wait after an exit before re-entering

                // --- Session window (first 2 hours after US cash open) ---
                SessionStartHHMM = 930;             // 09:30
                SessionEndHHMM = 1130;              // 11:30
            }
            else if (State == State.Configure)
            {
            }
            else if (State == State.DataLoaded)
            {
                fastEma = EMA(FastEmaPeriod);
                slowEma = EMA(SlowEmaPeriod);
                adx = ADX(TrendAdxPeriod);
                atr = ATR(AtrPeriod);

                AddChartIndicator(fastEma);
                AddChartIndicator(slowEma);

                previousPosition = MarketPosition.Flat;
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
                consecutiveLosses = 0;
                tradingHaltedForDay = false;
            }

            // Track when we return to flat so we can apply the cooldown.
            if (previousPosition != MarketPosition.Flat && Position.MarketPosition == MarketPosition.Flat)
                lastExitBar = CurrentBar;
            previousPosition = Position.MarketPosition;

            int nowHHMM = Time[0].Hour * 100 + Time[0].Minute;
            bool withinSession = nowHHMM >= SessionStartHHMM && nowHHMM < SessionEndHHMM;

            // Outside the trading window or once the day is halted: flatten and stop.
            if (!withinSession || tradingHaltedForDay)
            {
                Flatten("SessionOrRiskFlatten");
                return;
            }

            // --- Kill switch: daily loss limit (realized + open) ---
            double openPnL = Position.MarketPosition == MarketPosition.Flat
                ? 0
                : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);

            if (dailyRealizedPnL + openPnL <= -Math.Abs(MaxDailyLossDollars))
            {
                Print(string.Format("{0}: Daily loss limit hit ({1:C}). Flattening and halting for the day.",
                    Time[0], dailyRealizedPnL + openPnL));
                tradingHaltedForDay = true;
                Flatten("DailyLossLimit");
                return;
            }

            // --- In-trade management (break-even + time stop) ---
            if (Position.MarketPosition != MarketPosition.Flat)
            {
                ManageOpenPosition();
                return; // one position at a time; no new entries while in a trade
            }

            // --- Entry gating ---
            if (dailyTradeCount >= MaxDailyTrades)
                return;

            if (consecutiveLosses >= MaxConsecutiveLosses)
                return;

            if (CurrentBar - lastExitBar < CooldownBars)
                return;

            // Volatility filter.
            double atrTicks = atr[0] / TickSize;
            if (atrTicks < MinAtrTicks || atrTicks > MaxAtrTicks)
                return;

            // Trend-strength filter.
            if (adx[0] < TrendAdxThreshold)
                return;

            // EMA separation filter (avoid entering when EMAs are tangled).
            if (Math.Abs(fastEma[0] - slowEma[0]) < MinEmaSeparationAtr * atr[0])
                return;

            int stopTicks = Math.Max(1, (int)Math.Round(atr[0] * StopAtrMultiple / TickSize));
            int targetTicks = Math.Max(1, (int)Math.Round(atr[0] * TargetAtrMultiple / TickSize));

            if (CrossAbove(fastEma, slowEma, 1))
            {
                SetStopLoss("Long", CalculationMode.Ticks, stopTicks, false);
                SetProfitTarget("Long", CalculationMode.Ticks, targetTicks);
                EnterLong(Contracts, "Long");
                entryBar = CurrentBar;
                movedToBreakeven = false;
            }
            else if (CrossBelow(fastEma, slowEma, 1))
            {
                SetStopLoss("Short", CalculationMode.Ticks, stopTicks, false);
                SetProfitTarget("Short", CalculationMode.Ticks, targetTicks);
                EnterShort(Contracts, "Short");
                entryBar = CurrentBar;
                movedToBreakeven = false;
            }
        }

        private void ManageOpenPosition()
        {
            double entryPrice = Position.AveragePrice;

            // Break-even: once price has moved BreakevenTriggerAtrMultiple * ATR in our favor,
            // pull the stop to the entry price so the trade can no longer become a loser.
            if (BreakevenTriggerAtrMultiple > 0 && !movedToBreakeven)
            {
                double trigger = atr[0] * BreakevenTriggerAtrMultiple;

                if (Position.MarketPosition == MarketPosition.Long && Close[0] - entryPrice >= trigger)
                {
                    SetStopLoss("Long", CalculationMode.Price, entryPrice, false);
                    movedToBreakeven = true;
                }
                else if (Position.MarketPosition == MarketPosition.Short && entryPrice - Close[0] >= trigger)
                {
                    SetStopLoss("Short", CalculationMode.Price, entryPrice, false);
                    movedToBreakeven = true;
                }
            }

            // Time stop: don't hold a scalp indefinitely.
            if (MaxBarsInTrade > 0 && CurrentBar - entryBar >= MaxBarsInTrade)
                Flatten("TimeStop");
        }

        private void Flatten(string signalName)
        {
            if (Position.MarketPosition == MarketPosition.Long)
                ExitLong(signalName, "Long");
            else if (Position.MarketPosition == MarketPosition.Short)
                ExitShort(signalName, "Short");
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price,
            int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order == null || execution.Order.OrderState != OrderState.Filled)
                return;

            // Only account on exit fills (a completed round trip).
            if (execution.Order.Name != null &&
                (execution.Order.Name == "Long" || execution.Order.Name == "Short"))
                return;

            if (SystemPerformance.AllTrades.Count > 0)
            {
                var lastTrade = SystemPerformance.AllTrades[SystemPerformance.AllTrades.Count - 1];
                if (lastTrade.Exit.Time == time)
                {
                    dailyRealizedPnL += lastTrade.ProfitCurrency;
                    dailyTradeCount++;

                    if (lastTrade.ProfitCurrency < 0)
                        consecutiveLosses++;
                    else
                        consecutiveLosses = 0;
                }
            }
        }

        #region Properties

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Fast EMA Period", Order = 1, GroupName = "1. Trend / Signal")]
        public int FastEmaPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(2, int.MaxValue)]
        [Display(Name = "Slow EMA Period", Order = 2, GroupName = "1. Trend / Signal")]
        public int SlowEmaPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Contracts", Order = 3, GroupName = "1. Trend / Signal")]
        public int Contracts { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Trend ADX Period", Order = 1, GroupName = "2. Trend Strength")]
        public int TrendAdxPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(0, 100)]
        [Display(Name = "Trend ADX Threshold", Order = 2, GroupName = "2. Trend Strength")]
        public double TrendAdxThreshold { get; set; }

        [NinjaScriptProperty]
        [Range(0, double.MaxValue)]
        [Display(Name = "Min EMA Separation (x ATR)", Order = 3, GroupName = "2. Trend Strength")]
        public double MinEmaSeparationAtr { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "ATR Period", Order = 1, GroupName = "3. Volatility")]
        public int AtrPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(0, double.MaxValue)]
        [Display(Name = "Min ATR (ticks)", Order = 2, GroupName = "3. Volatility")]
        public double MinAtrTicks { get; set; }

        [NinjaScriptProperty]
        [Range(1, double.MaxValue)]
        [Display(Name = "Max ATR (ticks)", Order = 3, GroupName = "3. Volatility")]
        public double MaxAtrTicks { get; set; }

        [NinjaScriptProperty]
        [Range(0.1, double.MaxValue)]
        [Display(Name = "Stop Loss (x ATR)", Order = 1, GroupName = "4. Exits")]
        public double StopAtrMultiple { get; set; }

        [NinjaScriptProperty]
        [Range(0.1, double.MaxValue)]
        [Display(Name = "Take Profit (x ATR)", Order = 2, GroupName = "4. Exits")]
        public double TargetAtrMultiple { get; set; }

        [NinjaScriptProperty]
        [Range(0, double.MaxValue)]
        [Display(Name = "Break-even Trigger (x ATR, 0=off)", Order = 3, GroupName = "4. Exits")]
        public double BreakevenTriggerAtrMultiple { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [Display(Name = "Max Bars In Trade (0=off)", Order = 4, GroupName = "4. Exits")]
        public int MaxBarsInTrade { get; set; }

        [NinjaScriptProperty]
        [Range(1, double.MaxValue)]
        [Display(Name = "Max Daily Loss ($)", Order = 1, GroupName = "5. Daily Risk")]
        public double MaxDailyLossDollars { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Max Trades Per Day", Order = 2, GroupName = "5. Daily Risk")]
        public int MaxDailyTrades { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Max Consecutive Losses", Order = 3, GroupName = "5. Daily Risk")]
        public int MaxConsecutiveLosses { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [Display(Name = "Cooldown Bars", Order = 4, GroupName = "5. Daily Risk")]
        public int CooldownBars { get; set; }

        [NinjaScriptProperty]
        [Range(0, 2359)]
        [Display(Name = "Session Start (HHMM)", Order = 1, GroupName = "6. Session")]
        public int SessionStartHHMM { get; set; }

        [NinjaScriptProperty]
        [Range(0, 2359)]
        [Display(Name = "Session End (HHMM)", Order = 2, GroupName = "6. Session")]
        public int SessionEndHHMM { get; set; }

        #endregion
    }
}
