// =====================================================================================
// OrbApertura — ruptura del rango de apertura de EE.UU. (Opening Range Breakout, NinjaTrader 8).
//
// Vela de referencia = primeros 30 min de la RTH (09:30-10:00 hora del Este). Cuando cierra:
//   - Buy stop en el MÁXIMO del rango, sell stop en el MÍNIMO (OCO: entra el primero que se toque).
//   - Stop inicial = extremo CONTRARIO del rango (largo: mínimo; corto: máximo). Riesgo = rango.
//   - Break-even: cuando avanza +BeTicks a favor (por defecto 50t = 12,5pt), el stop pasa a la
//     entrada (protege sin cortar los runners). Sin target: se deja correr.
//   - Salida por tiempo (aplanado, sin overnight) y 1 operación por día. Miércoles INCLUIDOS. Sin filtros.
//
// ZONA HORARIA — IMPORTANTE: correr NinjaTrader en US Eastern (Tools > Options > General > Time zone).
// Este bot NO convierte zonas (la conversión resultó frágil y rompía el aplanado): usa la hora del
// gráfico TAL CUAL con ToTime(). Con NinjaTrader en US Eastern, todos los horarios de abajo son
// hora del Este. El aplanado por defecto es 12:00 ET ≈ 13:00 hora Argentina en verano de EE.UU.
// (en invierno de EE.UU., 12:00 ET = 14:00 ART; si querés respetar 13:00 ART exacto en invierno,
// poné el aplanado en 1100). Usar gráfico de 1 minuto (fills precisos de la ruptura y el break-even).
//
// ADVERTENCIA — EN OBSERVACIÓN, NO VALIDADO: in-sample se veía bien pero FALLÓ el out-of-sample
// 2022-2023 (edge dependiente del régimen). Se lleva a Sim solo para observar en papel. Ver doc 19.
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
        [Display(Name = "Aplanado (HHMM ET, 1200≈13:00 ART)", Order = 5, GroupName = "Horarios")]
        public int FinHHMM { get; set; } = 1200;

        private DateTime curDay = DateTime.MinValue;
        private double orbHi, orbLo, entryPrice;
        private bool orbActive, orbSet, tradedToday, beActivated;
        private Order ordLong, ordShort;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "OrbApertura";
                Description = "ORB de la apertura USA: buy/sell stop en el rango 09:30-10:00 ET, stop al extremo contrario, break-even, aplanado por tiempo. Correr NinjaTrader en US Eastern.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;
                BarsRequiredToTrade = 20;
            }
        }

        // hora del gráfico como minutos desde medianoche (ET si NinjaTrader está en US Eastern)
        private int MinDelDia(DateTime t) { return t.Hour * 60 + t.Minute; }

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

            int nowMin = MinDelDia(Time[0]);   // hora del Este (NinjaTrader en US Eastern)

            if (Time[0].Date != curDay)
            {
                curDay = Time[0].Date;
                orbHi = double.MinValue; orbLo = double.MaxValue;
                orbActive = false; orbSet = false; tradedToday = false; beActivated = false;
                ordLong = null; ordShort = null;
            }

            int orOpen = (AperturaHHMM / 100) * 60 + (AperturaHHMM % 100);
            int orEnd = orOpen + MinutosRango;
            int finMin = (FinHHMM / 100) * 60 + (FinHHMM % 100);

            // ---- construir el rango de apertura (09:30-10:00 ET) ----
            if (nowMin >= orOpen && nowMin < orEnd)
            {
                orbActive = true;
                if (High[0] > orbHi) orbHi = High[0];
                if (Low[0] < orbLo) orbLo = Low[0];
                return;
            }
            if (orbActive && !orbSet && nowMin >= orEnd)
            {
                orbSet = orbHi > orbLo; orbActive = false;
            }

            // ---- aplanado por tiempo: fuera de la ventana [orEnd, finMin) cerramos y cancelamos ----
            bool enVentana = orbSet && nowMin >= orEnd && nowMin < finMin;
            if (!enVentana)
            {
                if (Position.MarketPosition == MarketPosition.Long) ExitLong("finVentana");
                else if (Position.MarketPosition == MarketPosition.Short) ExitShort("finVentana");
                if (ordLong != null) { CancelOrder(ordLong); ordLong = null; }
                if (ordShort != null) { CancelOrder(ordShort); ordShort = null; }
                return;
            }

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

            // ---- flat y dentro de la ventana: colocar/mantener las dos órdenes stop de entrada (OCO) ----
            if (!tradedToday)
            {
                ordLong = EnterLongStopMarket(0, true, Contratos, orbHi, "orb_long");
                ordShort = EnterShortStopMarket(0, true, Contratos, orbLo, "orb_short");
            }
        }
    }
}
