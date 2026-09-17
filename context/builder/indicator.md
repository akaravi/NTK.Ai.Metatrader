# MQL Custom Indicator Development

## Indicator File Structure
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
#property indicator_chart_window    // or indicator_separate_window
#property indicator_buffers 2
#property indicator_plots   1
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrBlue
#property indicator_width1  2
#property indicator_label1  "My Indicator"

// --- Inputs ---
input int ma_period = 14;  // MA Period

// --- Indicator Buffers ---
double mainBuffer[];
double signalBuffer[];

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
    // Set as series
    ArraySetAsSeries(mainBuffer, true);
    ArraySetAsSeries(signalBuffer, true);
    
    // Bind buffers to indicator
    SetIndexBuffer(0, mainBuffer, INDICATOR_DATA);
    SetIndexBuffer(1, signalBuffer, INDICATOR_DATA);
    
    // Set empty values
    PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, 0.0);
    PlotIndexSetDouble(1, PLOT_EMPTY_VALUE, 0.0);
    
    // Set indicator name for DataWindow
    IndicatorSetString(INDICATOR_SHORTNAME, "MyIndicator(" + IntegerToString(ma_period) + ")");
    
    // Set number of digits
    IndicatorSetInteger(INDICATOR_DIGITS, _Digits);
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
    // Set arrays as series
    ArraySetAsSeries(close, true);
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    
    // Determine start position
    int start = prev_calculated;
    if (start == 0) start = 1;  // First run
    
    // Main calculation loop
    for (int i = start; i < rates_total; i++) {
        mainBuffer[i] = (high[i] + low[i] + close[i]) / 3.0;
    }
    
    return(rates_total);
}

//+------------------------------------------------------------------+
//| Deinitialization                                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Cleanup if needed
}
```

## MQL4 Indicator Structure (Differences)
```cpp
#property indicator_buffers 2
#property indicator_color1 Blue

// In OnInit (MQL4 uses SetIndexBuffer differently):
SetIndexBuffer(0, mainBuffer);
SetIndexBuffer(1, signalBuffer);
SetIndexStyle(0, DRAW_LINE, STYLE_SOLID, 2);
SetIndexLabel(0, "Main");

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
    // Same as MQL5
}
```

## Indicator Plot Types
```cpp
DRAW_LINE        // Continuous line
DRAW_SECTION     // Line segments between non-empty values
DRAW_HISTOGRAM   // Histogram from zero line
DRAW_ARROW       // Symbols/arrows
DRAW_ZIGZAG      // Zigzag style (no vertical connections)
DRAW_NONE        // Hidden (for intermediate calculations)
DRAW_FILLING     // Filled area between two buffers
DRAW_BARS        // Bar chart
DRAW_CANDLES     // Candlestick chart
DRAW_COLOR_LINE          // Multi-color line
DRAW_COLOR_HISTOGRAM     // Multi-color histogram
DRAW_COLOR_ARROW         // Multi-color arrows
DRAW_COLOR_ZIGZAG        // Multi-color zigzag
```

## Multiple Plots
```cpp
#property indicator_plots 2

// Plot 1
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrBlue
#property indicator_width1  2
#property indicator_label1  "Fast MA"

// Plot 2
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrRed
#property indicator_width2  1
#property indicator_label2  "Slow MA"

// Buffers
double fastMABuffer[];
double slowMABuffer[];

// Bind in OnInit:
SetIndexBuffer(0, fastMABuffer, INDICATOR_DATA);
SetIndexBuffer(1, slowMABuffer, INDICATOR_DATA);
```

## Separate Window Indicator
```cpp
#property indicator_separate_window
#property indicator_minimum -100
#property indicator_maximum 100
#property indicator_level1 70
#property indicator_level2 30
#property indicator_level3 -30
#property indicator_level4 -70
#property indicator_levelcolor clrGray
#property indicator_levelstyle STYLE_DOT
```

## Technical Indicator Handles (MQL5)
```cpp
// Create indicator handle
int maHandle = iMA(_Symbol, PERIOD_CURRENT, 14, 0, MODE_SMA, PRICE_CLOSE);
int rsiHandle = iRSI(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE);
int macdHandle = iMACD(_Symbol, PERIOD_CURRENT, 12, 26, 9, PRICE_CLOSE);
int bbandsHandle = iBands(_Symbol, PERIOD_CURRENT, 20, 0, 2.0, PRICE_CLOSE);
int atrHandle = iATR(_Symbol, PERIOD_CURRENT, 14);
int stochHandle = iStochastic(_Symbol, PERIOD_CURRENT, 5, 3, 3, MODE_SMA, STO_LOWHIGH);

// Validate handle
if (maHandle == INVALID_HANDLE) 
{
    Print("Failed to create MA handle. Error: ", GetLastError());
    return(INIT_FAILED);
}

// Copy data from handle
double maValues[];
ArraySetAsSeries(maValues, true);
if (CopyBuffer(maHandle, 0, 0, 3, maValues) < 3) 
{
    Print("Failed to copy MA data");
}

//+------------------------------------------------------------------+
//| Deinitialization                                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Release handle in OnDeinit
    if (maHandle != INVALID_HANDLE) IndicatorRelease(maHandle);
}
```

## Built-in i-Functions (MQL4)
```cpp
// MQL4 direct i-functions
double ma = iMA(_Symbol, PERIOD_CURRENT, 14, 0, MODE_SMA, PRICE_CLOSE, 0);
double rsi = iRSI(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE, 0);
double macd = iMACD(_Symbol, PERIOD_CURRENT, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
double upperBB = iBands(_Symbol, PERIOD_CURRENT, 20, 2, 0, PRICE_CLOSE, MODE_UPPER, 0);
double atr = iATR(_Symbol, PERIOD_CURRENT, 14, 0);
double stoch = iStochastic(_Symbol, PERIOD_CURRENT, 5, 3, 3, MODE_SMA, 0, MODE_MAIN, 0);
```

## Time-Series Array Convention
// MQL4: not time-series by default
// MQL5: time-series by default
// Call ArraySetAsSeries() for explicit direction.
