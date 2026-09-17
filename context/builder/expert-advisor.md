# MQL Expert Advisor Development

## EA File Structure (MQL5)
```cpp
//+------------------------------------------------------------------+
//|                                                      example.mq5 |
//|                                           Copyright 2026,Example |
//|                                         https://www.example.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,Example"
#property link      "https://www.example.com/"
#property description "Example Expert Advisor using MQL5"
#property strict

// --- Includes ---
#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/OrderInfo.mqh>

// --- Inputs ---
input group "Trading Settings"
input double lot_size = 0.1;       // Fixed Lot Size
input int magic_number = 123456;   // Magic Number
input int slippage = 30;           // Slippage (points)

input group "Strategy Parameters"
input int fast_ma = 10;            // Fast MA Period
input int slow_ma = 30;            // Slow MA Period

// --- Globals ---
CTrade trade;
CPositionInfo position;
int fastMAHandle, slowMAHandle;
bool isNewBar = false;
datetime lastBarTime = 0;

// ── Helper Functions ──
bool IsNewBar() 
{
    datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
    if (currentBarTime != lastBarTime) {
        lastBarTime = currentBarTime;
        return true;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Validate params
    if (fast_ma >= slow_ma) 
    {
        Print("Fast MA must be less than Slow MA");
        return(INIT_PARAMETERS_INCORRECT);
    }
    
    // Set trade properties
    trade.SetExpertMagicNumber(magic_number);
    trade.SetDeviationInPoints(slippage);
    trade.SetTypeFilling(ORDER_FILLING_FOK);
    
    // Create indicator handles
    fastMAHandle = iMA(_Symbol, PERIOD_CURRENT, fast_ma, 0, MODE_SMA, PRICE_CLOSE);
    slowMAHandle = iMA(_Symbol, PERIOD_CURRENT, slow_ma, 0, MODE_SMA, PRICE_CLOSE);
    
    if (fastMAHandle == INVALID_HANDLE || slowMAHandle == INVALID_HANDLE) 
    {
        Print("Failed to create indicator handles");
        return(INIT_FAILED);
    }
    
    Print("EA initialized on ", _Symbol);
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() 
{
    // Check if trading is allowed
    if (!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return;
    if (!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return;
    if (!MQLInfoInteger(MQL_TRADE_ALLOWED)) return;
    
    // Wait for new bar (optional)
    if (!IsNewBar()) return;
    
    // Get indicator values
    double fastMA[], slowMA[];
    ArraySetAsSeries(fastMA, true);
    ArraySetAsSeries(slowMA, true);
    
    if (CopyBuffer(fastMAHandle, 0, 0, 3, fastMA) < 3) return;
    if (CopyBuffer(slowMAHandle, 0, 0, 3, slowMA) < 3) return;
    
    // Check for crossover
    bool bullishCross = (fastMA[1] > slowMA[1] && fastMA[2] <= slowMA[2]);
    bool bearishCross = (fastMA[1] < slowMA[1] && fastMA[2] >= slowMA[2]);
    
    // Close opposite positions
    if (bullishCross) CloseSellPositions();
    if (bearishCross) CloseBuyPositions();
    
    // Open new positions
    if (bullishCross && !HasBuyPosition()) 
    {
        double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        double sl = 0;  // Calculate from ATR or fixed points
        double tp = 0;
        trade.Buy(lot_size, _Symbol, ask, sl, tp, "MA Cross Buy");
    }
    
    if (bearishCross && !HasSellPosition()) 
    {
        double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        double sl = 0;
        double tp = 0;
        trade.Sell(lot_size, _Symbol, bid, sl, tp, "MA Cross Sell");
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Release indicator handles
    if (fastMAHandle != INVALID_HANDLE) IndicatorRelease(fastMAHandle);
    if (slowMAHandle != INVALID_HANDLE) IndicatorRelease(slowMAHandle);
    Print("EA removed. Reason: ", reason);
}
```

## EA File Structure (MQL4)
```cpp
//+------------------------------------------------------------------+
//|                                                      example.mq4 |
//|                                           Copyright 2026,Example |
//|                                         https://www.example.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026,Example"
#property link      "https://www.example.com/"
#property description "Example Expert Advisor using MQL4"
#property strict

// Inputs
input double lot_size = 0.1;
input int magic_number = 123456;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() 
{
    // Check for new bar
    static datetime lastBarTime = 0;
    if (Time[0] == lastBarTime) return;
    lastBarTime = Time[0];
    
    // Get indicator values
    double fastMA = iMA(_Symbol, PERIOD_CURRENT, 10, 0, MODE_SMA, PRICE_CLOSE, 0);
    double slowMA = iMA(_Symbol, PERIOD_CURRENT, 30, 0, MODE_SMA, PRICE_CLOSE, 0);
    
    // Trading logic with OrderSend/OrderClose
}


//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{

}
```

## Key EA Event Handlers

### OnInit Return Codes
```cpp
INIT_SUCCEEDED          // 0 - Success
INIT_FAILED             // 1 - Generic failure
INIT_PARAMETERS_INCORRECT // 2 - Bad parameters
INIT_AGENT_NOT_SUITABLE // 3 - Not suitable for agent
```

### OnTick Tips
- Called on every price tick (bid/ask change)
- Use `IsNewBar()` pattern to run logic once per bar
- Always check trading permissions before trading
- Keep execution fast - heavy calculations on every tick can cause lag

### OnDeinit Reason Codes
```cpp
REASON_PROGRAM        // 0 - EA removed manually
REASON_REMOVE         // 1 - EA removed by user
REASON_RECOMPILE     // 2 - EA recompiled
REASON_CHARTCHANGE   // 3 - Symbol or timeframe changed
REASON_CHARTCLOSE    // 4 - Chart closed
REASON_PARAMETERS    // 5 - Parameters changed
REASON_ACCOUNT       // 6 - Account changed
REASON_TEMPLATE      // 7 - New template applied
REASON_INITFAILED    // 8 - OnInit returned error
REASON_CLOSE         // 9 - Terminal closed
```

## Timer Events (Optional)
```cpp
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    EventSetTimer(60);  // Call OnTimer every 60 seconds
    return(INIT_SUCCEEDED);
}


//+------------------------------------------------------------------+
//| Expert timer function                                            |
//+------------------------------------------------------------------+
void OnTimer()
{
    // Periodic tasks
    // Status logging, heartbeat
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    EventKillTimer();
}
```

## Chart Events (Optional)
```cpp
//+------------------------------------------------------------------+
//| Expert on-event function                                         |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
    if (id == CHARTEVENT_OBJECT_CLICK) {
        if (sparam == "btnBuy") {
            // Buy button clicked
        }
    }
    if (id == CHARTEVENT_KEYDOWN) {
        if (lparam == 'B') {
            // B key pressed
        }
    }
}
```
