// =====================================================================================
// OrbApertura — ruptura del rango de apertura de EE.UU. (Opening Range Breakout, NinjaTrader 8).
//
// Vela de referencia = primeros 30 min de la RTH (09:30-10:00 hora del Este). Cuando cierra:
//   - Si una vela de 1 min PERFORA el máximo del rango -> entra largo. Si perfora el mínimo -> corto.
//   - Stop inicial = extremo CONTRARIO del rango (largo: mínimo; corto: máximo).
//   - Break-even: cuando avanza +BeTicks a favor (por defecto 50t = 12,5pt), el stop pasa a la entrada.
//   - Aplanado por tiempo (sin overnight). 1 operación por día. Miércoles INCLUIDOS. Sin filtros.
//
// EJECUCIÓN A PRUEBA DE BALAS: solo órdenes a MERCADO al cierre de cada vela de 1 min (entrada, stop
// y aplanado). Sin órdenes stop GTC, sin SetStopLoss, sin OCO — para evitar conflictos de manejo de
// órdenes que dejaban posiciones trabadas. La entrada es al cierre de la vela que rompe el rango
// (aprox. la ruptura); el fill real es a mercado en la vela siguiente.
//
// ZONA HORARIA — IMPORTANTE: correr NinjaTrader en US Eastern. No convierte zonas: usa la hora del
// gráfico tal cual. Con NinjaTrader en US Eastern, los horarios de abajo son hora del Este. El
// aplanado por defecto es 12:00 ET (≈13:00 ART en verano de EE.UU.; poné 1100 para 13:00 ART en
// invierno). Usar gráfico de 1 minuto. Serie con overnight (Globex).
//
// ADVERTENCIA — EN OBSERVACIÓN, NO VALIDADO: falló el out-of-sample 2022-2023 (edge dependiente del
// régimen). Se lleva a Sim solo para observar en papel. El bot para real es ConnorsRsi2. Ver doc 19.
//
// Cómo saber que corre ESTA versión: las salidas se llaman "finVentana" / "stopLong" / "stopShort"
// (NO "Stop loss") y ninguna operación queda overnight (barras por trade cortas).
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

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "OrbApertura";
                Description = "ORB apertura USA (09:30-10:00 ET), solo órdenes a mercado, stop al extremo contrario + break-even, aplanado por tiempo. Correr NinjaTrader en US Eastern.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;
                BarsRequiredToTrade = 20;
            }
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price,
            int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order == null || execution.Order.OrderState != OrderState.Filled) return;
            string n = execution.Order.Name;
            if (n == "orb_long" || n == "orb_short") { entryPrice = price; beActivated = false; }
        }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0 || CurrentBar < 20) return;

            int nowMin = Time[0].Hour * 60 + Time[0].Minute;   // hora del Este (NinjaTrader en US Eastern)

            if (Time[0].Date != curDay)
            {
                curDay = Time[0].Date;
                orbHi = double.MinValue; orbLo = double.MaxValue;
                orbActive = false; orbSet = false; tradedToday = false; beActivated = false;
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

            // ---- fuera de la ventana [orEnd, finMin): aplanar y no operar ----
            bool enVentana = orbSet && nowMin >= orEnd && nowMin < finMin;
            if (!enVentana)
            {
                if (Position.MarketPosition == MarketPosition.Long) ExitLong("finVentana", "orb_long");
                else if (Position.MarketPosition == MarketPosition.Short) ExitShort("finVentana", "orb_short");
                return;
            }

            // ---- gestión de la posición abierta: stop manual (extremo contrario -> break-even) ----
            if (Position.MarketPosition == MarketPosition.Long)
            {
                if (BeTicks > 0 && !beActivated && High[0] >= entryPrice + BeTicks * TickSize) beActivated = true;
                double sp = beActivated ? entryPrice : orbLo;
                if (Low[0] <= sp) ExitLong("stopLong", "orb_long");
                return;
            }
            if (Position.MarketPosition == MarketPosition.Short)
            {
                if (BeTicks > 0 && !beActivated && Low[0] <= entryPrice - BeTicks * TickSize) beActivated = true;
                double sp = beActivated ? entryPrice : orbHi;
                if (High[0] >= sp) ExitShort("stopShort", "orb_short");
                return;
            }

            // ---- flat y dentro de la ventana: detectar ruptura y entrar a mercado (1 op/día) ----
            if (!tradedToday)
            {
                bool rompeArriba = High[0] >= orbHi;
                bool rompeAbajo = Low[0] <= orbLo;
                if (rompeArriba && rompeAbajo)
                {
                    // ambos en la misma vela: la que quede más cerca de la apertura de la vela
                    if (Math.Abs(Open[0] - orbHi) <= Math.Abs(Open[0] - orbLo))
                    { EnterLong(Contratos, "orb_long"); }
                    else { EnterShort(Contratos, "orb_short"); }
                    tradedToday = true;
                }
                else if (rompeArriba) { EnterLong(Contratos, "orb_long"); tradedToday = true; }
                else if (rompeAbajo) { EnterShort(Contratos, "orb_short"); tradedToday = true; }
            }
        }
    }
}
