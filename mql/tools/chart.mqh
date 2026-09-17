//+------------------------------------------------------------------+
//|                                                        chart.mqh |
//|                                      Copyright 2026,JBlanked LLC |
//|                                         https://www.jblanked.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked LLC"
#property link      "https://www.jblanked.com"
#property strict

#include  "JSON.mqh"

// forwards (in mql4 is shows import warning)
#ifdef __MQL5__
string chartClose(long chartId = 0);
string chartOpen(const string symbol, ENUM_TIMEFRAMES timeframe);
string getChartInfo(long chartId = 0);
string getChartIndicator(const string indicatorName);
string removeChartIndicator(const string indicatorName, long chartId = 0, int subWindow = 0);
#endif

//+------------------------------------------------------------------+
//| Close a chart                                                    |
//+------------------------------------------------------------------+
string chartClose(long chartId = 0)
{
   ResetLastError();
   return ChartClose(chartId) ? "Chart closed successfully" : StringFormat("Chart failed to close! Error: %d", GetLastError());
}

//+------------------------------------------------------------------+
//| Open a chart                                                     |
//+------------------------------------------------------------------+
string chartOpen(const string symbol, ENUM_TIMEFRAMES timeframe)
{
   ResetLastError();
   return ChartOpen(symbol, timeframe) != 0 ? "Chart opened successfully" : StringFormat("Chart failed to open! Error: %d", GetLastError());
}

//+------------------------------------------------------------------+
//| Get a dictionary of general chart information                    |
//+------------------------------------------------------------------+
string getChartInfo(long chartId = 0)
{
   CJAVal result;
   result.m_type = jtOBJ;

   result["id"]             = ChartID();
   result["symbol"]         = ChartSymbol(chartId);
   result["timeframe"]      = EnumToString(ChartPeriod(chartId));
   result["first_chart_id"] = ChartFirst();
   result["next_chart_id"]  = ChartNext(chartId);
   result["comment"]        = ChartGetString(chartId, CHART_COMMENT);
   result["current_expert"] = ChartGetString(chartId, CHART_EXPERT_NAME);
   result["current_script"] = ChartGetString(chartId, CHART_SCRIPT_NAME);
   result["mode"]           = EnumToString((ENUM_CHART_MODE)ChartGetInteger(chartId, CHART_MODE));
   result["handle"]         = ChartGetInteger(chartId, CHART_WINDOW_HANDLE);
   result["window_count"]   = ChartGetInteger(chartId, CHART_WINDOWS_TOTAL);
   result["bar_count"]      = ChartGetInteger(chartId, CHART_VISIBLE_BARS);
   result["ask"]            = SymbolInfoDouble(ChartSymbol(chartId), SYMBOL_ASK);
   result["bid"]            = SymbolInfoDouble(ChartSymbol(chartId), SYMBOL_BID);

   CJAVal windowArr;
   windowArr.m_type = jtARRAY;
   for(int i = 0; i < result["window_count"].ToInt(); i++)
   {
      CJAVal windowInfo;
      windowInfo["height"]          = ChartGetInteger(chartId, CHART_HEIGHT_IN_PIXELS, i);
      windowInfo["width"]           = ChartGetInteger(chartId, CHART_WIDTH_IN_PIXELS, i);
      windowInfo["price_min"]       = ChartGetDouble(chartId, CHART_PRICE_MIN, i);
      windowInfo["price_max"]       = ChartGetDouble(chartId, CHART_PRICE_MAX, i);
      windowInfo["indicator_count"] = ChartIndicatorsTotal(chartId, i);

      CJAVal iArray;
      iArray.m_type = jtARRAY;
      for(int j = 0; j < windowInfo["indicator_count"].ToInt(); j++)
      {
         CJAVal indiInfo;
         const string name  = ChartIndicatorName(chartId, i, j);
         indiInfo["name"]   = name;
         indiInfo["handle"] = ChartIndicatorGet(chartId, i, name);
         indiInfo["window"] = i;
         iArray.Add(indiInfo);
      }
      windowInfo["indicator_data"].Set(iArray);
      windowArr.Add(windowInfo);
   }
   result["window_info"].Set(windowArr);

   return result.Serialize();
}

//+------------------------------------------------------------------+
//| Find an indicator, returns a list of indicator information       |
//+------------------------------------------------------------------+
string getChartIndicator(const string indicatorName)
{
   CJAVal result;
   result.m_type = jtARRAY;
   const long chartId = ChartID();
   bool found = false;
   for(int i = 0; i < (int)ChartGetInteger(chartId, CHART_WINDOWS_TOTAL); i++)
   {
      for(int j = 0; j < ChartIndicatorsTotal(chartId, i); j++)
      {
         const string name  = ChartIndicatorName(chartId, i, j);
         if(name != indicatorName) continue;

         CJAVal info;
         info["name"]   = name;
         info["handle"] = ChartIndicatorGet(chartId, i, name);
         info["window"] = i;
         result.Add(info);
         found = true;
      }
   }
   return found ? result.Serialize() : "Indicator not found";
}

//+------------------------------------------------------------------+
//| Remove an indicator from the chart                               |
//+------------------------------------------------------------------+
string removeChartIndicator(const string indicatorName, long chartId = 0, int subWindow = 0)
{
   ResetLastError();
   return ChartIndicatorDelete(chartId, subWindow, indicatorName) ? "Indicator removed successfully" : StringFormat("Failed to remove indicator! Error: %d", GetLastError());
}
//+------------------------------------------------------------------+
