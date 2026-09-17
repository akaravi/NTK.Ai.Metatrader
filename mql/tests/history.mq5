//+------------------------------------------------------------------+
//|                                                      history.mq5 |
//|                                          Copyright 2026,JBlanked |
//|                                        https://www.jblanked.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked"
#property link      "https://www.jblanked.com/"
#property version   "1.00"
#property strict

#include <metatrader-ai/mql/tools/mt5.mqh>

#define SYMBOL "ETHUSD"

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OnStart()
{
// --- get all historical positions for the current year ---
   string histStr = getHistoryPositions();
   if (histStr == "" || histStr == "{}")
   {
      Print("No historical positions found for the current year.");
      return;
   }

   CJAVal hist;
   hist.Deserialize(histStr);
   int total = ArraySize(hist["positions"].m_e);
   if (total == 0)
   {
      Print("No historical positions found for the current year.");
      return;
   }

   Print("Found ", total, " historical deal(s).");
   int printCount = MathMin(total, 5); // print first 5 for brevity
   for (int i = 0; i < printCount; i++)
   {
      Print("  ticket=", hist["positions"][i]["ticket"].ToInt(),
            "  symbol=", hist["positions"][i]["symbol"].ToStr(),
            "  type=",   hist["positions"][i]["type"].ToInt(),
            "  volume=", hist["positions"][i]["lot_size"].ToDbl(),
            "  price=",  hist["positions"][i]["price"].ToDbl(),
            "  profit=", hist["positions"][i]["profit"].ToDbl(),
            "  time=",   hist["positions"][i]["time"].ToStr());
   }

// --- get all deals for the first closed position ---
   ulong ticket = (ulong)hist["positions"][0]["ticket"].ToInt();
   Print("\nFetching all deals for ticket ", ticket, "...");

   string dealStr = getHistoryPosition(ticket);
   if (dealStr == "" || dealStr == "{}")
   {
      Print("No deal found for ticket ", ticket, ".");
      return;
   }

   Print("Deal for ticket ", ticket, ": ", dealStr);

// --- filter history by symbol ---
   Print("\nFetching historical positions filtered by symbol ", SYMBOL, "...");
   string symHistStr = getHistoryPositions(SYMBOL);
   if (symHistStr == "" || symHistStr == "{}")
   {
      Print("No historical positions found for ", SYMBOL, ".");
      return;
   }

   CJAVal symHist;
   symHist.Deserialize(symHistStr);
   int symTotal = ArraySize(symHist["positions"].m_e);
   if (symTotal == 0)
      Print("No historical positions found for ", SYMBOL, ".");
   else
      Print("Found ", symTotal, " historical deal(s) for ", SYMBOL, ".");
}
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
