// =====================================================================================
// ConnorsRsi2 — reversión a la media de Larry Connors adaptada a futuros (NinjaTrader 8).
//
// Núcleo clásico de Connors sobre gráfico de 15 min:
//   - SMA 200 = filtro de tendencia (solo largos sobre la media, solo cortos debajo).
//   - SMA 10  = retroceso de entrada y salida.
//   - RSI(2)  = gatillo de timing: cruce extremo (sube por 10 = largo, baja por 90 = corto).
//
// Entrada LARGA:  Close > SMA200  y  Close < SMA10  y  RSI cruza HACIA ARRIBA el 10.
// Entrada CORTA:  Close < SMA200  y  Close > SMA10  y  RSI cruza HACIA ABAJO el 90.
// Salida Connors: el precio vuelve a cruzar la SMA10 (largo: Close > SMA10; corto: Close < SMA10).
// Stop y target:  30 ticks cada uno (1:1). Connors no usaba stop; nosotros SÍ (freno de seguridad).
//                 La salida por SMA10 suele activarse antes; el stop/target son la red.
// Ventana:        08:00-12:00 hora del Este (= 09:00-13:00 hora Argentina en verano de EE.UU.).
//                 Sin overnight: aplanado al fin de la ventana. Miércoles EXCLUIDO (se validó mejor así).
//
// VALIDACIÓN (por qué este bot y no el ORB de apertura): en backtest fiel sobre MES 15 min,
// esta config (30t/30t, sin ADX) fue positiva IN-SAMPLE (2023-2026) Y pasó el OUT-OF-SAMPLE
// 2022-2023 —incluido el bear market de 2022— con PF > 2. Es un edge chico pero real y persistente.
// Es de baja frecuencia (~30 operaciones/año). Ver docs 18-19.
//
// ZONA HORARIA — IMPORTANTE: correr NinjaTrader en US Eastern. Este bot NO convierte zonas (la
// conversión resultó frágil y rompía el aplanado): usa la hora del gráfico TAL CUAL. Con NinjaTrader
// en US Eastern, la ventana 0800-1200 es hora del Este = 09:00-13:00 ART en verano de EE.UU. (en
// invierno de EE.UU. equivale a 10:00-14:00 ART). Serie de 15 min con overnight (Globex) para que
// la SMA 200 arranque caliente. Un contrato al validar.
// =====================================================================================
#region Using declarations
using System;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Indicators;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class ConnorsRsi2 : Strategy
    {
        [NinjaScriptProperty][Range(1, 100)]
        [Display(Name = "Contratos", Order = 1, GroupName = "Parámetros")]
        public int Contratos { get; set; } = 1;

        [NinjaScriptProperty][Range(2, 500)]
        [Display(Name = "Media de tendencia (barras)", Order = 2, GroupName = "Parámetros")]
        public int MaTendencia { get; set; } = 200;

        [NinjaScriptProperty][Range(2, 100)]
        [Display(Name = "Media de retroceso/salida (barras)", Order = 3, GroupName = "Parámetros")]
        public int MaRetroceso { get; set; } = 10;

        [NinjaScriptProperty][Range(1, 20)]
        [Display(Name = "RSI período", Order = 4, GroupName = "Parámetros")]
        public int RsiPeriodo { get; set; } = 2;

        [NinjaScriptProperty][Range(1, 20)]
        [Display(Name = "RSI suavizado", Order = 5, GroupName = "Parámetros")]
        public int RsiSuave { get; set; } = 3;

        [NinjaScriptProperty][Range(1, 99)]
        [Display(Name = "RSI umbral inferior (largos)", Order = 6, GroupName = "Parámetros")]
        public int RsiInf { get; set; } = 10;

        [NinjaScriptProperty][Range(1, 99)]
        [Display(Name = "RSI umbral superior (cortos)", Order = 7, GroupName = "Parámetros")]
        public int RsiSup { get; set; } = 90;

        [NinjaScriptProperty][Range(1, 500)]
        [Display(Name = "Stop (ticks)", Order = 8, GroupName = "Riesgo")]
        public int StopTicks { get; set; } = 30;

        [NinjaScriptProperty][Range(1, 500)]
        [Display(Name = "Target (ticks)", Order = 9, GroupName = "Riesgo")]
        public int TargetTicks { get; set; } = 30;

        [NinjaScriptProperty][Range(0, 2359)]
        [Display(Name = "Inicio ventana (HHMM ET)", Order = 10, GroupName = "Horarios")]
        public int InicioHHMM { get; set; } = 800;

        [NinjaScriptProperty][Range(0, 2359)]
        [Display(Name = "Fin/aplanado ventana (HHMM ET)", Order = 11, GroupName = "Horarios")]
        public int FinHHMM { get; set; } = 1200;

        [NinjaScriptProperty]
        [Display(Name = "Excluir miércoles", Order = 12, GroupName = "Horarios")]
        public bool ExcluirMiercoles { get; set; } = true;

        private RSI rsi;
        private SMA smaTend;
        private SMA smaRet;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "ConnorsRsi2";
                Description = "Connors RSI(2) reversión a la media: SMA200 + SMA10 + RSI(2), 30t/30t. Correr NinjaTrader en US Eastern.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;
                BarsRequiredToTrade = 210;
            }
            else if (State == State.DataLoaded)
            {
                rsi = RSI(RsiPeriodo, RsiSuave);
                smaTend = SMA(MaTendencia);
                smaRet = SMA(MaRetroceso);
            }
        }

        private static int HHMM(DateTime t) { return t.Hour * 100 + t.Minute; }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0 || CurrentBar < MaTendencia + 5) return;

            // hora del gráfico TAL CUAL (hora del Este si NinjaTrader está en US Eastern). Sin conversión.
            DateTime hora = Time[0];
            int hhmm = HHMM(hora);
            bool enVentana = hhmm >= InicioHHMM && hhmm < FinHHMM;

            // ---- aplanado al fin de la ventana (sin overnight) ----
            if (!enVentana)
            {
                if (Position.MarketPosition == MarketPosition.Long) ExitLong("finVentana");
                else if (Position.MarketPosition == MarketPosition.Short) ExitShort("finVentana");
                return;
            }

            // ---- gestión de la posición abierta: salida Connors (vuelve a cruzar la SMA10) ----
            if (Position.MarketPosition == MarketPosition.Long)
            {
                if (Close[0] > smaRet[0]) ExitLong("salidaSMA10");
                return;
            }
            if (Position.MarketPosition == MarketPosition.Short)
            {
                if (Close[0] < smaRet[0]) ExitShort("salidaSMA10");
                return;
            }

            // ---- entradas (solo si estamos planos y dentro de la ventana) ----
            if (ExcluirMiercoles && hora.DayOfWeek == DayOfWeek.Wednesday) return;

            bool cruzaArriba = rsi[0] > RsiInf && rsi[1] < RsiInf;
            bool cruzaAbajo  = rsi[0] < RsiSup && rsi[1] > RsiSup;

            bool largo = Close[0] > smaTend[0] && Close[0] < smaRet[0] && cruzaArriba;
            bool corto = Close[0] < smaTend[0] && Close[0] > smaRet[0] && cruzaAbajo;

            if (largo || corto)
            {
                SetStopLoss(CalculationMode.Ticks, StopTicks);
                SetProfitTarget(CalculationMode.Ticks, TargetTicks);
                if (largo) EnterLong(Contratos, "cr_long");
                else EnterShort(Contratos, "cr_short");
            }
        }
    }
}
