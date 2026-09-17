//+------------------------------------------------------------------+
//|                                                          mt5.mqh |
//|                                          Copyright 2026,JBlanked |
//|                                        https://www.jblanked.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,JBlanked"
#property link      "https://www.jblanked.com/"
#property strict

#include "JSON.mqh"

#ifdef __MQL5__
#include <Trade\Trade.mqh>
static CTrade mt5Trade;
static CPositionInfo mt5Posi;
#endif

#define CONTAINS(symbol, match) (StringFind(symbol, match) != -1)
#define DIVISION(numerator, denominator) (denominator == 0 ? 0 : numerator / denominator)

#define SCREENSHOT_FILENAME "metatrader-ai"
#define SCREENSHOT_HEIGHT 800
#define SCREENSHOT_WIDTH 600

// forwards (in mql4 is shows import warning)
#ifdef __MQL5__
string base64Encode(const uchar &data[], int length);
string getAccountInfo();
string getBars(const string symbol, const ENUM_TIMEFRAMES timeframe, const datetime fromDate, const datetime toDate);
string getHistoryPosition(const ulong ticket);
string getHistoryPositions(const string symbol = "", const long magic = 0, const datetime fromDate = 0, const datetime toDate = 0);
string getOrder(const ulong ticket);
string getOrders(const string symbol = "");
double getPipValue(const string symbol);
string getPosition(const ulong ticket);
string getPositions(const string symbol = "");
string getRecentBars(const string symbol, const ENUM_TIMEFRAMES timeframe, const int numberOfBars, const int shift = 0);
double getRisk(const string symbol, const double percentRisk, const double stopLossPips);
string getScreenshot(const string symbol = "", const ENUM_TIMEFRAMES timeframe = PERIOD_CURRENT);
string getSymbolInfo(const string symbol);
bool isOrderOpened(const string symbol = "", const long magic = 0);
bool isPositionOpened(const string symbol = "", const long magic = 0);
bool orderDelete(const ulong ticket);
bool orderSend(const string symbol, ENUM_ORDER_TYPE type, const double volume, const double price, const int slippage, const double stopLoss, const double takeProfit, const string comment = "", const long magic = 0);
bool orderSendPips(const string symbol, ENUM_ORDER_TYPE type, const double volume, const double price, const int slippage, const double stoplossPips, const double takeprofitPips, const string comment = "", const long magic = 0);
bool orderModify(const ulong ticket, const double price, const double stopLoss, const double takeProfit);
bool positionClose(const ulong ticket);
bool positionModify(const string symbol, const ulong ticket, const double stopLoss, const double takeProfit);
bool selectSymbol(const string symbol, const bool enable = true);
#endif
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| base64-encode raw bytes                                          |
//+------------------------------------------------------------------+
string base64Encode(const uchar &data[], int length)
{
   const string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
   string result = "";
   int i = 0;
   while(i < length)
   {
      uint b0 = (uint)(uchar)data[i++];
      uint b1 = (i < length) ? (uint)(uchar)data[i++] : 0;
      uint b2 = (i < length) ? (uint)(uchar)data[i++] : 0;
      result += StringSubstr(chars, (b0 >> 2) & 0x3F, 1);
      result += StringSubstr(chars, ((b0 << 4) | (b1 >> 4)) & 0x3F, 1);
      result += (i - 1 < length || i <= length + 1) ? StringSubstr(chars, ((b1 << 2) | (b2 >> 6)) & 0x3F, 1) : "=";
      result += (i <= length) ? StringSubstr(chars, b2 & 0x3F, 1) : "=";
   }
   return StringLen(result) > 0 ? result : "Failed to encode base64";
}

//+------------------------------------------------------------------+
//| Get account information as a dictionary                          |
//+------------------------------------------------------------------+
string getAccountInfo(void)
{
   CJAVal result;
   result["number"]       = AccountInfoInteger(ACCOUNT_LOGIN);
   result["name"]         = AccountInfoString(ACCOUNT_NAME);
   result["balance"]      = AccountInfoDouble(ACCOUNT_BALANCE);
   result["equity"]       = AccountInfoDouble(ACCOUNT_EQUITY);
   result["margin"]       = AccountInfoDouble(ACCOUNT_MARGIN);
   result["free_margin"]  = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   result["margin_level"] = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
   result["currency"]     = AccountInfoString(ACCOUNT_CURRENCY);
   result["company"]      = AccountInfoString(ACCOUNT_COMPANY);
   result["profit"]       = AccountInfoDouble(ACCOUNT_PROFIT);
   return result.Serialize();
}

//+------------------------------------------------------------------+
//| Get rates for a specific symbol, timeframe, and range            |
//+------------------------------------------------------------------+
string getBars(const string symbol, const ENUM_TIMEFRAMES timeframe, const datetime fromDate, const datetime toDate)
{
   CJAVal result;
   MqlRates rates[];
   if(CopyRates(symbol, timeframe, fromDate, toDate, rates) == -1)
   {
      return StringFormat("Failed to fetch rates for %s", symbol);
   }
   for(int i = 0; i < ArraySize(rates); i++)
   {
      result["bars"][i]["close"]       = rates[i].close;
      result["bars"][i]["open"]        = rates[i].open;
      result["bars"][i]["high"]        = rates[i].high;
      result["bars"][i]["low"]         = rates[i].low;
      result["bars"][i]["spread"]      = rates[i].spread;
      result["bars"][i]["tick_volume"] = rates[i].tick_volume;
      result["bars"][i]["real_volume"] = rates[i].real_volume;
   }
   return result.Serialize();
}

//+------------------------------------------------------------------+
//| Get all deals related to the ticket number of a closed position  |
//+------------------------------------------------------------------+
string getHistoryPosition(const ulong ticket)
{
   CJAVal result;
   bool positionFound = false;
#ifdef __MQL5__
   if(HistoryDealSelect(ticket))
   {
      result["ticket"]     = (long)ticket;
      result["order"]      = (long)HistoryDealGetInteger(ticket, DEAL_ORDER);
      result["time"]       = TimeToString((datetime)HistoryDealGetInteger(ticket, DEAL_TIME));
      result["type"]       = (int)HistoryDealGetInteger(ticket, DEAL_TYPE);
      result["entry"]      = (int)HistoryDealGetInteger(ticket, DEAL_ENTRY);
      result["magic"]      = HistoryDealGetInteger(ticket, DEAL_MAGIC);
      result["volume"]     = HistoryDealGetDouble(ticket, DEAL_VOLUME);
      result["price"]      = HistoryDealGetDouble(ticket, DEAL_PRICE);
      result["commission"] = HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      result["swap"]       = HistoryDealGetDouble(ticket, DEAL_SWAP);
      result["profit"]     = HistoryDealGetDouble(ticket, DEAL_PROFIT);
      result["fee"]        = HistoryDealGetDouble(ticket, DEAL_FEE);
      result["symbol"]     = HistoryDealGetString(ticket, DEAL_SYMBOL);
      result["comment"]    = HistoryDealGetString(ticket, DEAL_COMMENT);
      positionFound        = true;
   }
   else
   {
      PrintFormat("HistoryDealSelect(%I64u) failed. Error %d", ticket, GetLastError());
   }
#else
   if(OrderSelect((int)ticket, SELECT_BY_TICKET))
   {
      result["ticket"]     = OrderTicket();
      result["time"]       = TimeToString((datetime)OrderOpenTime());
      result["type"]       = OrderType();
      result["magic"]      = OrderMagicNumber();
      result["volume"]     = OrderLots();
      result["price"]      = OrderOpenPrice();
      result["commission"] = OrderCommission();
      result["swap"]       = OrderSwap();
      result["profit"]     = OrderProfit();
      result["symbol"]     = OrderSymbol();
      result["comment"]    = OrderComment();
      positionFound        = true;
   }
#endif
   return positionFound ? result.Serialize() : "Position not found.";
}

//+------------------------------------------------------------------+
//| Get historical positions, optionally filtered                    |
//+------------------------------------------------------------------+
string getHistoryPositions(const string symbol = "", const long magic = 0, const datetime fromDate = 0, const datetime toDate = 0)
{
   CJAVal result;
   int count = 0;
   datetime _fromDate = fromDate == 0 ? (datetime)0 : fromDate;
   datetime _toDate   = toDate == 0 ? TimeCurrent() : toDate;
#ifdef __MQL5__
   if(HistorySelect(_fromDate, _toDate))
   {
      for(int i = 0; i < HistoryDealsTotal(); i++)
      {
         ulong dealTicket = HistoryDealGetTicket(i);
         string dealSymbol = HistoryDealGetString(dealTicket, DEAL_SYMBOL);
         long   dealMagic  = HistoryDealGetInteger(dealTicket, DEAL_MAGIC);
         if(symbol != "" && dealSymbol != symbol) continue;
         if(magic  != 0  && dealMagic  != magic)  continue;
         result["positions"][count]["ticket"]      = (long)dealTicket;
         result["positions"][count]["time"]        = TimeToString((datetime)HistoryDealGetInteger(dealTicket, DEAL_TIME));
         result["positions"][count]["type"]        = (int)HistoryDealGetInteger(dealTicket, DEAL_TYPE);
         result["positions"][count]["entry"]       = (int)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
         result["positions"][count]["magic_number"] = dealMagic;
         result["positions"][count]["lot_size"]    = HistoryDealGetDouble(dealTicket, DEAL_VOLUME);
         result["positions"][count]["price"]       = HistoryDealGetDouble(dealTicket, DEAL_PRICE);
         result["positions"][count]["commission"]  = HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
         result["positions"][count]["swap"]        = HistoryDealGetDouble(dealTicket, DEAL_SWAP);
         result["positions"][count]["profit"]      = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
         result["positions"][count]["fee"]         = HistoryDealGetDouble(dealTicket, DEAL_FEE);
         result["positions"][count]["symbol"]      = dealSymbol;
         result["positions"][count]["comment"]     = HistoryDealGetString(dealTicket, DEAL_COMMENT);
         count++;
      }
   }
#else
   for(int i = OrdersHistoryTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
      {
         if(symbol != "" && OrderSymbol() != symbol) continue;
         if(magic  != 0  && OrderMagicNumber() != (int)magic) continue;
         datetime orderTime = (datetime)OrderOpenTime();
         if(orderTime < _fromDate || orderTime > _toDate) continue;
         result["positions"][count]["ticket"]       = OrderTicket();
         result["positions"][count]["time"]         = TimeToString(orderTime);
         result["positions"][count]["type"]         = OrderType();
         result["positions"][count]["magic_number"] = OrderMagicNumber();
         result["positions"][count]["lot_size"]     = OrderLots();
         result["positions"][count]["price"]        = OrderOpenPrice();
         result["positions"][count]["commission"]   = OrderCommission();
         result["positions"][count]["swap"]         = OrderSwap();
         result["positions"][count]["profit"]       = OrderProfit();
         result["positions"][count]["symbol"]       = OrderSymbol();
         result["positions"][count]["comment"]      = OrderComment();
         count++;
      }
   }
#endif
   return count > 0 ? result.Serialize() : "No historical positions found.";
}

//+------------------------------------------------------------------+
//| Get a specific pending order by ticket number                    |
//+------------------------------------------------------------------+
string getOrder(const ulong ticket)
{
   CJAVal result;
   bool orderFound = false;
#ifdef __MQL5__
   if(OrderSelect(ticket))
   {
      result["magic"]         = OrderGetInteger(ORDER_MAGIC);
      result["symbol"]        = OrderGetString(ORDER_SYMBOL);
      result["type"]          = OrderGetInteger(ORDER_TYPE);
      result["comment"]       = OrderGetString(ORDER_COMMENT);
      result["stop_loss"]     = OrderGetDouble(ORDER_SL);
      result["take_profit"]   = OrderGetDouble(ORDER_TP);
      result["lot_size"]      = OrderGetDouble(ORDER_VOLUME_CURRENT);
      result["price_open"]    = OrderGetDouble(ORDER_PRICE_OPEN);
      result["price_current"] = OrderGetDouble(ORDER_PRICE_CURRENT);
      result["time_open"]     = TimeToString((datetime)OrderGetInteger(ORDER_TIME_SETUP));
      result["time_expire"]   = TimeToString((datetime)OrderGetInteger(ORDER_TIME_EXPIRATION));
      orderFound              = true;
   }
#else
   if(OrderSelect((int)ticket, SELECT_BY_TICKET)) // select the order
   {
      result["magic"]         = OrderMagicNumber();
      result["symbol"]        = OrderSymbol();
      result["type"]          = OrderType();
      result["comment"]       = OrderComment();
      result["stop_loss"]     = OrderStopLoss();
      result["take_profit"]   = OrderTakeProfit();
      result["lot_size"]      = OrderLots();
      result["price_open"]    = OrderOpenPrice();
      result["price_current"] = OrderClosePrice();
      result["time_open"]     = TimeToString((datetime)OrderOpenTime());
      result["time_expire"]   = TimeToString((datetime)OrderExpiration());
      orderFound              = true;
   }
#endif
   return orderFound ? result.Serialize() : "Order not found.";
}

//+------------------------------------------------------------------+
//| Get all pending orders, optionally filtered by symbol            |
//+------------------------------------------------------------------+
string getOrders(const string symbol = "")
{
   CJAVal result;
   int count = 0;
#ifdef __MQL5__
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(!OrderSelect(ticket)) continue;
      string orderSymbol = OrderGetString(ORDER_SYMBOL);
      if(symbol != "" && orderSymbol != symbol) continue;
      result["orders"][count]["ticket"]          = (long)ticket;
      result["orders"][count]["magic_number"]    = OrderGetInteger(ORDER_MAGIC);
      result["orders"][count]["symbol"]          = orderSymbol;
      result["orders"][count]["type"]            = (int)OrderGetInteger(ORDER_TYPE);
      result["orders"][count]["comment"]         = OrderGetString(ORDER_COMMENT);
      result["orders"][count]["stop_loss"]       = OrderGetDouble(ORDER_SL);
      result["orders"][count]["take_profit"]     = OrderGetDouble(ORDER_TP);
      result["orders"][count]["lot_size"]        = OrderGetDouble(ORDER_VOLUME_CURRENT);
      result["orders"][count]["open_price"]      = OrderGetDouble(ORDER_PRICE_OPEN);
      result["orders"][count]["current_price"]   = OrderGetDouble(ORDER_PRICE_CURRENT);
      result["orders"][count]["time_setup"]      = TimeToString((datetime)OrderGetInteger(ORDER_TIME_SETUP));
      result["orders"][count]["time_expiration"] = TimeToString((datetime)OrderGetInteger(ORDER_TIME_EXPIRATION));
      count++;
   }
#else
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS)) continue;
      if(OrderType() != OP_BUYSTOP && OrderType() != OP_SELLSTOP &&
            OrderType() != OP_BUYLIMIT && OrderType() != OP_SELLLIMIT) continue;
      if(symbol != "" && OrderSymbol() != symbol) continue;
      result["orders"][count]["ticket"]          = OrderTicket();
      result["orders"][count]["magic_number"]    = OrderMagicNumber();
      result["orders"][count]["symbol"]          = OrderSymbol();
      result["orders"][count]["type"]            = OrderType();
      result["orders"][count]["comment"]         = OrderComment();
      result["orders"][count]["stop_loss"]       = OrderStopLoss();
      result["orders"][count]["take_profit"]     = OrderTakeProfit();
      result["orders"][count]["lot_size"]        = OrderLots();
      result["orders"][count]["open_price"]      = OrderOpenPrice();
      result["orders"][count]["current_price"]   = OrderClosePrice();
      result["orders"][count]["time_setup"]      = TimeToString((datetime)OrderOpenTime());
      result["orders"][count]["time_expiration"] = TimeToString((datetime)OrderExpiration());
      count++;
   }
#endif
   return count > 0 ? result.Serialize() : "No open orders found.";
}
//+------------------------------------------------------------------+
//| Get the pip value for a specific symbol                          |
//+------------------------------------------------------------------+
double getPipValue(const string symbol)
{
   const double _pips = SymbolInfoDouble(symbol, SYMBOL_POINT) * 10;
   const double digits = int(SymbolInfoInteger(symbol, SYMBOL_DIGITS));

   if(symbol == "" || digits == 0)
   {
      return _pips;
   }

   if(digits >= 4) return 0.0001;
   if(digits == 3) return 0.01;

   if(CONTAINS(symbol, "XAU"))
   {
      return 0.10; // gold
   }

   if(CONTAINS(symbol, "US30") || CONTAINS(symbol, "NAS100") || CONTAINS(symbol, "SPX500") || CONTAINS(symbol, "UK100") || CONTAINS(symbol, "JPY225") || CONTAINS(symbol, "FRA40"))
   {
      return 1.0; // indices
   }

   if(CONTAINS(symbol, "ETHUSD") || CONTAINS(symbol, "BTCUSD"))
   {
      return 1.0; // crypto
   }

   return _pips;
}

//+------------------------------------------------------------------+
//| Get a specific open position by ticket number                    |
//+------------------------------------------------------------------+
string getPosition(const ulong ticket)
{
   CJAVal result;
   bool positionFound = false;
#ifdef __MQL5__
   if(mt5Posi.SelectByTicket(ticket)) // select the order
   {
      result["magic"]         = mt5Posi.Magic();
      result["symbol"]        = mt5Posi.Symbol();
      result["type"]          = (int)mt5Posi.PositionType();
      result["comment"]       = mt5Posi.Comment();
      result["stop_loss"]     = mt5Posi.StopLoss();
      result["take_profit"]   = mt5Posi.TakeProfit();
      result["lot_size"]      = mt5Posi.Volume();
      result["price_open"]    = mt5Posi.PriceOpen();
      result["price_current"] = mt5Posi.PriceCurrent();
      result["time_open"]     = TimeToString(mt5Posi.Time());
      positionFound           = true;
   }
#else
   if(OrderSelect((int)ticket, SELECT_BY_TICKET)) // select the order
   {
      result["magic"]         = OrderMagicNumber();
      result["symbol"]        = OrderSymbol();
      result["type"]          = OrderType();
      result["comment"]       = OrderComment();
      result["stop_loss"]     = OrderStopLoss();
      result["take_profit"]   = OrderTakeProfit();
      result["lot_size"]      = OrderLots();
      result["price_open"]    = OrderOpenPrice();
      result["price_current"] = OrderClosePrice();
      result["time_open"]     = TimeToString((datetime)OrderOpenTime());
      positionFound           = true;
   }
#endif
   return positionFound ? result.Serialize() : "Position not found.";
}

//+------------------------------------------------------------------+
//| Get all open positions, optionally filtered by symbol            |
//+------------------------------------------------------------------+
string getPositions(const string symbol = "")
{
   CJAVal result;
   int count = 0;
#ifdef __MQL5__
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!mt5Posi.SelectByIndex(i)) continue;
      if(symbol != "" && mt5Posi.Symbol() != symbol) continue;
      result["positions"][count]["ticket"]        = (long)mt5Posi.Ticket();
      result["positions"][count]["magic_number"]  = mt5Posi.Magic();
      result["positions"][count]["symbol"]        = mt5Posi.Symbol();
      result["positions"][count]["type"]          = (int)mt5Posi.PositionType();
      result["positions"][count]["comment"]       = mt5Posi.Comment();
      result["positions"][count]["stop_loss"]     = mt5Posi.StopLoss();
      result["positions"][count]["take_profit"]   = mt5Posi.TakeProfit();
      result["positions"][count]["lot_size"]      = mt5Posi.Volume();
      result["positions"][count]["open_price"]    = mt5Posi.PriceOpen();
      result["positions"][count]["current_price"] = mt5Posi.PriceCurrent();
      result["positions"][count]["profit"]        = mt5Posi.Profit();
      result["positions"][count]["swap"]          = mt5Posi.Swap();
      result["positions"][count]["time_open"]     = TimeToString(mt5Posi.Time());
      count++;
   }
#else
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS)) continue;
      if(OrderType() != OP_BUY && OrderType() != OP_SELL) continue;
      if(symbol != "" && OrderSymbol() != symbol) continue;
      result["positions"][count]["ticket"]        = OrderTicket();
      result["positions"][count]["magic_number"]  = OrderMagicNumber();
      result["positions"][count]["symbol"]        = OrderSymbol();
      result["positions"][count]["type"]          = OrderType();
      result["positions"][count]["comment"]       = OrderComment();
      result["positions"][count]["stop_loss"]     = OrderStopLoss();
      result["positions"][count]["take_profit"]   = OrderTakeProfit();
      result["positions"][count]["lot_size"]      = OrderLots();
      result["positions"][count]["open_price"]    = OrderOpenPrice();
      result["positions"][count]["current_price"] = OrderClosePrice();
      result["positions"][count]["profit"]        = OrderProfit();
      result["positions"][count]["swap"]          = OrderSwap();
      result["positions"][count]["time_open"]     = TimeToString((datetime)OrderOpenTime());
      count++;
   }
#endif
   return count > 0 ? result.Serialize() : "No open positions found";
}

//+------------------------------------------------------------------+
//| Get recent bars for a specific symbol, timeframe, and shift      |
//+------------------------------------------------------------------+
string getRecentBars(const string symbol, const ENUM_TIMEFRAMES timeframe, const int numberOfBars, const int shift = 0)
{
   CJAVal result;
   MqlRates rates[];
   if(CopyRates(symbol, timeframe, shift, numberOfBars, rates) == -1)
   {
      return StringFormat("Failed to fetch rates for %s", symbol);
   }
   for(int i = 0; i < ArraySize(rates); i++)
   {
      result["bars"][i]["close"]       = rates[i].close;
      result["bars"][i]["open"]        = rates[i].open;
      result["bars"][i]["high"]        = rates[i].high;
      result["bars"][i]["low"]         = rates[i].low;
      result["bars"][i]["spread"]      = rates[i].spread;
      result["bars"][i]["tick_volume"] = rates[i].tick_volume;
      result["bars"][i]["real_volume"] = rates[i].real_volume;
   }
   return result.Serialize();
}

//+------------------------------------------------------------------+
//| Get the lot size based on the percentage risk + stop loss in pips|
//+------------------------------------------------------------------+
double getRisk(const string symbol, const double percentRisk, const double stopLossPips)
{
   const double decimalRisk = percentRisk / 100;   // turn user input into risk %
   const double accountRisk = AccountInfoDouble(ACCOUNT_EQUITY) * decimalRisk; // define total risk
   const double pipValue    = getPipValue(symbol);
   const double maxLotSize  = SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE); // contract size

   double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   if(CONTAINS(symbol, ".mini") || AccountInfoString(ACCOUNT_COMPANY) == "FTMO S.R.O.")
   {
      tickValue *= 100;
   }

   const double maxLossInQuoteCurr = accountRisk / tickValue;
   const double quoteDivision      = DIVISION(maxLossInQuoteCurr, (stopLossPips * pipValue));
   const double startingRisk       = DIVISION(quoteDivision, maxLotSize);
   const double riskCurrent        = startingRisk * tickValue;

   return CONTAINS(symbol, "US30") || CONTAINS(symbol, "NAS100") ||
          CONTAINS(symbol, "SPX500") || CONTAINS(symbol, "JPY225") ||
          CONTAINS(symbol, "UK100") || CONTAINS(symbol, "FRA40") ||
          CONTAINS(symbol, "BTCUSD") || CONTAINS(symbol, "ETHUSD") ||
          CONTAINS(symbol, "LTCUSD") || CONTAINS(symbol, "BNBUSD")
          ?
          NormalizeDouble((riskCurrent * tickValue), 2)
          :
          CONTAINS(symbol, "USDJPY") || CONTAINS(symbol, "CADJPY") ||
          CONTAINS(symbol, "EURJPY") || CONTAINS(symbol, "AUDJPY") ||
          CONTAINS(symbol, "NZDJPY") || CONTAINS(symbol, "CHFJPY") ||
          CONTAINS(symbol, "GBPJPY")
          ?
          NormalizeDouble(((riskCurrent * 100) / tickValue), 2)
          :
          NormalizeDouble((riskCurrent), 2);

}

//+------------------------------------------------------------------+
//| Screenshot a chart, optionally switch to symbol/timeframe        |
//+------------------------------------------------------------------+
string getScreenshot(const string symbol = "", const ENUM_TIMEFRAMES timeframe = PERIOD_CURRENT)
{
   ResetLastError();
// switch chart if sym/tf is set but we're not on there
   if((symbol != "" && ChartSymbol() != symbol) || (timeframe != PERIOD_CURRENT && ChartPeriod() != timeframe))
   {
      if(!ChartSetSymbolPeriod(ChartID(), symbol, timeframe))
      {
         return StringFormat("getScreenshot(%s,%d) failed to set symbol/period. Error %d", symbol, timeframe, GetLastError());
      }
   }
// take screenshot
   const string currencyPair = symbol != "" ? symbol : _Symbol;
   if(!ChartScreenShot(ChartID(), SCREENSHOT_FILENAME + " " + currencyPair + ".png", SCREENSHOT_HEIGHT, SCREENSHOT_WIDTH))
   {
      return StringFormat("getScreenshot(%s,%d) failed to screenshot. Error %d", currencyPair, timeframe, GetLastError());
   }
// load screenshot into array
   int res;
   uchar file[];
   res = FileOpen(SCREENSHOT_FILENAME + " " + currencyPair + ".png", FILE_READ | FILE_BIN);
   if(res == INVALID_HANDLE)
   {
      return StringFormat("getScreenshot(%s,%d) failed to open screenshot file. Error %d", currencyPair, timeframe, GetLastError());
   }

   ulong fileSize = FileSize(res);
   if(FileReadArray(res, file, 0, (int)fileSize) != fileSize)
   {
      FileClose(res);
      return StringFormat("getScreenshot(%s,%d) failed to read screenshot file. Error %d", currencyPair, timeframe, GetLastError());
   }
   FileClose(res);
   return base64Encode(file, (int)fileSize);
}

//+------------------------------------------------------------------+
//| Get symbol information for a specific symbol                     |
//+------------------------------------------------------------------+
string getSymbolInfo(const string symbol)
{
   CJAVal result;
   result["tick_value"]   = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   result["spread"]       = SymbolInfoDouble(symbol, SYMBOL_ASK) - SymbolInfoDouble(symbol, SYMBOL_BID);
   result["bid"]          = SymbolInfoDouble(symbol, SYMBOL_BID);
   result["ask"]          = SymbolInfoDouble(symbol, SYMBOL_ASK);
   result["point"]        = SymbolInfoDouble(symbol, SYMBOL_POINT);
   result["front"]        = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
   result["end"]          = SymbolInfoInteger(symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   result["digits"]       = SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   result["max_lot_size"] = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   return result.Serialize();
}

//+------------------------------------------------------------------+
//| Check if there are any pending order opened                      |
//+------------------------------------------------------------------+
bool isOrderOpened(const string symbol = "", const long magic = 0)
{
#ifdef __MQL5__
   for(int i = OrdersTotal() - 1; i >= 0; i--) //count backwards
   {
      if(OrderSelect(OrderGetTicket(i))) // select the order
      {
         bool isMagic  = magic == 0 || OrderGetInteger(ORDER_MAGIC) == magic;
         bool isSymbol = symbol == "" || OrderGetString(ORDER_SYMBOL) == symbol;
         if(isMagic && isSymbol) return true;
      }
   }
#else
   for(int i = OrdersTotal() - 1; i >= 0; i--) //count backwards
   {
      if(OrderSelect(i, SELECT_BY_POS)) // select the order
      {
         if((OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT) &&
               OrderMagicNumber() == (int)magic && OrderSymbol() == symbol)
         {
            return true;
         }
      }
   }
#endif
   return false;
}

//+------------------------------------------------------------------+
//| Check if there are any open positions                            |
//+------------------------------------------------------------------+
bool isPositionOpened(const string symbol = "", const long magic = 0)
{
#ifdef __MQL5__
   for(int i = PositionsTotal() - 1; i >= 0; i--) //count backwards
   {
      if(mt5Posi.SelectByIndex(i)) // select the order
      {
         bool isSymbol = symbol == "" || mt5Posi.Symbol() == symbol;
         bool isMagic  = magic == 0 || mt5Posi.Magic() == magic;
         if(isSymbol && isMagic) return true;
      }
   }
#else
   for(int i = OrdersTotal() - 1; i >= 0; i--) //count backwards
   {
      if(OrderSelect(i, SELECT_BY_POS)) // select the order
      {
         const int orderType = OrderType();
         if(orderType != OP_BUY && orderType != OP_SELL) continue;
         bool isSymbol = symbol == "" || OrderSymbol() == symbol;
         bool isMagic  = magic == 0 || OrderMagicNumber() == (int)magic;
         if(isSymbol && isMagic) return true;
      }
   }
#endif
   return false;
}

//+------------------------------------------------------------------+
//| Delete a pending order by ticket number                          |
//+------------------------------------------------------------------+
bool orderDelete(const ulong ticket)
{
#ifdef __MQL5__
   return mt5Trade.OrderDelete(ticket);
#else
   return OrderDelete((int)ticket);
#endif
}

//+------------------------------------------------------------------+
//| Send an order: absolute entry, stop-loss, and take-profit prices |
//+------------------------------------------------------------------+
bool orderSend(const string symbol, const ENUM_ORDER_TYPE type, const double volume, const double price, const int slippage, const double stopLoss, const double takeProfit, const string comment = "", const long magic = 0)
{
   double _price = price;
#ifdef __MQL5__
   mt5Trade.SetExpertMagicNumber(magic);
   if(price == 0)
   {
      _price = type == ORDER_TYPE_BUY ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID);
   }
   switch(type)
   {
   case ORDER_TYPE_BUY:
   case ORDER_TYPE_SELL:
      return mt5Trade.PositionOpen(symbol, type, volume, _price, stopLoss, takeProfit, comment);
   default:
      return mt5Trade.OrderOpen(symbol, type, volume, price, price, stopLoss, takeProfit, ORDER_TIME_GTC, 0, comment);
   }
#else
   if(price == 0)
   {
      _price = type == OP_BUY ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID);
   }
   return OrderSend(symbol, type, volume, _price, slippage, stopLoss, takeProfit, comment, (int)magic, 0) > 0;
#endif
   return false;
}

//+------------------------------------------------------------------+
//| Send an order: entry, stop-loss, and take-profit  in pips        |
//+------------------------------------------------------------------+
bool orderSendPips(const string symbol, const ENUM_ORDER_TYPE type, const double volume, const double price, const int slippage, const double stoplossPips, const double takeprofitPips, const string comment = "", const long magic = 0)
{
   const double pipValue = getPipValue(symbol);
   double _price = price;
   double stopLoss = 0.0;
   double takeProfit = 0.0;
#ifdef __MQL5__
   if(price == 0)
   {
      _price = type == ORDER_TYPE_BUY ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID);
   }
   mt5Trade.SetExpertMagicNumber(magic);
   switch(type)
   {
   case ORDER_TYPE_BUY_LIMIT:
   case ORDER_TYPE_BUY_STOP:
   case ORDER_TYPE_BUY_STOP_LIMIT:
      stopLoss = _price - stoplossPips * pipValue;
      takeProfit = _price + takeprofitPips * pipValue;
      return mt5Trade.OrderOpen(symbol, type, volume, _price, _price, stopLoss, takeProfit, ORDER_TIME_GTC, 0, comment);
   case ORDER_TYPE_BUY:
      stopLoss = _price - stoplossPips * pipValue;
      takeProfit = _price + takeprofitPips * pipValue;
      return mt5Trade.PositionOpen(symbol, type, volume, _price, stopLoss, takeProfit, comment);
   case ORDER_TYPE_SELL_LIMIT:
   case ORDER_TYPE_SELL_STOP:
   case ORDER_TYPE_SELL_STOP_LIMIT:
      stopLoss = _price + stoplossPips * pipValue;
      takeProfit = _price - takeprofitPips * pipValue;
      return mt5Trade.OrderOpen(symbol, type, volume, _price, _price, stopLoss, takeProfit, ORDER_TIME_GTC, 0, comment);
   case ORDER_TYPE_SELL:
      stopLoss = _price + stoplossPips * pipValue;
      takeProfit = _price - takeprofitPips * pipValue;
      return mt5Trade.PositionOpen(symbol, type, volume, _price, stopLoss, takeProfit, comment);
   default:
      break;
   }
#else
   if(price == 0)
   {
      _price = type == OP_BUY ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID);
   }
   switch(type)
   {
   case OP_BUYLIMIT:
   case OP_BUYSTOP:
   case OP_BUY:
      stopLoss = _price - stoplossPips * pipValue;
      takeProfit = _price + takeprofitPips * pipValue;
      break;
   case OP_SELLLIMIT:
   case OP_SELLSTOP:
   case OP_SELL:
      stopLoss = _price + stoplossPips * pipValue;
      takeProfit = _price - takeprofitPips * pipValue;
      break;
   default:
      break;
   };
   return OrderSend(symbol, type, volume, _price, slippage, stopLoss, takeProfit, comment, (int)magic, 0) > 0;
#endif
   return false;
}

//+------------------------------------------------------------------+
//| Modify an existing pending order                                 |
//+------------------------------------------------------------------+
bool orderModify(const ulong ticket, const double price, const double stopLoss, const double takeProfit)
{
#ifdef __MQL5__
   if(!OrderSelect(ticket)) return false;
   return mt5Trade.OrderModify(
             ticket,
             price,
             stopLoss,
             takeProfit,
             (ENUM_ORDER_TYPE_TIME)OrderGetInteger(ORDER_TYPE_TIME),
             OrderGetInteger(ORDER_TIME_EXPIRATION)
          );
#else
   if(!OrderSelect((int)ticket, SELECT_BY_TICKET)) return false;
   return OrderModify((int)ticket, price, stopLoss, takeProfit, OrderExpiration()) > 0;
#endif
}

//+------------------------------------------------------------------+
//| Close an open position by ticket number                          |
//+------------------------------------------------------------------+
bool positionClose(const ulong ticket)
{
#ifdef __MQL5__
   return mt5Trade.PositionClose(ticket);
#else
   if(!OrderSelect((int)ticket, SELECT_BY_TICKET)) return false;
   return OrderClose(OrderTicket(), OrderLots(), OrderClosePrice(), 10) > 0 ? true : false;
#endif
}

//+------------------------------------------------------------------+
//| Modify an existing open position                                 |
//+------------------------------------------------------------------+
bool positionModify(const string symbol, const ulong ticket, const double stopLoss, const double takeProfit)
{
#ifdef __MQL5__
   return mt5Trade.PositionModify(ticket, stopLoss, takeProfit);
#else
   if(!OrderSelect((int)ticket, SELECT_BY_TICKET)) return false;
   return OrderModify((int)ticket, OrderOpenPrice(), stopLoss, takeProfit, OrderExpiration()) > 0;
#endif
}

//+------------------------------------------------------------------+
//| Ensure the specified symbol is enabled/disabled in Market Watch  |
//+------------------------------------------------------------------+
bool selectSymbol(const string symbol, const bool enable = true)
{
   return SymbolSelect(symbol, enable);
}
//+------------------------------------------------------------------+