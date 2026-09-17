//+------------------------------------------------------------------+
//|                                                   indicators.mqh |
//|                                      Copyright 2026,JBlanked LLC |
//|                                         https://www.jblanked.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked LLC"
#property link      "https://www.jblanked.com"
#property strict

#include "JB-Indicator.mqh"

static CIndicator indi;

// forwards (in mql4 is shows import warning)
#ifdef __MQL5__
string getMA(const string symbol, const ENUM_TIMEFRAMES timeframe, const int maPeriod, const int maShift, const ENUM_MA_METHOD maMethod, const int appliedPriceOrHandle, const int shift);
string getMAOnArray(double &array[], const int period, const int maShift, const ENUM_MA_METHOD maMethod, const int shift);
string getRSI(const string symbol, const ENUM_TIMEFRAMES timeframe, const int rsiPeriod, const int appliedPriceOrHandle, const int shift);
string getATR(const string symbol, const ENUM_TIMEFRAMES timeframe, const int atrPeriod, const int shift);
string getADX(const string symbol, const ENUM_TIMEFRAMES timeframe, const int adxPeriod, ENUM_APPLIED_PRICE appliedPrice, const int adxMode, const int shift);
string getCustom(const string symbol, const ENUM_TIMEFRAMES timeframe, const string indicatorAndFolderNameOnly, const int buffer, const int shift);
string getEnvelopes(const string symbol, const ENUM_TIMEFRAMES timeframe, const int envPeriod, const int maShift, const ENUM_MA_METHOD envMethod, const int appliedPriceOrHandle, const double envDeviation, const int envMode, const int shift);
string getFractals(const string symbol, const ENUM_TIMEFRAMES timeframe, const int fractalMode, const int shift);
string getMACD(const string symbol, const ENUM_TIMEFRAMES timeframe, const int fastPeriod, const int slowPeriod, const int signalPeriod, ENUM_APPLIED_PRICE appliedPrice, const int macdMode, const int shift);
string getAO(const string symbol, const ENUM_TIMEFRAMES timeframe, const int shift);
string getMomentum(const string symbol, const ENUM_TIMEFRAMES timeframe, const int momemtumPeriod, ENUM_APPLIED_PRICE appliedPrice, const int shift);
string getWPR(const string symbol, const ENUM_TIMEFRAMES timeframe, const int wprPeriod, const int shift);
string getBullsPower(const string symbol, const ENUM_TIMEFRAMES timeframe, const int bullPeriod, ENUM_APPLIED_PRICE appliedPrice, const int shift);
string getBearsPower(const string symbol, const ENUM_TIMEFRAMES timeframe, const int bearPeriod, ENUM_APPLIED_PRICE appliedPrice, const int shift);
string getATHR(const string symbol, const ENUM_TIMEFRAMES timeframe, const int shift);
string getStochastic(const string symbol, const ENUM_TIMEFRAMES timeframe, const int kPeriod, const int dPeriod, const int slowPeriod, const ENUM_MA_METHOD maMethod, ENUM_STO_PRICE stoPrice, const int stochMode, const int shift);
string getCCI(const string symbol, const ENUM_TIMEFRAMES timeframe, const int cciPeriod, ENUM_APPLIED_PRICE appliedPrice, const int shift);
string getADR(const string symbol, const int period, const int shift);
string getVWAP(const string symbol, const ENUM_TIMEFRAMES timeframe, const int period, const int shift);
string getPVI(const string symbol, const ENUM_TIMEFRAMES timeframe, const ENUM_APPLIED_VOLUME volumeType, const int shift);
string getPVI(const string symbol, const ENUM_TIMEFRAMES timeframe, const ENUM_APPLIED_VOLUME volumeType, const double & closeData[], const int shift);
string getRSIOnArray(double &array[], int period, int shift, int total);
#endif


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getMA(const string symbol, const ENUM_TIMEFRAMES timeframe, const int maPeriod, const int maShift, const ENUM_MA_METHOD maMethod, const int appliedPriceOrHandle, const int shift)
{
   return DoubleToString(indi.iMA(symbol, timeframe, maPeriod, maShift, maMethod, appliedPriceOrHandle, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getMAOnArray(double &array[], const int period, const int maShift, const ENUM_MA_METHOD maMethod, const int shift)
{
   return DoubleToString(indi.iMAOnArray(array, period, maShift, maMethod, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getRSI(const string symbol, const ENUM_TIMEFRAMES timeframe, const int rsiPeriod, const int appliedPriceOrHandle, const int shift)
{
   return DoubleToString(indi.iRSI(symbol, timeframe, rsiPeriod, appliedPriceOrHandle, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getATR(const string symbol, const ENUM_TIMEFRAMES timeframe, const int atrPeriod, const int shift)
{
   return DoubleToString(indi.iATR(symbol, timeframe, atrPeriod, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getADX(const string symbol, const ENUM_TIMEFRAMES timeframe, const int adxPeriod, ENUM_APPLIED_PRICE appliedPrice, const int adxMode = 0, const int shift = 0)
{
   return DoubleToString(indi.iADX(symbol, timeframe, adxPeriod, appliedPrice, adxMode, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getCustom(const string symbol, const ENUM_TIMEFRAMES timeframe, const string indicatorAndFolderNameOnly = "IndicatorName", const int buffer = 0, const int shift = 1)
{
   return DoubleToString(indi.iCustom(symbol, timeframe, indicatorAndFolderNameOnly, buffer, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getEnvelopes(const string symbol, const ENUM_TIMEFRAMES timeframe, const int envPeriod, const int maShift, const ENUM_MA_METHOD envMethod, const int appliedPriceOrHandle, const double envDeviation, const int envMode = 0, const int shift = 1)
{
   return DoubleToString(indi.iEnvelopes(symbol, timeframe, envPeriod, maShift, envMethod, appliedPriceOrHandle, envDeviation, envMode, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getFractals(const string symbol, const ENUM_TIMEFRAMES timeframe, const int fractalMode = 0, const int shift = 0)
{
   return DoubleToString(indi.iFractals(symbol, timeframe, fractalMode, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getMACD(const string symbol, const ENUM_TIMEFRAMES timeframe, const int fastPeriod, const int slowPeriod, const int signalPeriod, ENUM_APPLIED_PRICE appliedPrice, const int macdMode = 0, const int shift = 0)
{
   return DoubleToString(indi.iMACD(symbol, timeframe, fastPeriod, slowPeriod, signalPeriod, appliedPrice, macdMode, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getAO(const string symbol, const ENUM_TIMEFRAMES timeframe, const int shift = 0)
{
   return DoubleToString(indi.iAO(symbol, timeframe, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getMomentum(const string symbol, const ENUM_TIMEFRAMES timeframe, const int momemtumPeriod, ENUM_APPLIED_PRICE appliedPrice, const int shift = 0)
{
   return DoubleToString(indi.iMomentum(symbol, timeframe, momemtumPeriod, appliedPrice, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getWPR(const string symbol, const ENUM_TIMEFRAMES timeframe, const int wprPeriod, const int shift = 0)
{
   return DoubleToString(indi.iWPR(symbol, timeframe, wprPeriod, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getBullsPower(const string symbol, const ENUM_TIMEFRAMES timeframe, const int bullPeriod, ENUM_APPLIED_PRICE appliedPrice, const int shift = 0)
{
   return DoubleToString(indi.iBullsPower(symbol, timeframe, bullPeriod, appliedPrice, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getBearsPower(const string symbol, const ENUM_TIMEFRAMES timeframe, const int bearPeriod, ENUM_APPLIED_PRICE appliedPrice, const int shift = 0)
{
   return DoubleToString(indi.iBearsPower(symbol, timeframe, bearPeriod, appliedPrice, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getATHR(const string symbol, const ENUM_TIMEFRAMES timeframe, const int shift = 0)
{
   return DoubleToString(indi.iATHR(symbol, timeframe, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getStochastic(const string symbol, const ENUM_TIMEFRAMES timeframe, const int kPeriod, const int dPeriod, const int slowPeriod, const ENUM_MA_METHOD maMethod, ENUM_STO_PRICE stoPrice, const int stochMode = MODE_SIGNAL, const int shift = 0)
{
   return DoubleToString(indi.iStochastic(symbol, timeframe, kPeriod, dPeriod, slowPeriod, maMethod, stoPrice, stochMode, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getCCI(const string symbol, const ENUM_TIMEFRAMES timeframe, const int cciPeriod, ENUM_APPLIED_PRICE appliedPrice, const int shift = 0)
{
   return DoubleToString(indi.iCCI(symbol, timeframe, cciPeriod, appliedPrice, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getADR(const string symbol, const int period, const int shift)
{
   return DoubleToString(indi.iADR(symbol, period, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getVWAP(const string symbol, const ENUM_TIMEFRAMES timeframe, const int period, const int shift)
{
   return DoubleToString(indi.iVWAP(symbol, timeframe, period, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getPVI(const string symbol, const ENUM_TIMEFRAMES timeframe, const ENUM_APPLIED_VOLUME volumeType, const int shift)
{
   return DoubleToString(indi.iPVI(symbol, timeframe, volumeType, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getPVI(const string symbol, const ENUM_TIMEFRAMES timeframe, const ENUM_APPLIED_VOLUME volumeType, const double & closeData[], const int shift)
{
   return DoubleToString(indi.iPVI(symbol, timeframe, volumeType, closeData, shift));
}

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string getRSIOnArray(double &array[], int period, int shift, int total = 0)
{
   return DoubleToString(indi.iRSIOnArray(array, period, shift, total));
}
//+------------------------------------------------------------------+
