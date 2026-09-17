# MQL Trading Operations

## MQL5 Trade Classes (Preferred)
```cpp
#include <Trade/Trade.mqh>

CTrade trade;

// Set trade properties
trade.SetExpertMagicNumber(magicNumber);
trade.SetDeviationInPoints(slippage);
trade.SetTypeFilling(ORDER_FILLING_FOK);

// Open buy position
trade.Buy(lotSize, _Symbol, 0, stopLoss, takeProfit, "Buy EA");

// Open sell position
trade.Sell(lotSize, _Symbol, 0, stopLoss, takeProfit, "Sell EA");

// Close a position by ticket
trade.PositionClose(ticket);

trade.PositionClose(position.SelectByTicket(ticket));

// Modify position SL/TP
trade.PositionModify(ticket, newSL, newTP);

// Place pending order
trade.BuyStop(lotSize, price, _Symbol, sl, tp);
trade.SellStop(lotSize, price, _Symbol, sl, tp);
trade.BuyLimit(lotSize, price, _Symbol, sl, tp);
trade.SellLimit(lotSize, price, _Symbol, sl, tp);
```

## MQL5 Position Management
```cpp
#include <Trade/PositionInfo.mqh>

CPositionInfo position;

// Iterate open positions
for (int i = PositionsTotal() - 1; i >= 0; i--) {
    if (position.SelectByIndex(i)) {
        if (position.Symbol() == _Symbol && position.Magic() == magicNumber) {
            // Process position
            double openPrice = position.PriceOpen();
            double currentSL = position.StopLoss();
            double currentTP = position.TakeProfit();
            long ticket = position.Ticket();
        }
    }
}

// Check for existing position
bool HasOpenPosition() {
    for (int i = PositionsTotal() - 1; i >= 0; i--) {
        if (position.SelectByIndex(i)) {
            if (position.Symbol() == _Symbol && position.Magic() == magicNumber)
                return true;
        }
    }
    return false;
}
```

## MQL5 Order Management (Pending Orders)
```cpp
#include <Trade/OrderInfo.mqh>

COrderInfo order;

// Iterate pending orders
for (int i = OrdersTotal() - 1; i >= 0; i--) {
    if (order.SelectByIndex(i)) {
        if (order.Symbol() == _Symbol && order.Magic() == magicNumber) {
            // Delete pending order
            trade.OrderDelete(order.Ticket());
        }
    }
}
```

## MQL5 History
```cpp
#include <Trade/HistoryOrderInfo.mqh>
#include <Trade/HistoryDealInfo.mqh>

CHistoryOrderInfo historyOrder;
CHistoryDealInfo historyDeal;

// Select from history
HistorySelect(startTime, TimeCurrent());

for (int i = HistoryOrdersTotal() - 1; i >= 0; i--) {
    if (historyOrder.SelectByIndex(i)) {
        // Check order details
    }
}
```

## MQL4 Trading (Legacy)
```cpp
// Open buy
int ticket = OrderSend(_Symbol, OP_BUY, lotSize, Ask, slippage, sl, tp, "Buy EA", magicNumber, 0, clrGreen);

// Open sell
int ticket = OrderSend(_Symbol, OP_SELL, lotSize, Bid, slippage, sl, tp, "Sell EA", magicNumber, 0, clrRed);

// Close order
OrderClose(ticket, lotSize, OrderClosePrice(), slippage);

// Modify order
OrderModify(ticket, OrderOpenPrice(), newSL, newTP, 0);

// Iterate orders
for (int i = OrdersTotal() - 1; i >= 0; i--) {
    if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) {
        if (OrderSymbol() == _Symbol && OrderMagicNumber() == magicNumber) {
            // Process
        }
    }
}
```

## Key Differences MQL4 vs MQL5
| Feature | MQL4 | MQL5 |
|---------|------|------|
| Trade execution | OrderSend() | CTrade class |
| Position/Order model | Combined (orders) | Separate positions & orders |
| History access | OrderSelect(MODE_HISTORY) | HistorySelect() + HistoryOrderInfo |
| Hedging | Account-based | Position-based |
| Filling modes | Not available | ORDER_FILLING_FOK/IOC/RETURN |
| SL/TP in points | Yes (as price) | Yes (as price) |

## Common Patterns
- Always verify position count before trading
- Check `TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)` before trading
- Check `AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)` for expert permission
- Use `SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE)` for price rounding
- Round prices with `NormalizeDouble(price, digits)`
