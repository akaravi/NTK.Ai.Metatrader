//+------------------------------------------------------------------+
//|                                                       symbol.mq5 |
//|                                          Copyright 2026,JBlanked |
//|                                        https://www.jblanked.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked"
#property link      "https://www.jblanked.com/"
#property version   "1.00"
#property strict

#include <metatrader-ai/mql/tools/mt5.mqh>

#define SYMBOL            "ETHUSD"
#define BARS_PER_TIMEFRAME 3

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OnStart()
{
// --- symbol info ---
   Print("--- Symbol info: ", SYMBOL, " ---");
   string infoStr = getSymbolInfo(SYMBOL);
   if (infoStr == "" || infoStr == "{}")
   {
      Print("Could not retrieve symbol info for ", SYMBOL, ".");
      return;
   }

   CJAVal info;
   info.Deserialize(infoStr);
   Print("  bid=",     info["bid"].ToDbl(),
         "  ask=",     info["ask"].ToDbl(),
         "  spread=",  info["spread"].ToDbl(),
         "  digits=",  info["digits"].ToInt(),
         "  point=",   info["point"].ToDbl(),
         "  max_lot=", info["max_lot_size"].ToDbl());

// --- recent bars across multiple timeframes ---
   ENUM_TIMEFRAMES timeframes[] = { PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_M30, PERIOD_H1, PERIOD_H4, PERIOD_D1 };
   string          labels[]     = { "M1", "M5", "M15", "M30", "H1", "H4", "D1" };

   for (int t = 0; t < ArraySize(timeframes); t++)
   {
      Print("--- ", labels[t], " bars (last ", BARS_PER_TIMEFRAME, ") ---");
      string barsStr = getRecentBars(SYMBOL, timeframes[t], BARS_PER_TIMEFRAME);
      if (barsStr == "" || barsStr == "{}")
      {
         Print("  No bars returned for ", labels[t], ".");
         continue;
      }

      CJAVal barsResult;
      barsResult.Deserialize(barsStr);
      int n = ArraySize(barsResult["bars"].m_e);
      for (int i = 0; i < n; i++)
      {
         Print("  O=",   barsResult["bars"][i]["open"].ToDbl(),
               "  H=",   barsResult["bars"][i]["high"].ToDbl(),
               "  L=",   barsResult["bars"][i]["low"].ToDbl(),
               "  C=",   barsResult["bars"][i]["close"].ToDbl(),
               "  vol=", barsResult["bars"][i]["tick_volume"].ToInt());
      }
   }

// --- iXxx helpers at shift=1 for H1 and D1 ---
   ENUM_TIMEFRAMES testTfs[]    = { PERIOD_H1, PERIOD_D1 };
   string          testLabels[] = { "H1", "D1" };

   for (int t = 0; t < ArraySize(testTfs); t++)
   {
      Print("--- iXxx helpers at shift=1 (", testLabels[t], ") ---");
      datetime dt    = iTime(SYMBOL,  testTfs[t], 1);
      double   open  = iOpen(SYMBOL,  testTfs[t], 1);
      double   high  = iHigh(SYMBOL,  testTfs[t], 1);
      double   low   = iLow(SYMBOL,   testTfs[t], 1);
      double   close = iClose(SYMBOL, testTfs[t], 1);

      if (dt == 0)
      {
         Print("  Failed to read ", testLabels[t], " bar data.");
         continue;
      }

      Print("  time=",  TimeToString(dt),
            "  open=",  open,
            "  high=",  high,
            "  low=",   low,
            "  close=", close);
      Print("  ", testLabels[t], " bar data read successfully.");
   }
}
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
