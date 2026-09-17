# MQL Trading Strategies Reference

## General

### Checking for Red News
```cpp
//+------------------------------------------------------------------+
//| News detection using MT5 calendar                                |
//+------------------------------------------------------------------+
bool isRedNewsWindow(int bufferMinutes = 120)
{
   MqlCalendarValue values[];
   MqlCalendarEvent event;

   const int n = CalendarValueHistory(values, iTime(_Symbol, PERIOD_D1, 0));
   if(n <= 0) return false; // no calendar access
   for(int i = 0; i < n; i++)
   {
      if(!CalendarEventById(values[i].event_id, event))
      {
         continue;
      }

      if(event.importance == CALENDAR_IMPORTANCE_HIGH)
      {
         datetime t = values[i].time;
         if(MathAbs((int)(TimeCurrent() - t)) <= bufferMinutes * 60) return true;
      }
   }
   return false;
}
```

## 1. Moving Average Crossover
**Concept**: Fast MA crosses above slow MA = buy; crosses below = sell.
**Uses**: iMA(), crossover detection, CTrade (MQL5) or OrderSend (MQL4)
**Key Logic**:
```cpp
double fastMA[3], slowMA[3];
CopyBuffer(fastHandle, 0, 0, 3, fastMA);
CopyBuffer(slowHandle, 0, 0, 3, slowMA);
bool buySignal = (fastMA[1] > slowMA[1] && fastMA[2] <= slowMA[2]);
bool sellSignal = (fastMA[1] < slowMA[1] && fastMA[2] >= slowMA[2]);
```
**Common Inputs**: fast_period (10), slow_period (30), ma_method (SMA/EMA)

## 2. RSI Oversold/Overbought
**Concept**: RSI < oversold (30) = buy; RSI > overbought (70) = sell.
**Uses**: iRSI(), CTrade
**Key Logic**:
```cpp
double rsi[2];
CopyBuffer(rsiHandle, 0, 0, 2, rsi);
bool buySignal = (rsi[1] < oversold && rsi[0] > oversold);   // Cross above oversold
bool sellSignal = (rsi[1] > overbought && rsi[0] < overbought); // Cross below overbought
```
**Common Inputs**: rsi_period (14), oversold (30), overbought (70)

## 3. MACD Signal Line Crossover
**Concept**: MACD line crosses above signal line = buy; crosses below = sell.
**Uses**: iMACD(), main/signal lines
**Key Logic**:
```cpp
double macd[3], signal[3];
CopyBuffer(macdHandle, 0, 0, 3, macd);   // MAIN_LINE
CopyBuffer(macdHandle, 1, 0, 3, signal); // SIGNAL_LINE
bool buySignal = (macd[1] > signal[1] && macd[2] <= signal[2]);
bool sellSignal = (macd[1] < signal[1] && macd[2] >= signal[2]);
```
**Common Inputs**: fast_ema (12), slow_ema (26), signal_sma (9)

## 4. Bollinger Bands Breakout
**Concept**: Price closes above upper band = sell (mean reversion); closes below lower band = buy.
**Uses**: iBands(), UPPER_BAND, LOWER_BAND
**Key Logic**:
```cpp
double upper[2], lower[2], close[2];
CopyBuffer(bbHandle, 1, 0, 2, upper);
CopyBuffer(bbHandle, 2, 0, 2, lower);
CopyClose(_Symbol, PERIOD_CURRENT, 0, 2, close);
bool buySignal = (close[1] <= lower[1] && close[0] > lower[0]);  // Mean reversion
bool sellSignal = (close[1] >= upper[1] && close[0] < upper[0]);
```
**Common Inputs**: bb_period (20), deviation (2.0), shift (0)

## 5. Support/Resistance Breakout
**Concept**: Track swing highs/lows; break above resistance = buy; break below support = sell.
**Uses**: iHighest(), iLowest(), fractals, chart objects
**Key Logic**:
```cpp
int highestIdx = iHighest(_Symbol, PERIOD_CURRENT, MODE_HIGH, lookback, 1);
double resistance = iHigh(_Symbol, PERIOD_CURRENT, highestIdx);

int lowestIdx = iLowest(_Symbol, PERIOD_CURRENT, MODE_LOW, lookback, 1);
double support = iLow(_Symbol, PERIOD_CURRENT, lowestIdx);

bool buySignal = (close[1] <= resistance && close[0] > resistance);
bool sellSignal = (close[1] >= support && close[0] < support);
```
**Common Inputs**: lookback (20), min_distance (50 points)

## 6. ATR-Based Volatility Breakout
**Concept**: Price breaks above/below a channel defined by ATR from opening price.
**Uses**: iATR()
**Key Logic**:
```cpp
double atr[1];
CopyBuffer(atrHandle, 0, 0, 1, atr);
double upperChannel = open[0] + atr[0] * multiplier;
double lowerChannel = open[0] - atr[0] * multiplier;
bool buySignal = (close[0] > upperChannel && close[1] <= upperChannel);
bool sellSignal = (close[0] < lowerChannel && close[1] >= lowerChannel);
```
**Common Inputs**: atr_period (14), multiplier (1.5)

## 7. Stochastic Crossover
**Concept**: %K crosses above %D in oversold = buy; %K crosses below %D in overbought = sell.
**Uses**: iStochastic(), MAIN_LINE, SIGNAL_LINE
**Key Logic**:
```cpp
double k[3], d[3];
CopyBuffer(stochHandle, 0, 0, 3, k);  // MAIN_LINE
CopyBuffer(stochHandle, 1, 0, 3, d);  // SIGNAL_LINE
bool buySignal = (k[1] > d[1] && k[2] <= d[2] && k[1] < 30);
bool sellSignal = (k[1] < d[1] && k[2] >= d[2] && k[1] > 70);
```
**Common Inputs**: k_period (5), d_period (3), slowing (3)

## 8. Multi-Timeframe Confirmation
**Concept**: Higher timeframe trend direction filters lower timeframe entries.
**Uses**: iMA() on higher timeframe, PERIOD_D1 for trend, PERIOD_H1 for entry
**Key Logic**:
```cpp
double htMA[1];
CopyBuffer(htMAHandle, 0, 0, 1, htMA);
bool dailyUptrend = (iClose(_Symbol, PERIOD_D1, 0) > htMA[0]);
bool dailyDowntrend = (iClose(_Symbol, PERIOD_D1, 0) < htMA[0]);

// Filter by HT trend
if (buySignal && !dailyUptrend) return;
if (sellSignal && !dailyDowntrend) return;
```

## 9. Martingale / Grid Trading
**Concept**: Double lot size after each loss, or place grid of orders at fixed intervals.
**Uses**: Position iteration, lot multiplier
**Key Logic**:
```cpp
// Martingale sizing
double lastLot = GetLastClosedLot();
double nextLot = (lastLoss) ? lastLot * martinMultiplier : baseLot;
nextLot = MathMin(nextLot, maxLot);

// Grid spacing
double gridSpace = gridPoints * point;
double nextPrice = lastEntryPrice + gridSpace;
```
**Warning**: High risk — always use with position limits and max loss boundaries.

## 10. Hedging/Dual Strategy
**Concept**: Run buy and sell positions simultaneously (only in hedging accounts).
**Uses**: Separate magic numbers for long/short, PositionSelectByTicket
**Key Logic**:
```cpp
if (buySignal && CountPositions(MAGIC_LONG) < maxLong) 
{
    trade.Buy(lot, _Symbol, ask, sl, tp, "Hedge Buy");
}
if (sellSignal && CountPositions(MAGIC_SHORT) < maxShort) 
{
    trade.Sell(lot, _Symbol, bid, sl, tp, "Hedge Sell");
}
// Separate magic numbers
```

## Risk Management Integration
Every strategy should integrate:
- Position sizing (fixed lot or risk-based)
- Stop loss (ATR-based, fixed points, or swing-based)
- Take profit (RR ratio or ATR multiple)
- Maximum positions limit
- Trailing stop (optional, after N points in profit)
- Break even (optional)
- Daily loss limit
- Time filters (trade only during specific sessions)

## Strategy Inputs Template
```cpp
input group "Strategy"
input ENUM_MA_METHOD inpMaMethod = MODE_SMA;   // MA Method
input int inpFastPeriod = 10;                  // Fast Period
input int inpSlowPeriod = 30;                  // Slow Period
input bool inpUseRsiFilter = true;             // Use RSI Filter
input int inpRsiPeriod = 14;                   // RSI Period
input int inpRsiMax = 70;                      // RSI Overbought
input int inpRsiMin = 30;                      // RSI Oversold
input bool inpCloseOnOpposite = true;          // Close on Opposite Signal
input bool inpUseTimeFilter = false;           // Use Time Filter
input string inpStartTime = "08:00";           // Start Time
input string inpEndTime = "20:00";             // End Time
```
