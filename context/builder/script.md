# MQL Script Development

Scripts are one-shot programs that execute once and terminate. Unlike EAs, they have only `OnStart()`.

## Script File Structure (MQL5)
```cpp
//+------------------------------------------------------------------+
//|                                                      example.mq5 |
//|                                           Copyright 2026,Example |
//|                                         https://www.example.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,Example"
#property link      "https://www.example.com/"
#property version   "1.00"
#property strict
#property script_show_inputs  // Show input dialog before execution

// --- Includes ---
#include <Trade/Trade.mqh>

// --- Inputs ---
input double inpLotSize = 0.1;    // Lot Size
input int inpTakeProfit = 500;    // Take Profit (points)
input int inpStopLoss = 300;      // Stop Loss (points)

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
    // Validate inputs
    if (inpLotSize <= 0) 
    {
        Print("Invalid lot size");
        return;
    }
    
    // Single execution logic
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    
    double sl = NormalizeDouble(bid - inpStopLoss * point, digits);
    double tp = NormalizeDouble(ask + inpTakeProfit * point, digits);
    
    CTrade trade;
    trade.SetExpertMagicNumber(0);
    
    if (trade.Buy(inpLotSize, _Symbol, ask, sl, tp, "Script Buy")) 
    {
        Print("Buy order placed. Ticket: ", trade.ResultOrder());
    } 
    else 
    {
        Print("Buy failed. Error: ", GetLastError());
    }
}
```

## MQL4 Script Structure
```cpp
//+------------------------------------------------------------------+
//|                                                      example.mq5 |
//|                                           Copyright 2026,Example |
//|                                         https://www.example.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,Example"
#property link      "https://www.example.com/"
#property version   "1.00"
#property strict
#property show_inputs

input double inpLotSize = 0.1;

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
    // OrderSend only
    int ticket = OrderSend(_Symbol, OP_BUY, inpLotSize, Ask, 30, 0, 0, "Script Buy", 0, 0, clrGreen);
    if (ticket == -1) 
    {
         Print("Order failed. Error: ", GetLastError());
    }
}
```

## Common Script Use Cases
1. **Place a single trade** - Open one position with specified parameters
2. **Close all positions** - Close all open positions on a symbol or account
3. **Delete pending orders** - Remove all pending orders
4. **Modify positions** - Adjust SL/TP on all open trades
5. **Export data** - Write price data, indicator values, or account info to CSV
6. **Draw objects** - Place chart objects (lines, labels, rectangles)
7. **Account operations** - Display account summary, calculate exposure

## Close All Positions Script (MQL5)
```cpp
#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
    CTrade trade;
    CPositionInfo pos;
    
    for (int i = PositionsTotal() - 1; i >= 0; i--) 
        if (pos.SelectByIndex(i)) 
            if (!trade.PositionClose(pos.Ticket())) 
                Print("Failed to close position ", pos.Ticket());
            
    Print("All positions closed");
}
```

## Export Bars to CSV Script (MQL5)
```cpp
//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
    string filename = "data_" + _Symbol + ".csv";
    int handle = FileOpen(filename, FILE_WRITE | FILE_CSV | FILE_ANSI, ",");
    
    if (handle == INVALID_HANDLE) 
    {
        Print("Cannot create file");
        return;
    }
    
    FileWrite(handle, "Time", "Open", "High", "Low", "Close", "Volume");
    
    datetime time[];
    double open[], high[], low[], close[];
    long volume[];
    
    ArraySetAsSeries(time, true);
    ArraySetAsSeries(open, true);
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);
    ArraySetAsSeries(volume, true);
    
    CopyTime(_Symbol, PERIOD_CURRENT, 0, 1000, time);
    CopyOpen(_Symbol, PERIOD_CURRENT, 0, 1000, open);
    CopyHigh(_Symbol, PERIOD_CURRENT, 0, 1000, high);
    CopyLow(_Symbol, PERIOD_CURRENT, 0, 1000, low);
    CopyClose(_Symbol, PERIOD_CURRENT, 0, 1000, close);
    CopyTickVolume(_Symbol, PERIOD_CURRENT, 0, 1000, volume);
    
    for (int i = 999; i >= 0; i--) 
        FileWrite(handle, TimeToString(time[i]), open[i], high[i], low[i], close[i], volume[i]);
    
    FileClose(handle);
    Print("Data exported to ", filename);
}
```

## Important Notes
- Scripts run once and complete - no continuous execution
- Use `#property script_show_inputs` to show parameter dialog
- `OnStart()` is the only event handler
- Scripts can access all terminal functions except chart/timer events
- For heavy operations, show progress with `Comment()` or update a label object
- Use `IsStopped()` in loops to allow user cancellation
