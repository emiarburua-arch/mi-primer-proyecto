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
// RESULTADO REAL sobre datos limpios de NinjaTrader (MES SEP26, ene–ago 2026, 32 ops):
//   - A FAVOR de la ruptura (breakout): PF 0,35, 28 % aciertos, −$1.674. NO tiene ventaja.
//   - FADEADO (parámetro Fade=true): la inversión exacta dio PF 2,87, 72 %, +$1.514.
//     Coincide con la lógica del doc 13: los índices REVIERTEN intradía → hay que fadear.
// Mi backtest en Python daba PF 1,41 pero usaba un continuo stitcheado con artefactos en los
// rolls (rangos de apertura inflados). NO es confiable; la verdad salió de la ejecución limpia.
//
// Parámetros clave:
//   - Fade: false = sigue la ruptura (petróleo); true = fadea (índices: MES/MNQ).
//   - UsarFiltros: media 200 + dirección del día previo (pensados para el breakout; probar
//     apagados para el fade).
//
// IMPORTANTE:
//   - Poné NinjaTrader en zona horaria US Eastern; la ventana de apertura se mide a las 09:30 ET.
//   - Usá 1 minuto con overnight (Globex) para que la media de 200 tenga barras continuas.
//   - Preferí UN solo contrato (evita artefactos de roll) para validar en el Strategy Analyzer.
//
// Estado: pendiente confirmar el fade con una corrida real y más años antes de Sim101.
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

        // Fade = fadear la ruptura (para índices, que revierten intradía) en vez de seguirla.
        // Sobre MES el breakout perdió (PF 0,35); la inversión fadeada dio PF 2,87 en 7 meses.
        [NinjaScriptProperty]
        [Display(Name = "Fade (fadear la ruptura)", Order = 7, GroupName = "Parámetros")]
        public bool Fade { get; set; } = false;

        // Filtros de tendencia/dirección: útiles al breakout, dudosos al fade. Se pueden apagar.
        [NinjaScriptProperty]
        [Display(Name = "Usar filtros media/dirección", Order = 8, GroupName = "Parámetros")]
        public bool UsarFiltros { get; set; } = true;

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

            // REGLA D3: solo la PRIMERA ruptura de la sesión cuenta. Se cierra el día YA
            // (pase o no los filtros) para no re-evaluar rupturas posteriores. Sin esto el bot
            // seguiría escaneando y entraría en una ruptura más tardía/favorable — un artefacto
            // optimista que infla las operaciones y no existe en el backtest de Python.
            tradedToday = true;

            bool breakoutUp = up;   // dirección de la ruptura (independiente de si operamos a favor o fade)

            // Filtros (opcionales). Se evalúan sobre la dirección de la RUPTURA, como en el
            // breakout original, para poder comparar los mismos setups a favor y fadeados.
            if (UsarFiltros)
            {
                if (breakoutUp && !(Close[0] > sma[0])) return;      // tendencia (media 200)
                if (!breakoutUp && !(Close[0] < sma[0])) return;
                if (breakoutUp && prevDayDir != 1) return;           // dirección del día previo
                if (!breakoutUp && prevDayDir != -1) return;
            }

            double range = orbHi - orbLo;
            double entry = Close[0];
            // A favor: seguimos la ruptura. Fade: la invertimos.
            //   - Objetivo del fade = el extremo OPUESTO del rango (mismo nivel que el stop del breakout).
            //   - Stop del fade = 1R más allá de la entrada (mismo nivel que el objetivo del breakout).
            bool goLong = Fade ? !breakoutUp : breakoutUp;
            double stop, target;
            if (!Fade)
            {
                stop   = breakoutUp ? orbLo : orbHi;
                target = breakoutUp ? entry + range : entry - range;
            }
            else
            {
                target = breakoutUp ? orbLo : orbHi;
                stop   = breakoutUp ? entry + range : entry - range;
            }

            SetStopLoss(CalculationMode.Price, stop);
            SetProfitTarget(CalculationMode.Price, target);
            if (goLong) EnterLong(Contratos, "pe_long");
            else EnterShort(Contratos, "pe_short");
            tradedToday = true;
        }
    }
}
