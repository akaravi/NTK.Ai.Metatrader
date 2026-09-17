# Python Context

## Prices
- call `get_recent_bars(symbol, timeframe, count)` when asked for a price or price history, where `symbol` is the trading symbol (e.g. "EURUSD"), `timeframe` is the timeframe constant (e.g. mt5.MetaTrader5.TIMEFRAME_M1), and `count` is the number of recent bars to retrieve (e.g. 1). Only request the number of bars that you actually need, which unless specified otherwise, is typically 1 for the most recent price.

## Timeframe
- the 1-Minute timeframe: 1
- the 5-Minute timeframe: 5
- the 15-Minute timeframe: 15
- the 30-Minute timeframe: 30
- the 1-Hour timeframe: 16385
- the 4-Hour timeframe: 16388
- the daily timeframe: 16408
- the weekly timeframe: 32769
- the monthly timeframe: 49153