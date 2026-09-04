// =====================================================================================
// OrbApertura — ruptura del rango de apertura de EE.UU. (Opening Range Breakout, NinjaTrader 8).
//
// Vela de referencia = primeros 30 min de la RTH (09:30-10:00 hora del Este). Cuando cierra:
//   - Buy stop en el MÁXIMO del rango, sell stop en el MÍNIMO (OCO: entra el primero que se toque).
//   - Stop inicial = extremo CONTRARIO del rango (largo: mínimo; corto: máximo). Riesgo = rango.
//   - Break-even: cuando avanza +BeTicks a favor (por defecto 50t = 12,5pt), el stop pasa a la
//     entrada (protege sin cortar los runners). Sin target: se deja correr.
//   - Salida por tiempo: 13:00 hora Argentina (disponibilidad del operador). Sin overnight.
//   - 1 operación por día (OCO): si el stop saca, no reingresa. Miércoles INCLUIDOS. Sin filtros.
//
// ADVERTENCIA — POR QUÉ ESTÁ EN OBSERVACIÓN Y NO VALIDADO:
//   In-sample (2023-2026) se veía muy bien (+$2.700-$3.100, positivo los 4 años, buena frecuencia).
//   Pero en el OUT-OF-SAMPLE 2022-2023 se dio vuelta a NEGATIVO (-$2.000/-$2.656, rompía el
//   drawdown): es un edge DEPENDIENTE DEL RÉGIMEN, no persistente. Se lleva a Sim solo para
//   observarlo en papel en paralelo, NO para operar en real. El bot validado es ConnorsRsi2. Ver doc 19.
//
// El break-even (BeTicks) SÍ resultó gestión de riesgo real (redujo pérdidas también en 2022) —
// por eso queda activado por defecto, aunque no alcance para dar vuelta el sistema.
//
// ZONA HORARIA: correr NinjaTrader en US Eastern. El rango de apertura se detecta en hora del Este
// (sigue el horario de verano de EE.UU.); la salida se calcula en hora Argentina (UTC-3 fija).
// Usar gráfico de 1 minuto (fills precisos de la ruptura y del break-even). Serie con overnight.
// =====================================================================================
#region Using declarations
using System;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class OrbApertura : Strategy
    {
        [NinjaScriptProperty][Range(1, 100)]
        [Display(Name = "Contratos", Order = 1, GroupName = "Parámetros")]
        public int Contratos { get; set; } = 1;

        [NinjaScriptProperty][Range(0, 2359)]
        [Display(Name = "Apertura RTH (HHMM ET)", Order = 2, GroupName = "Parámetros")]
        public int AperturaHHMM { get; set; } = 930;

        [NinjaScriptProperty][Range(5, 120)]
        [Display(Name = "Minutos del rango de apertura", Order = 3, GroupName = "Parámetros")]
        public int MinutosRango { get; set; } = 30;

        [NinjaScriptProperty][Range(0, 500)]
        [Display(Name = "Break-even a +N ticks (0 = sin BE)", Order = 4, GroupName = "Riesgo")]
        public int BeTicks { get; set; } = 50;

        [NinjaScriptProperty][Range(0, 2359)]
        [Display(Name = "Aplanado (HHMM ART)", Order = 5, GroupName = "Horarios")]
        public int FinHHMM { get; set; } = 1300;

        [NinjaScriptProperty]
        [Display(Name = "Zona del gráfico (Windows ID)", Order = 6, GroupName = "Horarios")]
        public string IdZonaGrafico { get; set; } = "Eastern Standard Time";

        private TimeZoneInfo srcZone;   // zona del gráfico
        private TimeZoneInfo etZone;    // hora del Este (para el rango de apertura)
        private DateTime curDay = DateTime.MinValue;
        private double orbHi, orbLo, entryPrice;
        private bool orbActive, orbSet, tradedToday, beActivated;
        private Order ordLong, ordShort;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "OrbApertura";
                Description = "ORB de la apertura USA: buy/sell stop en el rango 09:30-10:00 ET, stop al extremo contrario, break-even, salida 13:00 ART.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;
                BarsRequiredToTrade = 20;
            }
            else if (State == State.DataLoaded)
            {
                try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); }
                catch { etZone = null; }
                try { srcZone = TimeZoneInfo.FindSystemTimeZoneById(IdZonaGrafico.Trim()); }
                catch { srcZone = null; }
            }
        }

        private DateTime ToUtc(DateTime chartTime)
        {
            if (srcZone == null) return chartTime;
            DateTime unspec = DateTime.SpecifyKind(chartTime, DateTimeKind.Unspecified);
            return TimeZoneInfo.ConvertTimeToUtc(unspec, srcZone);
        }
        private DateTime ToEt(DateTime chartTime)
        {
            if (srcZone == null || etZone == null) return chartTime;
            try { return TimeZoneInfo.ConvertTimeFromUtc(ToUtc(chartTime), etZone); }
            catch { return chartTime; }
        }
        private DateTime ToArt(DateTime chartTime)
        {
            if (srcZone == null) return chartTime.AddHours(-2);
            try { return ToUtc(chartTime).AddHours(-3); }   // Buenos Aires, UTC-3 fija
            catch { return chartTime.AddHours(-2); }
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price,
            int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order == null || execution.Order.OrderState != OrderState.Filled) return;
            string n = execution.Order.Name;
            if (n == "orb_long" || n == "orb_short")
            {
                tradedToday = true; entryPrice = price; beActivated = false;
                if (n == "orb_long" && ordShort != null) { CancelOrder(ordShort); ordShort = null; }
                if (n == "orb_short" && ordLong != null) { CancelOrder(ordLong); ordLong = null; }
            }
        }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0 || CurrentBar < 20) return;

            DateTime et = ToEt(Time[0]);
            DateTime art = ToArt(Time[0]);
            int etMin = et.Hour * 60 + et.Minute;
            int artHHMM = art.Hour * 100 + art.Minute;

            if (et.Date != curDay)
            {
                curDay = et.Date;
                orbHi = double.MinValue; orbLo = double.MaxValue;
                orbActive = false; orbSet = false; tradedToday = false; beActivated = false;
                ordLong = null; ordShort = null;
            }

            int orOpen = (AperturaHHMM / 100) * 60 + (AperturaHHMM % 100);
            int orEnd = orOpen + MinutosRango;

            // ---- construir el rango de apertura (09:30-10:00 ET) ----
            if (etMin >= orOpen && etMin < orEnd)
            {
                orbActive = true;
                if (High[0] > orbHi) orbHi = High[0];
                if (Low[0] < orbLo) orbLo = Low[0];
                return;
            }
            if (orbActive && !orbSet && etMin >= orEnd)
            {
                orbSet = orbHi > orbLo; orbActive = false;
            }

            // ---- salida por tiempo (13:00 ART) ----
            if (artHHMM >= FinHHMM)
            {
                if (Position.MarketPosition == MarketPosition.Long) ExitLong("finVentana");
                else if (Position.MarketPosition == MarketPosition.Short) ExitShort("finVentana");
                if (ordLong != null) { CancelOrder(ordLong); ordLong = null; }
                if (ordShort != null) { CancelOrder(ordShort); ordShort = null; }
                return;
            }

            if (!orbSet) return;

            // ---- gestión de la posición abierta: stop dinámico (extremo contrario -> break-even) ----
            if (Position.MarketPosition == MarketPosition.Long)
            {
                if (BeTicks > 0 && !beActivated && High[0] >= entryPrice + BeTicks * TickSize) beActivated = true;
                SetStopLoss(CalculationMode.Price, beActivated ? entryPrice : orbLo);
                return;
            }
            if (Position.MarketPosition == MarketPosition.Short)
            {
                if (BeTicks > 0 && !beActivated && Low[0] <= entryPrice - BeTicks * TickSize) beActivated = true;
                SetStopLoss(CalculationMode.Price, beActivated ? entryPrice : orbHi);
                return;
            }

            // ---- flat: colocar/mantener las dos órdenes stop de entrada (OCO) ----
            if (!tradedToday && Position.MarketPosition == MarketPosition.Flat)
            {
                ordLong = EnterLongStopMarket(0, true, Contratos, orbHi, "orb_long");
                ordShort = EnterShortStopMarket(0, true, Contratos, orbLo, "orb_short");
            }
        }
    }
}
