# Platform Differences

## General

### Time Series Arrays
- MQL4: Low[x], High[x], Open[x], Close[x], Volume[x] where x is the index of the bar (0 for current, 1 for previous, etc.)
- MQL5: iLow(symbol, timeframe, x), iHigh(symbol, timeframe, x), iOpen(symbol, timeframe, x), iClose(symbol, timeframe, x), iVolume(symbol, timeframe, x) where symbol and timeframe are specified.

## Functions

### StringToUpper
- MQL5: `bool StringToUpper(string &str)`
- MQL4: `string StringToUpper(string str)`


