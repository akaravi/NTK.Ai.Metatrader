# MQL Risk Management

## Position Sizing

### Dollar Risk-Based Lot Size
```cpp
//+------------------------------------------------------------------+
//| Calculate lot size from dollar risk amount                       |
//+------------------------------------------------------------------+
double CalculateLotSize(double riskAmount, double price, double stopLoss)
{
   const double pipValue    = getPipValue(_Symbol);
   const double maxLotSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(StringFind(_Symbol, ".mini") != -1 || AccountInfoString(ACCOUNT_COMPANY) == "FTMO S.R.O.")
      tickValue *= 100;

   const double stopLossPips = MathAbs(price - stopLoss) / pipValue;
   if(stopLossPips == 0) return 0;

   const double maxLossInQuoteCurr = riskAmount / tickValue;
   const double quoteDivision      = stopLossPips * pipValue == 0 ? 0 : maxLossInQuoteCurr / (stopLossPips * pipValue);
   const double startingRisk       = maxLotSize == 0 ? 0 : quoteDivision / maxLotSize;
   const double riskCurrent        = startingRisk * tickValue;

   double lots;
   if(StringFind(_Symbol, "US30") != -1 || StringFind(_Symbol, "NAS100") != -1 ||
      StringFind(_Symbol, "SPX500") != -1 || StringFind(_Symbol, "JPY225") != -1 ||
      StringFind(_Symbol, "UK100") != -1 || StringFind(_Symbol, "FRA40") != -1 ||
      StringFind(_Symbol, "BTCUSD") != -1 || StringFind(_Symbol, "ETHUSD") != -1 ||
      StringFind(_Symbol, "LTCUSD") != -1 || StringFind(_Symbol, "BNBUSD") != -1)
      lots = NormalizeDouble(riskCurrent * tickValue, 2);
   else if(StringFind(_Symbol, "USDJPY") != -1 || StringFind(_Symbol, "CADJPY") != -1 ||
           StringFind(_Symbol, "EURJPY") != -1 || StringFind(_Symbol, "AUDJPY") != -1 ||
           StringFind(_Symbol, "NZDJPY") != -1 || StringFind(_Symbol, "CHFJPY") != -1 ||
           StringFind(_Symbol, "GBPJPY") != -1)
      lots = NormalizeDouble((riskCurrent * 100) / tickValue, 2);
   else
      lots = NormalizeDouble(riskCurrent, 2);

   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   if(lotStep > 0)
      lots = MathFloor(lots / lotStep) * lotStep;
   lots = MathMax(minLot, MathMin(maxLot, lots));

   return NormalizeDouble(lots, 2);
}
```

### Pip Value Helper
```cpp
//+------------------------------------------------------------------+
//| Get pip value for a symbol                                       |
//+------------------------------------------------------------------+
double getPipValue(const string symbol)
{
   const double _pips = SymbolInfoDouble(symbol, SYMBOL_POINT) * 10;
   const double digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   if(symbol == "" || digits == 0)
      return _pips;

   if(digits >= 4) return 0.0001;
   if(digits == 3) return 0.01;

   if(StringFind(symbol, "XAU") != -1)
      return 0.10;

   if(StringFind(symbol, "US30") != -1 || StringFind(symbol, "NAS100") != -1 ||
      StringFind(symbol, "SPX500") != -1 || StringFind(symbol, "UK100") != -1 ||
      StringFind(symbol, "JPY225") != -1 || StringFind(symbol, "FRA40") != -1)
      return 1.0;

   if(StringFind(symbol, "ETHUSD") != -1 || StringFind(symbol, "BTCUSD") != -1)
      return 1.0;

   return _pips;
}
```

### Risk-Based Lot (Fixed Percent per Trade)
```cpp
//+------------------------------------------------------------------+
//| Calc lot size from entry, SL, and risk percent                   |
//+------------------------------------------------------------------+
double calculateRiskLot(double entryPrice, double stopLossPrice, double riskPercent = 1.0)
{
   const double accountRisk = AccountInfoDouble(ACCOUNT_EQUITY) * (riskPercent / 100.0);
   const double pipValue    = getPipValue(_Symbol);
   const double maxLotSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(StringFind(_Symbol, ".mini") != -1 || AccountInfoString(ACCOUNT_COMPANY) == "FTMO S.R.O.")
      tickValue *= 100;

   const double stopLossPips = MathAbs(entryPrice - stopLossPrice) / pipValue;
   if(stopLossPips == 0) return 0;

   const double maxLossInQuoteCurr = accountRisk / tickValue;
   const double quoteDivision      = stopLossPips * pipValue == 0 ? 0 : maxLossInQuoteCurr / (stopLossPips * pipValue);
   const double startingRisk       = maxLotSize == 0 ? 0 : quoteDivision / maxLotSize;
   const double riskCurrent        = startingRisk * tickValue;

   double calculatedLot;
   if(StringFind(_Symbol, "US30") != -1 || StringFind(_Symbol, "NAS100") != -1 ||
      StringFind(_Symbol, "SPX500") != -1 || StringFind(_Symbol, "JPY225") != -1 ||
      StringFind(_Symbol, "UK100") != -1 || StringFind(_Symbol, "FRA40") != -1 ||
      StringFind(_Symbol, "BTCUSD") != -1 || StringFind(_Symbol, "ETHUSD") != -1 ||
      StringFind(_Symbol, "LTCUSD") != -1 || StringFind(_Symbol, "BNBUSD") != -1)
      calculatedLot = NormalizeDouble(riskCurrent * tickValue, 2);
   else if(StringFind(_Symbol, "USDJPY") != -1 || StringFind(_Symbol, "CADJPY") != -1 ||
           StringFind(_Symbol, "EURJPY") != -1 || StringFind(_Symbol, "AUDJPY") != -1 ||
           StringFind(_Symbol, "NZDJPY") != -1 || StringFind(_Symbol, "CHFJPY") != -1 ||
           StringFind(_Symbol, "GBPJPY") != -1)
      calculatedLot = NormalizeDouble((riskCurrent * 100) / tickValue, 2);
   else
      calculatedLot = NormalizeDouble(riskCurrent, 2);

   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   if(lotStep > 0)
      calculatedLot = MathFloor(calculatedLot / lotStep) * lotStep;
   calculatedLot = MathMax(minLot, MathMin(maxLot, calculatedLot));

   return NormalizeDouble(calculatedLot, 2);
}
```

## Trailing Stop (MQL5)
```cpp
void applyTrailingStop(double trailPoints) 
{
    double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double trailPrice = trailPoints * point;
    
    for (int i = PositionsTotal() - 1; i >= 0; i--) 
        if (position.SelectByIndex(i)) 
        {
            if (position.Symbol() != _Symbol || position.Magic() != magicNumber) continue;
            
            double currentSL = position.StopLoss();
            double openPrice = position.PriceOpen();
            double currentPrice = position.PriceCurrent();
            double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
            double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
            int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
            
            if (position.PositionType() == POSITION_TYPE_BUY) 
            {
                double newSL = NormalizeDouble(bid - trailPrice, digits);
                if (currentSL < NormalizeDouble(newSL - tickSize, digits)) 
                    if (trade.PositionModify(position.Ticket(), newSL, position.TakeProfit())) 
                        PrintFormat("Trailing SL updated for buy #%d to %.5f", position.Ticket(), newSL);
            } 
            else if (position.PositionType() == POSITION_TYPE_SELL) 
            {
                double newSL = NormalizeDouble(ask + trailPrice, digits);
                if (currentSL > NormalizeDouble(newSL + tickSize, digits) || currentSL == 0) 
                    if (trade.PositionModify(position.Ticket(), newSL, position.TakeProfit())) 
                        PrintFormat("Trailing SL updated for sell #%d to %.5f", position.Ticket(), newSL);
            }
        }
    
}
```

## Break Even
```cpp
void applyBreakEven(double breakEvenPoints, double lockProfitPoints = 0) 
{
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    
    for (int i = PositionsTotal() - 1; i >= 0; i--) 
        if (position.SelectByIndex(i)) {
            if (position.Symbol() != _Symbol || position.Magic() != magicNumber) continue;
            
            double openPrice = position.PriceOpen();
            double currentSL = position.StopLoss();
            double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
            double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
            
            if (position.PositionType() == POSITION_TYPE_BUY) 
            {
                double profitPoints = (bid - openPrice) / point;
                if (profitPoints >= breakEvenPoints) {
                    double newSL = NormalizeDouble(openPrice + lockProfitPoints * point, digits);
                    if (currentSL < newSL - tickSize || currentSL == 0) 
                        trade.PositionModify(position.Ticket(), newSL, position.TakeProfit());
                }
            } 
            else if (position.PositionType() == POSITION_TYPE_SELL) 
            {
                double profitPoints = (openPrice - ask) / point;
                if (profitPoints >= breakEvenPoints) {
                    double newSL = NormalizeDouble(openPrice - lockProfitPoints * point, digits);
                    if (currentSL > newSL + tickSize || currentSL == 0) 
                        trade.PositionModify(position.Ticket(), newSL, position.TakeProfit());
                }
            }
        }
}
```

## Daily Loss Limit
```cpp
bool IsDailyLossExceeded(double maxLossPercent) 
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double lossPercent = ((balance - equity) / balance) * 100.0;
    return lossPercent >= maxLossPercent;
}
```

## Maximum Positions / Exposure
```cpp
int countOpenPositions() 
{
    int count = 0;
    for (int i = PositionsTotal() - 1; i >= 0; i--) 
        if (position.SelectByIndex(i)) 
            if (position.Symbol() == _Symbol && position.Magic() == magicNumber)
                count++;
    return count;
}

bool isMaxPositionsReached(int maxPositions) 
{
    return countOpenPositions() >= maxPositions;
}
```

## MQL4 Trailing Stop
```cpp
void applyTrailingStopMQL4(double trailPoints) 
{
    double point = MarketInfo(_Symbol, MODE_POINT);
    double trailPrice = trailPoints * point;
    int digits = (int)MarketInfo(_Symbol, MODE_DIGITS);
    
    for (int i = OrdersTotal() - 1; i >= 0; i--) {
        if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) {
            if (OrderSymbol() != _Symbol || OrderMagicNumber() != magicNumber) continue;
            
            double newSL = 0;
            if (OrderType() == OP_BUY) {
                newSL = NormalizeDouble(Bid - trailPrice, digits);
                if (newSL > OrderStopLoss() + point || OrderStopLoss() == 0) {
                    if (Bid - OrderOpenPrice() > trailPrice)
                        OrderModify(OrderTicket(), OrderOpenPrice(), newSL, OrderTakeProfit(), 0);
                }
            } else if (OrderType() == OP_SELL) {
                newSL = NormalizeDouble(Ask + trailPrice, digits);
                if (newSL < OrderStopLoss() - point || OrderStopLoss() == 0) {
                    if (OrderOpenPrice() - Ask > trailPrice)
                        OrderModify(OrderTicket(), OrderOpenPrice(), newSL, OrderTakeProfit(), 0);
                }
            }
        }
    }
}
```

## Risk Management Input Example
```cpp
input group "Risk Management"
input double inpRiskPercent = 1.0;         // Risk Percent per Trade
input double inpLotSize = 0.1;             // Fixed Lot Size (if risk_percent = 0)
input int inpMaxPositions = 1;             // Maximum Open Positions
input double inpDailyLossLimit = 5.0;     // Daily Loss Limit (%)
input bool inpUseTrailingStop = true;     // Enable Trailing Stop
input double inpTrailingStopPoints = 200; // Trailing Stop (points)
input double inpTrailingStepPoints = 50;  // Trailing Step (points)
input bool inpUseBreakEven = true;        // Enable Break Even
input double inpBreakevenPoints = 300;     // Break Even Trigger (points)
input double inpLockProfitPoints = 50;    // Lock Profit After BE (points)
```
