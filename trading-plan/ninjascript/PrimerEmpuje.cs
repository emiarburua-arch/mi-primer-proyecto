// =====================================================================================
// PrimerEmpuje — estrategia NinjaScript (NinjaTrader 8) del breakout de apertura filtrado.
//
// Reglas validadas en Python (trading-plan/backtest, doc 13; mejor candidato para MES):
//   - Rango de apertura = máx/mín de los primeros 30 min de la RTH (09:30–10:00 ET).
//   - Ruptura = una vela de 1 min CIERRA fuera del rango (primera del día).
//   - Filtros:
//       (1) Tendencia: la ruptura debe estar del lado correcto de la media de 200 (M1).
//       (2) Volatilidad: el rango de apertura (en %) debe superar la mediana de los últimos
//           20 días (solo días de rango amplio).
//       (3) Dirección del día previo: si la RTH de ayer cerró alcista, solo largos hoy;
//           si cerró bajista, solo cortos.
//   - Entrada al cierre de la vela de ruptura. Stop = extremo opuesto del rango.
//     Objetivo = 1R (una altura de rango). Una operación por día. Aplanado no-overnight.
//
// Resultado del backtest (MES, 3 años, con costos): PF 1.41, media +$18/op, DD $1.010 (1 lote),
// positivo todos los años; entra a 2 lotes en cuenta de $2.500 DD / $900 diario.
//
// IMPORTANTE:
//   - Poné NinjaTrader en zona horaria US Eastern (Tools > Options > General > Time zone),
//     porque la ventana de apertura se mide a las 09:30 ET.
//   - Usá una serie de 1 minuto que incluya el overnight (Globex), NO solo RTH: la media de
//     200 necesita las barras continuas para coincidir con el backtest.
//
// Estado: v1 para compilar y validar en el Strategy Analyzer. Esperá iterar en compilación.
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
    public class PrimerEmpuje : Strategy
    {
        [NinjaScriptProperty]
        [Range(1, 100)]
        [Display(Name = "Contratos", Order = 1, GroupName = "Parámetros")]
        public int Contratos { get; set; } = 1;

        [NinjaScriptProperty]
        [Range(5, 120)]
        [Display(Name = "Minutos del rango de apertura", Order = 2, GroupName = "Parámetros")]
        public int OrbMinutes { get; set; } = 30;

        [NinjaScriptProperty]
        [Range(10, 500)]
        [Display(Name = "Media de tendencia (barras)", Order = 3, GroupName = "Parámetros")]
        public int MaPeriod { get; set; } = 200;

        [NinjaScriptProperty]
        [Range(5, 60)]
        [Display(Name = "Días para mediana de volatilidad", Order = 4, GroupName = "Parámetros")]
        public int VolLookback { get; set; } = 20;

        // RTH en hora del EXCHANGE/ET (NinjaTrader en zona US Eastern). Formato HHMM.
        [NinjaScriptProperty]
        [Display(Name = "Apertura RTH (HHMM ET)", Order = 5, GroupName = "Horarios")]
        public int RthOpen { get; set; } = 930;

        [NinjaScriptProperty]
        [Display(Name = "Aplanado (HHMM ET)", Order = 6, GroupName = "Horarios")]
        public int FlattenHHMM { get; set; } = 1555;

        private SMA sma;

        // estado de la sesión
        private DateTime curDay = DateTime.MinValue;
        private double orbHi, orbLo;
        private bool orbSet, tradedToday, orbActive, orbEvaluated;
        private double sessOpen, sessClose;
        private bool sessOpenSet;
        private int prevDayDir;                 // 1 alcista, -1 bajista, 0 desconocido
        private readonly List<double> rangeHist = new List<double>();

        private int OrbEndMinutes;              // minutos desde medianoche del fin del rango

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "PrimerEmpuje";
                Description = "Breakout de apertura (30m) + media200 + volatilidad + dirección día previo.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;
                BarsRequiredToTrade = 220;
            }
            else if (State == State.DataLoaded)
            {
                sma = SMA(MaPeriod);
            }
        }

        private static int HHMM(DateTime t) { return t.Hour * 100 + t.Minute; }
        private static int Minutes(DateTime t) { return t.Hour * 60 + t.Minute; }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0 || CurrentBar < MaPeriod + 5) return;

            DateTime t = Time[0];

            // ---- nuevo día: cerrar el anterior y resetear ----
            if (t.Date != curDay)
            {
                if (curDay != DateTime.MinValue && sessOpenSet)
                    prevDayDir = sessClose > sessOpen ? 1 : -1;   // dirección de la RTH de AYER
                curDay = t.Date;
                orbHi = double.MinValue; orbLo = double.MaxValue;
                orbSet = false; orbActive = false; tradedToday = false; orbEvaluated = false;
                sessOpenSet = false;
                int oh = RthOpen / 100, om = RthOpen % 100;
                OrbEndMinutes = oh * 60 + om + OrbMinutes;
            }

            int hhmm = HHMM(t), mins = Minutes(t);
            int rthOpenMin = (RthOpen / 100) * 60 + (RthOpen % 100);

            // registrar apertura/cierre de la RTH (para dirección del día)
            bool inRth = mins >= rthOpenMin && hhmm < 1600;
            if (inRth)
            {
                if (!sessOpenSet) { sessOpen = Open[0]; sessOpenSet = true; }
                sessClose = Close[0];
            }

            // ---- construir el rango de apertura (primeros OrbMinutes de la RTH) ----
            if (mins >= rthOpenMin && mins < OrbEndMinutes)
            {
                orbActive = true;
                if (High[0] > orbHi) orbHi = High[0];
                if (Low[0] < orbLo) orbLo = Low[0];
            }
            else if (orbActive && !orbEvaluated && mins >= OrbEndMinutes)
            {
                // rango recién cerrado: se evalúa UNA sola vez por día (bug corregido)
                orbEvaluated = true;
                double frac = orbHi > 0 ? (orbHi - orbLo) / orbHi : 0;   // igual que Python (R/hi)
                bool volOK = false;
                if (rangeHist.Count >= 10)
                {
                    var last = rangeHist.GetRange(Math.Max(0, rangeHist.Count - VolLookback),
                        Math.Min(VolLookback, rangeHist.Count));
                    last.Sort();
                    double med = last[last.Count / 2];
                    volOK = frac > med;
                }
                rangeHist.Add(frac);       // se agrega una sola vez
                orbSet = volOK;            // solo se opera si la volatilidad supera la mediana
            }

            // ---- aplanado no-overnight ----
            if (hhmm >= FlattenHHMM)
            {
                if (Position.MarketPosition == MarketPosition.Long) ExitLong("flat");
                else if (Position.MarketPosition == MarketPosition.Short) ExitShort("flat");
                return;
            }

            // ---- buscar la ruptura (una por día) ----
            if (!orbSet || tradedToday || Position.MarketPosition != MarketPosition.Flat) return;
            if (mins < OrbEndMinutes) return;

            bool up = Close[0] > orbHi;
            bool down = Close[0] < orbLo;
            if (!up && !down) return;

            bool isLong = up;
            // filtro de tendencia (media 200)
            if (isLong && !(Close[0] > sma[0])) return;
            if (!isLong && !(Close[0] < sma[0])) return;
            // filtro de dirección del día previo
            if (isLong && prevDayDir != 1) return;
            if (!isLong && prevDayDir != -1) return;

            double range = orbHi - orbLo;
            double entry = Close[0];
            double stop = isLong ? orbLo : orbHi;
            double target = isLong ? entry + range : entry - range;

            SetStopLoss(CalculationMode.Price, stop);
            SetProfitTarget(CalculationMode.Price, target);
            if (isLong) EnterLong(Contratos, "pe_long");
            else EnterShort(Contratos, "pe_short");
            tradedToday = true;
        }
    }
}
