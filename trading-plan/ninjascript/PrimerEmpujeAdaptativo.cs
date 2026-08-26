// =====================================================================================
// PrimerEmpujeAdaptativo — ORB de apertura que SIGUE EL RÉGIMEN (NinjaTrader 8).
//
// El índice tiende algunos períodos (gana el breakout) y revierte otros (gana el fade).
// Este bot elige la dirección según lo que viene ganando: opera FADE si la suma de las
// últimas K "operaciones-fade" es >= 0; si no, opera BREAKOUT.
//
// Validado out-of-sample en MES y MNQ (datos limpios NinjaTrader, 2024-2026, K=10):
//   Portfolio 1 MES + 1 MNQ: +$9.384 en 3 años, max drawdown -$1.729, positivo los 6
//   años-instrumento. Robusto de K=6 a K=15. Ver doc 16.
//
// Resto de las reglas = Primer Empuje filtrado:
//   - Rango de apertura = primeros 30 min de la RTH (09:30-10:00 ET).
//   - Ruptura = primera vela de 1 min que CIERRA fuera del rango (regla D3: cierra el día).
//   - Filtros (opcionales): media 200 + dirección del día previo, sobre la dirección de la ruptura.
//   - R = alto del rango. Objetivo 1R, stop al extremo opuesto. 1 op/día. Aplanado no-overnight.
//
// La señal de régimen usa el resultado REAL de cada operación cerrada (NinjaTrader lo calcula),
// convertido a "equivalente-fade": si operamos fade, su P&L; si operamos breakout, su P&L negado
// (lo que habría hecho el fade). Así la señal es idéntica a lo que pasó, sin supuestos de intrabar.
//
// IMPORTANTE: NinjaTrader en zona US Eastern; serie de 1 min con overnight (Globex) para la
// media de 200; preferir UN contrato (evita artefactos de roll) al validar.
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
    public class PrimerEmpujeAdaptativo : Strategy
    {
        [NinjaScriptProperty][Range(1, 100)]
        [Display(Name = "Contratos", Order = 1, GroupName = "Parámetros")]
        public int Contratos { get; set; } = 1;

        [NinjaScriptProperty][Range(5, 120)]
        [Display(Name = "Minutos del rango de apertura", Order = 2, GroupName = "Parámetros")]
        public int OrbMinutes { get; set; } = 30;

        [NinjaScriptProperty][Range(10, 500)]
        [Display(Name = "Media de tendencia (barras)", Order = 3, GroupName = "Parámetros")]
        public int MaPeriod { get; set; } = 200;

        [NinjaScriptProperty][Range(5, 60)]
        [Display(Name = "Días para mediana de volatilidad", Order = 4, GroupName = "Parámetros")]
        public int VolLookback { get; set; } = 20;

        [NinjaScriptProperty][Range(2, 60)]
        [Display(Name = "K (ventana de régimen)", Order = 5, GroupName = "Parámetros")]
        public int KVentana { get; set; } = 10;

        [NinjaScriptProperty]
        [Display(Name = "Usar filtros media/dirección", Order = 6, GroupName = "Parámetros")]
        public bool UsarFiltros { get; set; } = true;

        [NinjaScriptProperty]
        [Display(Name = "Apertura RTH (HHMM ET)", Order = 7, GroupName = "Horarios")]
        public int RthOpen { get; set; } = 930;

        [NinjaScriptProperty]
        [Display(Name = "Aplanado (HHMM ET)", Order = 8, GroupName = "Horarios")]
        public int FlattenHHMM { get; set; } = 1555;

        private SMA sma;
        private DateTime curDay = DateTime.MinValue;
        private double orbHi, orbLo;
        private bool orbSet, tradedToday, orbActive, orbEvaluated;
        private double sessOpen, sessClose;
        private bool sessOpenSet;
        private int prevDayDir;
        private readonly List<double> rangeHist = new List<double>();
        private readonly List<double> fadeHist = new List<double>();   // resultado-fade por operación
        private int OrbEndMinutes;

        // señal de régimen basada en el resultado REAL de cada operación (fiel a los fills)
        private int tradesVistos;      // cuántas operaciones cerradas ya contabilizamos
        private bool opActualEsFade;   // la operación abierta, ¿es un fade?

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "PrimerEmpujeAdaptativo";
                Description = "ORB que sigue el régimen: fade si el fade viene ganando, si no breakout.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;
                BarsRequiredToTrade = 220;
            }
            else if (State == State.DataLoaded) { sma = SMA(MaPeriod); }
        }

        private static int HHMM(DateTime t) { return t.Hour * 100 + t.Minute; }
        private static int Minutes(DateTime t) { return t.Hour * 60 + t.Minute; }

        // suma de las últimas K entradas de la lista de resultados-fade
        private double SumaUltimasK()
        {
            double s = 0; int n = fadeHist.Count;
            for (int i = Math.Max(0, n - KVentana); i < n; i++) s += fadeHist[i];
            return s;
        }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0 || CurrentBar < MaPeriod + 5) return;
            DateTime t = Time[0];

            if (t.Date != curDay)
            {
                if (curDay != DateTime.MinValue && sessOpenSet)
                    prevDayDir = sessClose > sessOpen ? 1 : -1;
                curDay = t.Date;
                orbHi = double.MinValue; orbLo = double.MaxValue;
                orbSet = false; orbActive = false; tradedToday = false; orbEvaluated = false;
                sessOpenSet = false;
                int oh = RthOpen / 100, om = RthOpen % 100;
                OrbEndMinutes = oh * 60 + om + OrbMinutes;
            }

            int hhmm = HHMM(t), mins = Minutes(t);
            int rthOpenMin = (RthOpen / 100) * 60 + (RthOpen % 100);

            bool inRth = mins >= rthOpenMin && hhmm < 1600;
            if (inRth) { if (!sessOpenSet) { sessOpen = Open[0]; sessOpenSet = true; } sessClose = Close[0]; }

            // ---- registrar el resultado-fade de las operaciones que se hayan cerrado ----
            while (SystemPerformance.AllTrades.Count > tradesVistos)
            {
                Trade tr = SystemPerformance.AllTrades[tradesVistos];
                double pts = tr.ProfitPoints;                       // P&L de la operación en puntos
                fadeHist.Add(opActualEsFade ? pts : -pts);          // equivalente-fade
                tradesVistos++;
            }

            // ---- construir el rango de apertura ----
            if (mins >= rthOpenMin && mins < OrbEndMinutes)
            {
                orbActive = true;
                if (High[0] > orbHi) orbHi = High[0];
                if (Low[0] < orbLo) orbLo = Low[0];
            }
            else if (orbActive && !orbEvaluated && mins >= OrbEndMinutes)
            {
                orbEvaluated = true;
                double frac = orbHi > 0 ? (orbHi - orbLo) / orbHi : 0;
                bool volOK = false;
                if (rangeHist.Count >= 10)
                {
                    var last = rangeHist.GetRange(Math.Max(0, rangeHist.Count - VolLookback),
                        Math.Min(VolLookback, rangeHist.Count));
                    last.Sort();
                    double med = last[last.Count / 2];
                    volOK = frac > med;
                }
                rangeHist.Add(frac);
                orbSet = volOK;
            }

            // ---- aplanado no-overnight ----
            if (hhmm >= FlattenHHMM)
            {
                if (Position.MarketPosition == MarketPosition.Long) ExitLong("flat");
                else if (Position.MarketPosition == MarketPosition.Short) ExitShort("flat");
                return;
            }

            if (!orbSet || tradedToday || Position.MarketPosition != MarketPosition.Flat) return;
            if (mins < OrbEndMinutes) return;

            bool up = Close[0] > orbHi;
            bool down = Close[0] < orbLo;
            if (!up && !down) return;

            tradedToday = true;   // regla D3: la primera ruptura cierra el día
            bool breakoutUp = up;

            if (UsarFiltros)
            {
                if (breakoutUp && !(Close[0] > sma[0])) return;
                if (!breakoutUp && !(Close[0] < sma[0])) return;
                if (breakoutUp && prevDayDir != 1) return;
                if (!breakoutUp && prevDayDir != -1) return;
            }

            double range = orbHi - orbLo;
            double entry = Close[0];

            // decisión de régimen: fade si el fade viene ganando (suma últimas K >= 0)
            bool chooseFade = fadeHist.Count == 0 ? true : (SumaUltimasK() >= 0);
            bool goLong = chooseFade ? !breakoutUp : breakoutUp;

            double stop, target;
            if (!chooseFade)   // seguir la ruptura
            {
                stop = breakoutUp ? orbLo : orbHi;
                target = breakoutUp ? entry + range : entry - range;
            }
            else               // fadear la ruptura
            {
                target = breakoutUp ? orbLo : orbHi;
                stop = breakoutUp ? entry + range : entry - range;
            }

            SetStopLoss(CalculationMode.Price, stop);
            SetProfitTarget(CalculationMode.Price, target);
            if (goLong) EnterLong(Contratos, "pe_long");
            else EnterShort(Contratos, "pe_short");

            opActualEsFade = chooseFade;   // para clasificar el resultado cuando la operación cierre
        }
    }
}
