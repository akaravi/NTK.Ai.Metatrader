//+------------------------------------------------------------------+
//|                                                        order.mq5 |
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
// --- get symbol info to find ask price ---
   string infoStr = getSymbolInfo(SYMBOL);
   if (infoStr == "" || infoStr == "{}")
   {
      Print("Could not retrieve price for ", SYMBOL, ".");
      return;
   }

   CJAVal info;
   info.Deserialize(infoStr);
   double ask = info["ask"].ToDbl();
   if (ask == 0)
   {
      Print("Could not retrieve price for ", SYMBOL, ".");
      return;
   }

   double limitPrice = NormalizeDouble(ask * 0.90, 2); // 10% below ask — stays pending
   Print("Current ASK: ", ask, "  ->  placing BUY LIMIT at: ", limitPrice);

// --- place a pending buy limit order ---
   bool ok = orderSend(SYMBOL, ORDER_TYPE_BUY_LIMIT, LOT, limitPrice, 3, 0, 0);
   if (!ok)
   {
      Print("Failed to place pending buy limit order.");
      return;
   }
   Print("Pending buy limit order placed successfully.");

// --- find the pending order ---
   string ordersStr = getOrders(SYMBOL);
   if (ordersStr == "" || ordersStr == "{}")
   {
      Print("No pending orders found after placing order.");
      return;
   }

   CJAVal orders;
   orders.Deserialize(ordersStr);
   if (ArraySize(orders["orders"].m_e) == 0)
   {
      Print("No pending orders found after placing order.");
      return;
   }

   ulong ticket = (ulong)orders["orders"][0]["ticket"].ToInt();
   Print("Pending order ticket: ", ticket);

// --- delete the pending order ---
   ok = orderDelete(ticket);
   if (!ok)
   {
      Print("Failed to delete order ", ticket, ".");
      return;
   }
   Print("Pending order ", ticket, " deleted successfully.");
}
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
