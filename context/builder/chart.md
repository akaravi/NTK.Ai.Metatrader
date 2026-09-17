# MQL Chart Operations

## Chart Management
```cpp
// Open a new chart
long chartId = ChartOpen("EURUSD", PERIOD_H1);

// Close a chart
ChartClose(0);  // 0 = current chart

// Get current chart ID
long chartId = ChartID();

// Get chart symbol
string symbol = ChartSymbol(0);

// Get chart period
ENUM_TIMEFRAMES period = ChartPeriod(0);

// Change chart symbol
ChartSetSymbolPeriod(0, "GBPUSD", PERIOD_M15);

BringToTop();
```

## Chart Properties
```cpp
// Chart dimensions
int width = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
int height = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS);
int visibleBars = (int)ChartGetInteger(0, CHART_VISIBLE_BARS);
int firstVisibleBar = (int)ChartGetInteger(0, CHART_FIRST_VISIBLE_BAR);

// Chart display
ChartGetInteger(0, CHART_SCALE);           // Scale factor
ChartGetInteger(0, CHART_SCALEFIX);        // Fixed scale (true/false)
ChartGetDouble(0, CHART_FIXED_MAX);        // Fixed max price
ChartGetDouble(0, CHART_FIXED_MIN);        // Fixed min price
ChartGetInteger(0, CHART_MODE);            // CHART_BARS, CHART_CANDLES, CHART_LINE
ChartGetInteger(0, CHART_SHOW_GRID);       // Grid visibility
ChartGetInteger(0, CHART_SHOW_VOLUMES);    // Volume display
ChartGetInteger(0, CHART_SHOW_ASK_LINE);   // Ask line visibility
ChartGetInteger(0, CHART_SHOW_BID_LINE);   // Bid line visibility

// Set chart properties
ChartSetInteger(0, CHART_MODE, CHART_CANDLES);
ChartSetInteger(0, CHART_SCALE, 3);  // 0-5
ChartSetInteger(0, CHART_SHOW_GRID, true);
ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_TICK);
ChartSetInteger(0, CHART_AUTOSCROLL, true);
ChartSetInteger(0, CHART_SHIFT, true);  // Shift chart from right edge

// Chart colors
ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrBlack);
ChartSetInteger(0, CHART_COLOR_FOREGROUND, clrWhite);
ChartSetInteger(0, CHART_COLOR_GRID, clrDimGray);
ChartSetInteger(0, CHART_COLOR_CHART_UP, clrLime);
ChartSetInteger(0, CHART_COLOR_CHART_DOWN, clrRed);
ChartSetInteger(0, CHART_COLOR_CANDLE_BULL, clrGreen);
ChartSetInteger(0, CHART_COLOR_CANDLE_BEAR, clrRed);
ChartSetInteger(0, CHART_COLOR_BID, clrDodgerBlue);
ChartSetInteger(0, CHART_COLOR_ASK, clrOrangeRed);
ChartSetInteger(0, CHART_COLOR_LAST, clrGold);
```

## Chart Events (EA/Indicator)
```cpp
//+------------------------------------------------------------------+
//| Chart event handler                                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
    switch(id) 
    {
        case CHARTEVENT_KEYDOWN:
            Print("Key pressed: ", lparam);
            break;
        case CHARTEVENT_OBJECT_CLICK:
            Print("Object clicked: ", sparam);
            break;
        case CHARTEVENT_OBJECT_DRAG:
            Print("Object dragged: ", sparam);
            break;
        case CHARTEVENT_OBJECT_DELETE:
            Print("Object deleted: ", sparam);
            break;
        case CHARTEVENT_CLICK:
            Print("Chart clicked at x=", (int)lparam, " y=", (int)dparam);
            break;
        case CHARTEVENT_MOUSE_MOVE:
            // lparam = x, dparam = y
            break;
        case CHARTEVENT_CHART_CHANGE:
            Print("Chart timeframe or symbol changed");
            break;
        case CHARTEVENT_CUSTOM + 1:
            // Custom event
            break;
        default:
            break;
    }
}
```

## Chart Navigation
```cpp
// Navigate to a specific time
ChartNavigate(0, CHART_CURRENT_POS, 0);   // Jump to current
ChartNavigate(0, CHART_BEGIN, 0);         // Jump to start
ChartNavigate(0, CHART_END, 0);           // Jump to end  

// Scroll chart
ChartNavigate(0, CHART_CURRENT_POS, shift);

// Set visible range
datetime startTime = StringToTime("2025.01.01 00:00");
datetime endTime = StringToTime("2025.06.01 00:00");
ChartSetInteger(0, CHART_SHOW_PRICE_SCALE, true);
```

## Template Operations
```cpp
// Save chart template
ChartSaveTemplate(0, "my_template");

// Apply chart template
ChartApplyTemplate(0, "my_template");

// Screenshot
ChartScreenShot(0, "chart_screenshot.png", 1920, 1080, ALIGN_RIGHT);
```

## Subwindows
```cpp
// Get number of subwindows
int subWindows = (int)ChartGetInteger(0, CHART_WINDOWS_TOTAL);

// Get visible subwindow
int visibleWindow = (int)ChartGetInteger(0, CHART_WINDOW_IS_VISIBLE, 1);

// Subwindow indicator
#property indicator_separate_window
#property indicator_minimum -100
#property indicator_maximum 100

// Chart height per subwindow
ChartSetInteger(0, CHART_HEIGHT_IN_PIXELS, subwindow_index, height);
```

## Timeframe Constants
```cpp
PERIOD_M1       // 1 minute
PERIOD_M2       // 2 minutes
PERIOD_M3       // 3 minutes
PERIOD_M4       // 4 minutes
PERIOD_M5       // 5 minutes
PERIOD_M6       // 6 minutes
PERIOD_M10      // 10 minutes
PERIOD_M12      // 12 minutes
PERIOD_M15      // 15 minutes
PERIOD_M20      // 20 minutes
PERIOD_M30      // 30 minutes
PERIOD_H1       // 1 hour
PERIOD_H2       // 2 hours
PERIOD_H3       // 3 hours
PERIOD_H4       // 4 hours
PERIOD_H6       // 6 hours
PERIOD_H8       // 8 hours
PERIOD_H12      // 12 hours
PERIOD_D1       // Daily
PERIOD_W1       // Weekly
PERIOD_MN1      // Monthly

// Period conversion
string periodStr = EnumToString(PERIOD_H1);  // "PERIOD_H1"
int periodMinutes = PeriodSeconds(PERIOD_H1) / 60;  // 60
```
