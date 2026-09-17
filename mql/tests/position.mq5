//+------------------------------------------------------------------+
//|                                                     position.mq5 |
//|                                          Copyright 2026,JBlanked |
//|                                        https://www.jblanked.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked"
#property link      "https://www.jblanked.com/"
#property version   "1.00"
#property strict

#include <metatrader-ai/mql/tools/mt5.mqh>

#define SYMBOL "ETHUSD"
#define LOT     0.01

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OnStart()
{
// --- place a market buy order ---
   bool ok = orderSend(SYMBOL, ORDER_TYPE_BUY, LOT, 0, 3, 0, 0);
   if (!ok)
   {
      Print("Failed to place market buy order.");
      return;
   }
   Print("Market buy order placed successfully.");

// --- find the open position ---
   string posStr = getPositions(SYMBOL);
   if (posStr == "" || posStr == "{}")
   {
      Print("No open positions found after placing order.");
      return;
   }

   CJAVal positions;
   positions.Deserialize(posStr);
   if (ArraySize(positions["positions"].m_e) == 0)
   {
      Print("No open positions found after placing order.");
      return;
   }

   ulong ticket = (ulong)positions["positions"][0]["ticket"].ToInt();
   Print("Position ticket: ", ticket);

// --- close the position ---
   ok = positionClose(ticket);
   if (!ok)
   {
      Print("Failed to close position ", ticket, ".");
      return;
   }
   Print("Position ", ticket, " closed successfully.");
}
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
