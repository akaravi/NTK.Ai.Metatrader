import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config import settings
from db import db

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
}


class MT5Service:
    def __init__(self):
        self._connected = False

    def connect(self) -> bool:
        """Initialize connection to MetaTrader 5 terminal."""
        if not mt5.initialize():
            self._connected = False
            return False
        self._connected = True
        return True

    def disconnect(self):
        """Shutdown connection."""
        if self._connected:
            mt5.shutdown()
            self._connected = False

    def ensure_connected(self) -> bool:
        """Check if terminal is connected and reconnect if needed."""
        try:
            term_info = mt5.terminal_info()
            if term_info is None or not term_info.connected:
                return self.connect()
            self._connected = True
            return True
        except Exception:
            return False

    def get_terminal_status(self) -> Dict[str, Any]:
        """Get terminal connectivity and algorithmic trading permissions."""
        if not self.ensure_connected():
            return {
                "connected": False,
                "trade_allowed": False,
                "error": "عدم امکان اتصال به ترمینال MetaTrader 5"
            }
        t_info = mt5.terminal_info()
        return {
            "connected": bool(t_info.connected) if t_info else False,
            "trade_allowed": bool(t_info.trade_allowed) if t_info else False,
            "tradeapi_disabled": bool(t_info.tradeapi_disabled) if t_info else False,
            "name": t_info.name if t_info else "Unknown",
            "path": t_info.path if t_info else "",
            "build": t_info.build if t_info else 0,
        }

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Fetch real-time MT5 account information."""
        if not self.ensure_connected():
            return None
        acc = mt5.account_info()
        if acc is None:
            return None
        return {
            "login": acc.login,
            "trade_mode": "Demo" if acc.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else "Real",
            "currency": acc.currency,
            "balance": round(acc.balance, 2),
            "equity": round(acc.equity, 2),
            "profit": round(acc.profit, 2),
            "margin": round(acc.margin, 2),
            "margin_free": round(acc.margin_free, 2),
            "margin_level": round(acc.margin_level, 2) if acc.margin_level else 0.0,
            "leverage": acc.leverage,
            "server": acc.server,
            "company": acc.company,
        }

    def get_available_symbols(self, filter_popular: bool = True) -> List[str]:
        """Fetch list of available tradeable symbols."""
        if not self.ensure_connected():
            return ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]
        
        popular_defaults = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD",
            "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
            "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "US500", "USTEC"
        ]
        
        symbols = mt5.symbols_get()
        if not symbols:
            return popular_defaults
        
        available = {s.name.upper(): s.name for s in symbols}
        if filter_popular:
            found = []
            for p in popular_defaults:
                if p in available:
                    found.append(available[p])
                elif f"{p}.m" in available:
                    found.append(available[f"{p}.m"])
                elif f"{p}_i" in available:
                    found.append(available[f"{p}_i"])
            if found:
                return found
        
        return [s.name for s in symbols[:50]]

    def get_symbol_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get live tick, spread, and contract details for a symbol."""
        if not self.ensure_connected():
            return None
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            symbol_info = mt5.symbol_info(symbol.upper())
            if symbol_info is None:
                return None
            symbol = symbol.upper()

        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)
            symbol_info = mt5.symbol_info(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None

        spread_points = round((tick.ask - tick.bid) / symbol_info.point, 1) if symbol_info.point else 0

        return {
            "symbol": symbol,
            "ask": tick.ask,
            "bid": tick.bid,
            "last": tick.last,
            "spread_points": spread_points,
            "digits": symbol_info.digits,
            "point": symbol_info.point,
            "volume_min": symbol_info.volume_min,
            "volume_max": symbol_info.volume_max,
            "volume_step": symbol_info.volume_step,
            "trade_mode": symbol_info.trade_mode,
            "time": datetime.fromtimestamp(tick.time).strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_multi_symbol_ticks(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fetch ultra-fast tick snapshots for multiple symbols concurrently."""
        symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]
        results = {}
        if not self.ensure_connected():
            return results

        for s in symbols:
            info = self.get_symbol_overview(s)
            if info:
                results[s] = info
        return results

    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> List[str]:
        """Recognize Japanese Candlestick Patterns on recent candles."""
        patterns = []
        if len(df) < 3:
            return patterns

        c0 = df.iloc[-1]
        c1 = df.iloc[-2]
        c2 = df.iloc[-3]

        body0 = abs(c0["close"] - c0["open"])
        range0 = c0["high"] - c0["low"]
        is_bull0 = c0["close"] > c0["open"]
        is_bear0 = c0["close"] < c0["open"]

        is_bull1 = c1["close"] > c1["open"]
        is_bear1 = c1["close"] < c1["open"]

        # 1. Doji
        if range0 > 0 and body0 / range0 < 0.1:
            patterns.append("Doji (بلاتکلیفی بازار)")

        # 2. Bullish Engulfing
        if is_bear1 and is_bull0 and c0["close"] > c1["open"] and c0["open"] < c1["close"]:
            patterns.append("Bullish Engulfing (پوشای صعودی)")

        # 3. Bearish Engulfing
        if is_bull1 and is_bear0 and c0["close"] < c1["open"] and c0["open"] > c1["close"]:
            patterns.append("Bearish Engulfing (پوشای نزولی)")

        # 4. Hammer (Bullish Reversal)
        lower_shadow = min(c0["open"], c0["close"]) - c0["low"]
        upper_shadow = c0["high"] - max(c0["open"], c0["close"])
        if range0 > 0 and lower_shadow > body0 * 2 and upper_shadow < body0 * 0.5:
            patterns.append("Hammer (چکش صعودی)")

        # 5. Shooting Star (Bearish Reversal)
        if range0 > 0 and upper_shadow > body0 * 2 and lower_shadow < body0 * 0.5:
            patterns.append("Shooting Star (ستاره ثاقب نزولی)")

        return patterns

    def get_candles_with_indicators(self, symbol: str, timeframe_str: str = "M15", count: int = 100) -> Optional[Dict[str, Any]]:
        """
        Fetch historical candles and calculate institutional technical indicators:
        EMA 9, 21, 50, 200, RSI 14, MACD, ATR, Bollinger Bands, Pivot Points, Patterns, Trend.
        """
        if not self.ensure_connected():
            return None

        tf = TIMEFRAME_MAP.get(timeframe_str.upper(), mt5.TIMEFRAME_M15)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) < 30:
            rates = mt5.copy_rates_from_pos(symbol.upper(), tf, 0, count)
            if rates is None or len(rates) < 30:
                return None
            symbol = symbol.upper()

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # EMAs
        df["ema9"] = close.ewm(span=9, adjust=False).mean()
        df["ema21"] = close.ewm(span=21, adjust=False).mean()
        df["ema50"] = close.ewm(span=50, adjust=False).mean()

        # RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["rsi"] = df["rsi"].fillna(50.0)

        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        # ATR (14)
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=14).mean().bfill()

        # Bollinger Bands (20, 2.0)
        df["bb_mid"] = close.rolling(window=20).mean()
        df["bb_std"] = close.rolling(window=20).std()
        df["bb_upper"] = df["bb_mid"] + (df["bb_std"] * 2.0)
        df["bb_lower"] = df["bb_mid"] - (df["bb_std"] * 2.0)

        # Last candle technical summary
        last = df.iloc[-1]
        current_price = float(last["close"])
        rsi_val = round(float(last["rsi"]), 2)
        ema9_val = round(float(last["ema9"]), 5)
        ema21_val = round(float(last["ema21"]), 5)
        ema50_val = round(float(last["ema50"]), 5)
        atr_val = round(float(last["atr"]), 5)
        bb_upper = round(float(last["bb_upper"]), 5) if not np.isnan(last["bb_upper"]) else current_price
        bb_lower = round(float(last["bb_lower"]), 5) if not np.isnan(last["bb_lower"]) else current_price

        # Trend Determination
        if ema9_val > ema21_val and current_price > ema50_val:
            trend = "صعودی قوی (Bullish)"
            trend_code = "BULLISH"
        elif ema9_val < ema21_val and current_price < ema50_val:
            trend = "نزولی قوی (Bearish)"
            trend_code = "BEARISH"
        else:
            trend = "خنثی / رنج (Neutral/Range)"
            trend_code = "NEUTRAL"

        # Recent Support & Resistance levels
        recent_low = round(float(df["low"].tail(30).min()), 5)
        recent_high = round(float(df["high"].tail(30).max()), 5)

        # Pivot Points calculation
        prev_bar = df.iloc[-2]
        p_high = float(prev_bar["high"])
        p_low = float(prev_bar["low"])
        p_close = float(prev_bar["close"])
        pivot_p = round((p_high + p_low + p_close) / 3.0, 5)
        pivot_r1 = round((2 * pivot_p) - p_low, 5)
        pivot_s1 = round((2 * pivot_p) - p_high, 5)

        # Candlestick Patterns
        patterns = self._detect_candlestick_patterns(df)

        # Build candle array
        candles_list = []
        for _, row in df.tail(50).iterrows():
            candles_list.append({
                "time": int(row["time"].timestamp()),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["tick_volume"]),
            })

        return {
            "symbol": symbol,
            "timeframe": timeframe_str,
            "current_price": current_price,
            "rsi": rsi_val,
            "ema9": ema9_val,
            "ema21": ema21_val,
            "ema50": ema50_val,
            "atr": atr_val,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "macd": round(float(last["macd"]), 5),
            "macd_signal": round(float(last["macd_signal"]), 5),
            "support": recent_low,
            "resistance": recent_high,
            "pivot_point": pivot_p,
            "pivot_r1": pivot_r1,
            "pivot_s1": pivot_s1,
            "patterns": patterns,
            "trend": trend,
            "trend_code": trend_code,
            "candles": candles_list
        }

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Fetch all currently open positions."""
        if not self.ensure_connected():
            return []
        
        positions = mt5.positions_get()
        if positions is None or len(positions) == 0:
            return []
        
        result = []
        for p in positions:
            result.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
                "type_code": p.type,
                "volume": round(p.volume, 2),
                "open_price": p.price_open,
                "current_price": p.price_current,
                "sl": p.sl,
                "tp": p.tp,
                "profit": round(p.profit, 2),
                "swap": round(p.swap, 2),
                "comment": p.comment,
                "time": datetime.fromtimestamp(p.time).strftime("%Y-%m-%d %H:%M:%S")
            })
        return result

    def get_filling_type(self, symbol: str) -> int:
        """Determine correct MT5 filling type supported by the broker."""
        info = mt5.symbol_info(symbol)
        if info is None:
            return mt5.ORDER_FILLING_IOC
        
        filling = info.filling_mode
        if filling & 1:
            return mt5.ORDER_FILLING_FOK
        elif filling & 2:
            return mt5.ORDER_FILLING_IOC
        return mt5.ORDER_FILLING_RETURN

    def execute_order(self, symbol: str, order_type: str, volume: float,
                      sl: Optional[float] = None, tp: Optional[float] = None,
                      comment: str = "NTK AI Trader", confidence: float = 75.0,
                      prediction_title: str = "تحلیل تکنیکال", prediction_reason: str = "") -> Dict[str, Any]:
        """
        Execute Buy or Sell Market Order in MT5.
        """
        if not self.ensure_connected():
            return {"success": False, "error": "عدم اتصال به متاتریدر ۵"}

        # Check Algo Trading permission
        t_info = mt5.terminal_info()
        if t_info and not t_info.trade_allowed:
            return {
                "success": False,
                "retcode": 10027,
                "error": "معاملات خودکار در متاتریدر غیرفعال است (دکمه Algo Trading را در متاتریدر روشن کنید)."
            }

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            symbol_info = mt5.symbol_info(symbol.upper())
            if symbol_info is None:
                return {"success": False, "error": f"نماد {symbol} یافت نشد"}
            symbol = symbol.upper()

        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"success": False, "error": f"عدم امکان دریافت قیمت لحظه‌ای {symbol}"}

        # Normalize volume to symbol limits
        volume = max(symbol_info.volume_min, min(symbol_info.volume_max, volume))
        if symbol_info.volume_step > 0:
            volume = round(round(volume / symbol_info.volume_step) * symbol_info.volume_step, 2)

        order_type_code = mt5.ORDER_TYPE_BUY if order_type.upper() == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if order_type_code == mt5.ORDER_TYPE_BUY else tick.bid

        point = symbol_info.point
        if sl is None and settings.SL_PIPS > 0:
            sl_distance = settings.SL_PIPS * 10 * point
            sl = round(price - sl_distance if order_type_code == mt5.ORDER_TYPE_BUY else price + sl_distance, symbol_info.digits)
        if tp is None and settings.TP_PIPS > 0:
            tp_distance = settings.TP_PIPS * 10 * point
            tp = round(price + tp_distance if order_type_code == mt5.ORDER_TYPE_BUY else price - tp_distance, symbol_info.digits)

        filling_type = self.get_filling_type(symbol)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type_code,
            "price": float(price),
            "sl": float(sl) if sl else 0.0,
            "tp": float(tp) if tp else 0.0,
            "deviation": 20,
            "magic": settings.MAGIC_NUMBER,
            "comment": comment[:31],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_type,
        }

        result = mt5.order_send(request)
        if result is None:
            last_err = mt5.last_error()
            return {"success": False, "error": f"خطا در ارسال سفارش: {last_err}"}
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            # Persist open trade to SQLite with prediction attribution
            db.record_trade_open(
                ticket=result.order,
                symbol=symbol,
                trade_type=order_type,
                volume=volume,
                open_price=float(result.price),
                sl=sl,
                tp=tp,
                comment=comment,
                strategy=prediction_title,
                confidence=confidence,
                prediction_title=prediction_title,
                prediction_reason=prediction_reason
            )
            return {
                "success": True,
                "order_ticket": result.order,
                "deal_ticket": result.deal,
                "volume": result.volume,
                "price": result.price,
                "comment": "سفارش با موفقیت باز شد"
            }
        else:
            return {
                "success": False,
                "retcode": result.retcode,
                "comment": result.comment,
                "error": f"خطا از سوی بروکر/ترمینال: {result.comment} (کد: {result.retcode})"
            }

    def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> Dict[str, Any]:
        """Modify Stop Loss and Take Profit for an open position."""
        if not self.ensure_connected():
            return {"success": False, "error": "عدم اتصال به متاتریدر ۵"}

        positions = mt5.positions_get(ticket=ticket)
        if positions is None or len(positions) == 0:
            return {"success": False, "error": f"پوزیشن #{ticket} یافت نشد"}

        pos = positions[0]
        symbol = pos.symbol
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {"success": False, "error": f"نماد {symbol} در مارکت واچ یافت نشد"}

        digits = symbol_info.digits
        new_sl = round(float(sl), digits) if sl is not None else pos.sl
        new_tp = round(float(tp), digits) if tp is not None else pos.tp

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": symbol,
            "sl": new_sl,
            "tp": new_tp,
            "magic": settings.MAGIC_NUMBER,
        }

        result = mt5.order_send(request)
        if result is None:
            return {"success": False, "error": f"خطا در ارسال دستور تغییر حد ضرر/سود: {mt5.last_error()}"}

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "success": True,
                "ticket": ticket,
                "sl": new_sl,
                "tp": new_tp,
                "message": f"حد ضرر و سود پوزیشن #{ticket} با موفقیت بروزرسانی شد (SL: {new_sl}, TP: {new_tp})"
            }
        else:
            return {
                "success": False,
                "retcode": result.retcode,
                "error": f"خطا در تغییر پوزیشن: {result.comment} (کد: {result.retcode})"
            }

    def set_breakeven(self, ticket: int, buffer_pips: float = 0.5) -> Dict[str, Any]:
        """Move Stop Loss of a position to entry price plus optional buffer."""
        if not self.ensure_connected():
            return {"success": False, "error": "عدم اتصال به متاتریدر ۵"}

        positions = mt5.positions_get(ticket=ticket)
        if positions is None or len(positions) == 0:
            return {"success": False, "error": f"پوزیشن #{ticket} یافت نشد"}

        pos = positions[0]
        symbol = pos.symbol
        point = 0.0001 if "JPY" not in symbol.upper() and "XAU" not in symbol.upper() else (0.01 if "JPY" in symbol.upper() else 0.1)
        buffer_pts = buffer_pips * point * 10

        if pos.type == mt5.ORDER_TYPE_BUY:
            target_sl = pos.price_open + buffer_pts
            if pos.price_current <= target_sl:
                return {"success": False, "error": "قیمت فعلی هنوز در حاشیه سود کافی برای ریسک‌فری قرار ندارد"}
        else:
            target_sl = pos.price_open - buffer_pts
            if pos.price_current >= target_sl:
                return {"success": False, "error": "قیمت فعلی هنوز در حاشیه سود کافی برای ریسک‌فری قرار ندارد"}

        return self.modify_position(ticket=ticket, sl=target_sl, tp=pos.tp)

    def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close an open position by its ticket number."""
        if not self.ensure_connected():
            return {"success": False, "error": "عدم اتصال به متاتریدر ۵"}

        positions = mt5.positions_get(ticket=ticket)
        if positions is None or len(positions) == 0:
            return {"success": False, "error": f"پوزیشن #{ticket} یافت نشد"}

        pos = positions[0]
        symbol = pos.symbol
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None or symbol_info is None:
            return {"success": False, "error": "عدم دسترسی به قیمت فعلی نماد"}

        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
        filling_type = self.get_filling_type(symbol)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": settings.MAGIC_NUMBER,
            "comment": f"Close #{ticket}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_type,
        }

        result = mt5.order_send(request)
        if result is None:
            return {"success": False, "error": f"خطا در بستن سفارش: {mt5.last_error()}"}

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            # Persist closed trade to SQLite
            db.record_trade_close(
                ticket=ticket,
                close_price=float(price),
                profit=float(pos.profit)
            )
            return {"success": True, "comment": f"پوزیشن #{ticket} با موفقیت بسته شد"}
        else:
            return {
                "success": False,
                "retcode": result.retcode,
                "error": f"خطا در بستن پوزیشن: {result.comment} (کد: {result.retcode})"
            }
    def close_all_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Close all open positions or all positions for a specific symbol."""
        positions = self.get_open_positions()
        if not positions:
            return {"success": True, "closed_count": 0, "message": "هیچ پوزیشن بازی وجود ندارد"}

        closed = 0
        errors = []
        for p in positions:
            if symbol and p["symbol"].upper() != symbol.upper():
                continue
            res = self.close_position(p["ticket"])
            if res.get("success"):
                closed += 1
            else:
                errors.append(f"#{p['ticket']}: {res.get('error')}")

        return {
            "success": len(errors) == 0,
            "closed_count": closed,
            "errors": errors,
            "message": f"تعداد {closed} پوزیشن بسته شد."
        }

    def close_profitable_positions(self) -> Dict[str, Any]:
        """Close all open positions that are currently in profit to lock in gains."""
        positions = self.get_open_positions()
        profitable = [p for p in positions if p["profit"] > 0]
        if not profitable:
            return {"success": True, "closed_count": 0, "message": "هیچ پوزیشن سوددهی برای بستن وجود ندارد."}

        closed = 0
        errors = []
        total_profit = 0.0
        for p in profitable:
            res = self.close_position(p["ticket"])
            if res.get("success"):
                closed += 1
                total_profit += p["profit"]
            else:
                errors.append(f"#{p['ticket']}: {res.get('error')}")

        return {
            "success": len(errors) == 0,
            "closed_count": closed,
            "total_profit_locked": round(total_profit, 2),
            "errors": errors,
            "message": f"تعداد {closed} معامله سودده به مجموع سود ${total_profit:.2f} با موفقیت بسته شد."
        }

    def get_portfolio_correlation_matrix(self, symbols: Optional[List[str]] = None, timeframe: str = "H1", count: int = 60) -> Dict[str, Any]:
        """
        Compute Pearson correlation matrix across portfolio symbols.
        """
        if not self.ensure_connected():
            return {"symbols": [], "matrix": []}

        target_symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "XAUUSD", "BTCUSD"]
        price_series = {}

        tf_const = TIMEFRAME_MAP.get(timeframe, mt5.TIMEFRAME_H1)
        for sym in target_symbols:
            rates = mt5.copy_rates_from_pos(sym, tf_const, 0, count)
            if rates is not None and len(rates) > 10:
                df = pd.DataFrame(rates)
                price_series[sym] = df["close"]

        if not price_series or len(price_series) < 2:
            return {"symbols": list(price_series.keys()), "matrix": []}

        combined_df = pd.DataFrame(price_series).dropna()
        corr_df = combined_df.corr().round(2)

        symbols_list = list(corr_df.columns)
        matrix_data = []
        for s1 in symbols_list:
            row_vals = []
            for s2 in symbols_list:
                val = float(corr_df.loc[s1, s2])
                row_vals.append({
                    "target": s2,
                    "correlation": val,
                    "strength": "قوی مثبت" if val >= 0.75 else ("قوی منفی" if val <= -0.75 else ("متوسط" if abs(val) >= 0.4 else "خنثی/مستقل"))
                })
            matrix_data.append({"symbol": s1, "correlations": row_vals})

        return {
            "symbols": symbols_list,
            "timeframe": timeframe,
            "candle_count": count,
            "matrix": matrix_data
        }

    def get_net_currency_exposure(self) -> Dict[str, Any]:
        """
        Calculate net lot and dollar exposure across individual currencies (USD, EUR, GBP, JPY, XAU, etc.).
        """
        positions = self.get_open_positions()
        if not positions:
            return {
                "total_positions": 0,
                "total_lots": 0.0,
                "net_exposure": {},
                "risk_assessment_fa": "هیچ پوزیشن بازی وجود ندارد. ریسک ارزی در سطح صفر است."
            }

        currency_lots = {
            "USD": 0.0, "EUR": 0.0, "GBP": 0.0, "JPY": 0.0,
            "CHF": 0.0, "AUD": 0.0, "CAD": 0.0, "NZD": 0.0,
            "XAU": 0.0, "BTC": 0.0
        }

        total_lots = 0.0
        for p in positions:
            sym = p["symbol"].upper()
            vol = float(p["volume"])
            p_type = p["type"]
            total_lots += vol

            # Parse Base and Quote
            if sym.startswith("XAU"):
                base, quote = "XAU", "USD"
            elif sym.startswith("BTC"):
                base, quote = "BTC", "USD"
            elif len(sym) >= 6:
                base, quote = sym[:3], sym[3:6]
            else:
                base, quote = sym, "USD"

            if p_type == "BUY":
                currency_lots[base] = currency_lots.get(base, 0.0) + vol
                currency_lots[quote] = currency_lots.get(quote, 0.0) - vol
            else:  # SELL
                currency_lots[base] = currency_lots.get(base, 0.0) - vol
                currency_lots[quote] = currency_lots.get(quote, 0.0) + vol

        # Clean and round exposures
        exposure_summary = []
        max_exposure_curr = "USD"
        max_lot_val = 0.0

        for curr, lot_val in currency_lots.items():
            val_rounded = round(lot_val, 2)
            if abs(val_rounded) > 0.001:
                if abs(val_rounded) > max_lot_val:
                    max_lot_val = abs(val_rounded)
                    max_exposure_curr = curr
                exposure_summary.append({
                    "currency": curr,
                    "net_lots": val_rounded,
                    "direction": "خرید خالص (Long)" if val_rounded > 0 else "فروش خالص (Short)",
                    "color": "emerald" if val_rounded > 0 else "rose",
                    "risk_tier": "بالا (High)" if abs(val_rounded) >= 0.08 else ("متوسط" if abs(val_rounded) >= 0.03 else "ایمن")
                })

        exposure_summary.sort(key=lambda x: abs(x["net_lots"]), reverse=True)

        risk_fa = f"بیشترین درگیری پورتفوی روی ارز {max_exposure_curr} با حجم خالص {max_lot_val:.2f} لات است."
        if max_lot_val >= 0.08:
            risk_fa += " ⚠️ هشدار تمرکز ریسک: حجم درگیری این ارز بالاست."
        else:
            risk_fa += " ✅ توزیع ریسک سبد متوازن و در محدوده امن قرار دارد."

        return {
            "total_positions": len(positions),
            "total_lots": round(total_lots, 2),
            "net_exposure": exposure_summary,
            "dominant_currency": max_exposure_curr,
            "risk_assessment_fa": risk_fa
        }


mt5_service = MT5Service()
