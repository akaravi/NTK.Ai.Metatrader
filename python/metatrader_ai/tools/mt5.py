from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta, date
from functools import wraps
from .tool import Tool, Property, Parameters

try:
    import MetaTrader5
except ImportError:
    MetaTrader5 = None  # type: ignore[assignment]


def _require_mt5_installed() -> None:
    if MetaTrader5 is None:
        raise ImportError(
            "MetaTrader5 module not found. It is only available on Windows/Linux and can be installed using 'pip install --upgrade MetaTrader5'."
        )


def _require_connection(method: callable):
    """Decorator that raises RuntimeError if MT5 is not connected before calling a method."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        _require_mt5_installed()
        if not MetaTrader5.terminal_info() or not MetaTrader5.terminal_info().connected:
            raise RuntimeError("Not connected to MetaTrader 5. Call login() first.")
        return method(self, *args, **kwargs)

    return wrapper


class MT5:
    """Class to interact with MetaTrader 5"""

    def __init__(
        self, account_number: int, account_password: str, broker_server_name: str
    ):
        _require_mt5_installed()
        self._account_number = account_number
        self._account_password = account_password
        self._broker_server_name = broker_server_name

    @property
    @_require_connection
    def account_info(self):
        """Get account information"""
        return MetaTrader5.account_info()

    @property
    @_require_connection
    def account_balance(self) -> float:
        """Get the account balance"""
        return MetaTrader5.account_info().balance

    @property
    @_require_connection
    def account_company(self) -> str:
        """Get the name of the brokerage company"""
        return MetaTrader5.account_info().company

    @property
    @_require_connection
    def account_currency(self) -> str:
        """Get the account currency"""
        return MetaTrader5.account_info().currency

    @property
    @_require_connection
    def account_equity(self) -> float:
        """Get the account equity"""
        return MetaTrader5.account_info().equity

    @property
    @_require_connection
    def account_name(self) -> str:
        """Get the account holder's name"""
        return MetaTrader5.account_info().name

    @property
    @_require_connection
    def account_number(self) -> int:
        """Get the account number from the live MT5 session"""
        return MetaTrader5.account_info().login

    @property
    @_require_connection
    def account_profit(self) -> float:
        """Get the current profit/loss of the account"""
        return MetaTrader5.account_info().profit

    @property
    def common_data_path(self) -> str:
        """Get the path to the common data folder of MetaTrader 5"""
        return MetaTrader5.terminal_info().commondata_path

    @property
    def data_path(self) -> str:
        """Get the path to the data folder of MetaTrader 5"""
        return MetaTrader5.terminal_info().data_path

    @property
    def is_connected(self) -> bool:
        """Check if the terminal is connected to a trade server"""
        info = MetaTrader5.terminal_info()
        return info.connected if info else False

    @property
    def is_trade_enabled(self) -> bool:
        """Check if auto-trading is enabled in MetaTrader 5"""
        return MetaTrader5.terminal_info().trade_allowed

    @property
    def last_error(self) -> str:
        """
        Get the last error message from MetaTrader 5 as a string.
        """
        error_code, _description = MetaTrader5.last_error()
        error_map = {
            1: "Success",
            -1: "Generic fail",
            -2: "Invalid arguments/parameters",
            -3: "No memory condition",
            -4: "No history",
            -5: "Invalid version",
            -6: "Authorization failed",
            -7: "Unsupported method",
            -8: "Auto-trading disabled",
            -10000: "Internal IPC general error",
            -10001: "Internal IPC send failed",
            -10002: "Internal IPC receive failed",
            -10003: "Internal IPC initialization fail",
            -10004: "Internal IPC no ipc",
            -10005: "Internal timeout",
        }
        return error_map.get(error_code, f"Unknown error code: {error_code}")

    @property
    def max_bars(self) -> int:
        """Get the maximum number of bars available"""
        return MetaTrader5.terminal_info().maxbars

    @property
    @_require_connection
    def orders_total(self) -> int:
        """Get the total number of pending orders"""
        return MetaTrader5.orders_total()

    @property
    @_require_connection
    def positions_total(self) -> int:
        """Get the total number of open positions"""
        return MetaTrader5.positions_total()

    @property
    def terminal_info(self) -> MetaTrader5.TerminalInfo:
        """Get terminal information"""
        return MetaTrader5.terminal_info()

    @property
    def version(self) -> str:
        """Get the version of MetaTrader 5 terminal"""
        return MetaTrader5.terminal_info().version

    @_require_connection
    def close(self) -> None:
        """Close MetaTrader 5 connection"""
        MetaTrader5.shutdown()

    def __division(self, numerator, denominator):
        """Safely perform division and handle division by zero"""
        return 0 if denominator == 0 else numerator / denominator

    def __get_filling_mode(self, symbol: str, is_pending: bool):
        """
        Determine the correct filling mode by porting
        """
        info = MetaTrader5.symbol_info(symbol)
        if info is None:
            return MetaTrader5.ORDER_FILLING_RETURN

        exec_mode = info.trade_exemode
        filling = info.filling_mode

        INSTANT = MetaTrader5.SYMBOL_TRADE_EXECUTION_INSTANT
        REQUEST = MetaTrader5.SYMBOL_TRADE_EXECUTION_REQUEST
        MARKET = MetaTrader5.SYMBOL_TRADE_EXECUTION_MARKET
        # EXCHANGE = anything else

        # INSTANT / REQUEST: terminal sets filling automatically, omit the field
        if exec_mode in (INSTANT, REQUEST):
            return None

        # MARKET execution
        if exec_mode == MARKET:
            if not is_pending:
                # Market orders: FOK -> IOC; RETURN is not valid here
                if filling & 1:  # SYMBOL_FILLING_FOK
                    return MetaTrader5.ORDER_FILLING_FOK
                if filling & 2:  # SYMBOL_FILLING_IOC
                    return MetaTrader5.ORDER_FILLING_IOC
                # Neither supported — broker misconfiguration, best effort
                return MetaTrader5.ORDER_FILLING_RETURN
            # Pending orders in MARKET mode: no filling needed
            return None

        # EXCHANGE execution
        if is_pending:
            # Pending orders always use RETURN in EXCHANGE mode
            return MetaTrader5.ORDER_FILLING_RETURN
        # Market orders in EXCHANGE: FOK -> IOC
        if filling & 1:
            return MetaTrader5.ORDER_FILLING_FOK
        if filling & 2:
            return MetaTrader5.ORDER_FILLING_IOC
        return MetaTrader5.ORDER_FILLING_RETURN

    def __get_order_entry_price(self, symbol: str, order_type: str):
        """Get the order entry price based on selected side of the spread."""
        tick = MetaTrader5.symbol_info_tick(symbol)
        if tick is None:
            print(
                f"\033[91mFailed to retrieve tick for {symbol}: {self.last_error}\033[0m"
            )
            return None
        return (
            tick.ask
            if order_type.lower() in {"buy", "buy limit", "buy stop"}
            else tick.bid
        )

    def __resolve_order_type(self, order_type: str):
        """Map human-readable order type to (MT5 type constant, action constant, is_pending)."""
        order_type_map = {
            "buy": (MetaTrader5.ORDER_TYPE_BUY, MetaTrader5.TRADE_ACTION_DEAL, False),
            "buy limit": (
                MetaTrader5.ORDER_TYPE_BUY_LIMIT,
                MetaTrader5.TRADE_ACTION_PENDING,
                True,
            ),
            "buy stop": (
                MetaTrader5.ORDER_TYPE_BUY_STOP,
                MetaTrader5.TRADE_ACTION_PENDING,
                True,
            ),
            "sell": (MetaTrader5.ORDER_TYPE_SELL, MetaTrader5.TRADE_ACTION_DEAL, False),
            "sell limit": (
                MetaTrader5.ORDER_TYPE_SELL_LIMIT,
                MetaTrader5.TRADE_ACTION_PENDING,
                True,
            ),
            "sell stop": (
                MetaTrader5.ORDER_TYPE_SELL_STOP,
                MetaTrader5.TRADE_ACTION_PENDING,
                True,
            ),
        }
        return order_type_map.get(order_type.lower())

    def __validate_sl_tp(
        self,
        order_type: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
    ) -> bool:
        """
        Validate that SL and TP are on the correct side of the entry price.

        Returns True if valid, False (with a printed message) if not.
        """
        buy_types = {"buy", "buy limit", "buy stop"}
        sell_types = {"sell", "sell limit", "sell stop"}
        ot = order_type.lower()

        if ot in buy_types:
            if take_profit != 0 and take_profit < entry:
                print(
                    f"\033[91mInvalid SL/TP: take_profit ({take_profit}) must be above entry ({entry}) for {ot}\033[0m"
                )
                return False
            if stop_loss != 0 and stop_loss > entry:
                print(
                    f"\033[91mInvalid SL/TP: stop_loss ({stop_loss}) must be below entry ({entry}) for {ot}\033[0m"
                )
                return False
            if take_profit != 0 and stop_loss != 0 and take_profit < stop_loss:
                print(
                    f"\033[91mInvalid SL/TP: take_profit ({take_profit}) must be above stop_loss ({stop_loss}) for {ot}\033[0m"
                )
                return False

        elif ot in sell_types:
            if take_profit != 0 and take_profit > entry:
                print(
                    f"\033[91mInvalid SL/TP: take_profit ({take_profit}) must be below entry ({entry}) for {ot}\033[0m"
                )
                return False
            if stop_loss != 0 and stop_loss < entry:
                print(
                    f"\033[91mInvalid SL/TP: stop_loss ({stop_loss}) must be above entry ({entry}) for {ot}\033[0m"
                )
                return False
            if take_profit != 0 and stop_loss != 0 and take_profit > stop_loss:
                print(
                    f"\033[91mInvalid SL/TP: take_profit ({take_profit}) must be below stop_loss ({stop_loss}) for {ot}\033[0m"
                )
                return False

        else:
            print(
                f"\033[91m__validate_sl_tp: unrecognised order_type '{order_type}'\033[0m"
            )
            return False

        return True

    def __submit_order(
        self,
        method_name: str,
        symbol: str,
        order_type: str,
        lot: float,
        entry_price: float,
        slippage: int,
        stop_loss: float,
        take_profit: float,
        order_comment: str,
        magic_number: int,
    ) -> bool:
        """Submit a fully-priced order request to MT5."""
        order_meta = self.__resolve_order_type(order_type)
        if order_meta is None:
            print(
                f"\033[91m{method_name}: unrecognised order_type '{order_type}'\033[0m"
            )
            return False

        order_type_mt5, action, is_pending = order_meta

        filling_mode = self.__get_filling_mode(symbol, is_pending)

        request = {
            "action": action,
            "symbol": symbol,
            "type": order_type_mt5,
            "volume": float(lot),
            "price": float(entry_price),
            "deviation": int(slippage),
            "sl": float(stop_loss),
            "tp": float(take_profit),
            "comment": str(order_comment),
            "magic": int(magic_number),
            "type_time": MetaTrader5.ORDER_TIME_GTC,
        }

        if filling_mode is not None:
            request["type_filling"] = filling_mode

        result = MetaTrader5.order_send(request)
        if result is None:
            print(
                f"\033[91m{method_name} failed, no result returned: {self.last_error}\033[0m"
            )
            return False
        if result.retcode != MetaTrader5.TRADE_RETCODE_DONE:
            print(
                f"\033[91m{method_name} failed, retcode={result.retcode}, comment={result.comment}\033[0m"
            )
            return False
        return True

    @_require_connection
    def get_account_info(self) -> dict:
        """Get account information as a dictionary"""
        info = MetaTrader5.account_info()
        if info is None:
            print(f"\033[91mFailed to retrieve account info: {self.last_error}\033[0m")
            return {}
        return {
            "account_number": info.login,
            "account_name": info.name,
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "margin_level": info.margin_level,
            "currency": info.currency,
            "company": info.company,
            "profit": info.profit,
        }

    @_require_connection
    def get_history_position(self, ticket: int) -> list:
        """
        Get all deals related to the ticket number of a closed position
        Unlike get_order and get_position, this method returns a list of all deals associated with the ticket,
        which can include order modifications, partial closes, the initial opening deal, and the closing deal.
        """
        result = MetaTrader5.history_deals_get(ticket=ticket)
        if result is None or len(result) == 0:
            print(
                f"\033[91mHistorical position with ticket {ticket} not found: {self.last_error}\033[0m"
            )
            return []
        return result

    @_require_connection
    def get_history_positions(
        self,
        symbol: str = None,
        magic: int = None,
        from_date: datetime = None,
        to_date: datetime = None,
    ) -> list:
        """Get historical positions, optionally filtered by symbol, magic number, and date range"""
        def _parse_dt(val: Any, default_val: datetime) -> datetime:
            if val is None:
                return default_val
            if isinstance(val, datetime):
                return val.replace(tzinfo=None) if val.tzinfo else val
            if isinstance(val, (int, float)):
                return datetime.fromtimestamp(val)
            if isinstance(val, str):
                s = val.strip()
                try:
                    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                    if dt.tzinfo:
                        dt = dt.astimezone().replace(tzinfo=None)
                    return dt
                except Exception:
                    try:
                        return datetime.strptime(s[:10], "%Y-%m-%d")
                    except Exception:
                        return default_val
            return default_val

        now = datetime.now()
        from_dt = _parse_dt(from_date, datetime(now.year, now.month, now.day))
        to_dt = _parse_dt(to_date, now + timedelta(days=1))

        _positions = []
        deals = MetaTrader5.history_deals_get(from_dt, to_dt)
        if deals is None or len(deals) == 0:
            # Fallback to broader range if today's range was empty
            deals = MetaTrader5.history_deals_get(datetime(now.year, 1, 1), now + timedelta(days=1))
        if deals is None:
            print(f"\033[91mNo historical deals found: {self.last_error}\033[0m")
            return _positions
        for deal in deals:
            if (symbol is None or deal.symbol == symbol) and (
                magic is None or deal.magic == magic
            ):
                _positions.append(
                    {
                        "ticket": deal.ticket,
                        "time": datetime.fromtimestamp(
                            int(deal.time), tz=timezone.utc
                        ).isoformat(),
                        "type": deal.type,
                        "volume": deal.volume,
                        "magic_number": deal.magic,
                        "lot_size": deal.volume,
                        "price": deal.price,
                        "commission": deal.commission,
                        "swap": deal.swap,
                        "profit": deal.profit,
                        "fee": deal.fee,
                        "symbol": deal.symbol,
                        "comment": deal.comment,
                    }
                )
        return _positions

    @_require_connection
    def get_order(self, ticket: int):
        """Get a specific pending order by ticket number"""
        result = MetaTrader5.orders_get(ticket=ticket)
        if result is None or len(result) == 0:
            print(
                f"\033[91mOrder with ticket {ticket} not found: {self.last_error}\033[0m"
            )
            return None
        return result[0]

    @_require_connection
    def get_orders(self, currency_pair: str = None) -> list:
        """Get pending orders, optionally filtered by symbol"""
        _orders = []
        if MetaTrader5.orders_total() > 0:
            if currency_pair:
                order_data = MetaTrader5.orders_get(symbol=currency_pair)
            else:
                order_data = MetaTrader5.orders_get()

            if order_data is None:
                return _orders

            for order in order_data:
                _orders.append(
                    {
                        "ticket": order.ticket,
                        "time_setup": datetime.fromtimestamp(
                            int(order.time_setup), tz=timezone.utc
                        ).isoformat(),
                        "time_expiration": datetime.fromtimestamp(
                            int(order.time_expiration), tz=timezone.utc
                        ).isoformat(),
                        "type": order.type,
                        "type_time": order.type_time,
                        "type_filling": order.type_filling,
                        "state": order.state,
                        "magic_number": order.magic,
                        "lot_size": order.volume_current,
                        "open_price": order.price_open,
                        "stop_loss": order.sl,
                        "take_profit": order.tp,
                        "current_price": order.price_current,
                        "symbol": order.symbol,
                        "comment": order.comment,
                    }
                )
        return _orders

    def get_pip_value(self, symbol: str) -> float:
        """Get the pip value for a given symbol based on its digits and asset class"""
        _digits: int = self.get_symbol_info(symbol).get("digits", 0)

        if _digits >= 4:
            return 0.0001

        lowercase_symbol = symbol.lower()

        if re.search(
            r"us30|nas100|spx500|jpn225|uk100|fra40|esp35|us30.mini|nas100.mini|btcusd|ethusd|ltcusd|bnbusd|u30usd.hkt|nasusd.hkt|spxusd.hkt|225jpy.hkt|100gbp.hkt|f40eur.hkt|e35eur.hkt|us100.cash|us30.cash|us30.e8|us100.e8|us500.e8|ger40.e8|eu50.e8",
            lowercase_symbol,
        ):
            return 1.0

        if "xau" in lowercase_symbol:
            return 0.10

        return 0.01

    @_require_connection
    def get_position(self, ticket: int):
        """Get a specific open position by ticket number"""
        result = MetaTrader5.positions_get(ticket=ticket)
        if result is None or len(result) == 0:
            print(
                f"\033[91mPosition with ticket {ticket} not found: {self.last_error}\033[0m"
            )
            return None
        return result[0]

    @_require_connection
    def get_positions(self, currency_pair: str = None) -> list:
        """Get open positions, optionally filtered by symbol"""
        _positions = []
        if MetaTrader5.positions_total() > 0:
            if currency_pair:
                position_data = MetaTrader5.positions_get(symbol=currency_pair)
            else:
                position_data = MetaTrader5.positions_get()

            if position_data is None:
                return _positions

            for position in position_data:
                _positions.append(
                    {
                        "magic_number": position.magic,
                        "stop_loss": position.sl,
                        "take_profit": position.tp,
                        "comment": position.comment,
                        "lot_size": position.volume,
                        "type": position.type,
                        "symbol": position.symbol,
                        "swap": position.swap,
                        "ticket": position.ticket,
                        "open_price": position.price_open,
                        "current_price": position.price_current,
                        "profit": position.profit,
                        "status": False if position.price_open <= 0 else True,
                    }
                )
        return _positions

    @_require_connection
    def get_recent_bars(
        self, currency: str, timeframe: int, number_of_bars: int, shift: int = 0
    ) -> list:
        """Get recent bars for a given symbol, timeframe, and shift. Returns a list of dictionaries with time (ISO 8601 UTC), open, high, low, close, tick_volume, spread, and real_volume for each bar."""
        _bars = []

        if not MetaTrader5.symbol_select(currency, True):
            print(
                f"\033[91mFailed to select symbol {currency}: {self.last_error}\033[0m"
            )
            return _bars

        candle_data = MetaTrader5.copy_rates_from_pos(
            currency, timeframe, shift, number_of_bars
        )

        if candle_data is None:
            if self.last_error in ("Success", "No history"):
                print(
                    f"\033[91mNo bars available for {currency} at timeframe {timeframe} and shift {shift}\033[0m"
                )
            else:
                print(f"\033[91mFailed to retrieve bars: {self.last_error}\033[0m")
            return _bars

        for candle in candle_data:
            _bars.append(
                {
                    "time": datetime.fromtimestamp(
                        int(candle[0]), tz=timezone.utc
                    ).isoformat(),
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "tick_volume": int(candle[5]),
                    "spread": int(candle[6]),
                    "real_volume": int(candle[7]),
                }
            )
        return _bars

    @_require_connection
    def get_risk(
        self, use_risk, use_lot_size, percent_risk, stop_loss, lot_size, symbol
    ) -> float:
        """Get the lot size based on the percentage risk and stop loss in pips"""
        decimal_risk = percent_risk / 100
        account_risk = self.account_equity * decimal_risk
        lot_sizes = self.get_symbol_info(symbol).get("max_lot_size", 0)
        tick_value = self.get_symbol_info(symbol).get("tick_value", 0)
        account_company = self.account_company
        pip_value = self.get_pip_value(symbol)

        if symbol == "US30.mini":
            tick_value *= 100

        if symbol == "NAS100.mini":
            tick_value *= 100

        if account_company == "FTMO S.R.O." and pip_value == 1:
            tick_value *= 100

        max_loss_in_quote = self.__division(account_risk, tick_value)
        quote_division = self.__division(max_loss_in_quote, (stop_loss * pip_value))
        _get_risk = round(self.__division(quote_division, lot_sizes), 2)

        if use_risk and not use_lot_size:
            return _get_risk
        if use_lot_size and not use_risk:
            return round(lot_size, 2)
        return lot_size

    def get_symbol_info(self, currency_pair: str) -> dict:
        """Get symbol information for a given currency pair"""
        if not MetaTrader5.symbol_select(currency_pair, True):
            print(
                f"\033[91mFailed to select symbol {currency_pair}: {self.last_error}\033[0m"
            )
            return {}
        data = MetaTrader5.symbol_info(currency_pair)
        if data is None:
            print(f"\033[91mSymbol {currency_pair} not found: {self.last_error}\033[0m")
            return {}
        return {
            "tick_value": data.trade_tick_value,
            "spread": data.spread,
            "bid": data.bid,
            "ask": data.ask,
            "point": data.point,
            "front": data.currency_base,
            "end": data.currency_profit,
            "digits": data.digits,
            "max_lot_size": data.volume_max,
        }

    def get_timeframe(self, minutes: int) -> int:
        """Convert minutes to MetaTrader 5 timeframe constant"""
        _map = {
            1: MetaTrader5.TIMEFRAME_M1,
            5: MetaTrader5.TIMEFRAME_M5,
            15: MetaTrader5.TIMEFRAME_M15,
            30: MetaTrader5.TIMEFRAME_M30,
            60: MetaTrader5.TIMEFRAME_H1,
            240: MetaTrader5.TIMEFRAME_H4,
            1440: MetaTrader5.TIMEFRAME_D1,
            10080: MetaTrader5.TIMEFRAME_W1,
            43200: MetaTrader5.TIMEFRAME_MN1,
        }
        return _map.get(minutes, MetaTrader5.TIMEFRAME_MN1)

    @_require_connection
    def iClose(self, symbol: str, timeframe: int, shift: int) -> float:
        """Get the closing price of a specific bar based on the symbol, timeframe, and shift parameters"""
        _bars = self.get_recent_bars(symbol, timeframe, 1, shift)
        if _bars:
            return _bars[0]["close"]
        print(
            f"\033[91mNo bars returned for iClose with symbol={symbol}, timeframe={timeframe}, shift={shift}\033[0m"
        )
        return 0.0

    @_require_connection
    def iDate(self, symbol: str, timeframe: int, shift: int) -> str:
        """Get the date of a specific bar based on the symbol, timeframe, and shift parameters"""
        _bars = self.get_recent_bars(symbol, timeframe, 1, shift)
        if _bars:
            return _bars[0]["time"]
        print(
            f"\033[91mNo bars returned for iDate with symbol={symbol}, timeframe={timeframe}, shift={shift}\033[0m"
        )
        return ""

    @_require_connection
    def iHigh(self, symbol: str, timeframe: int, shift: int) -> float:
        """Get the high price of a specific bar based on the symbol, timeframe, and shift parameters"""
        _bars = self.get_recent_bars(symbol, timeframe, 1, shift)
        if _bars:
            return _bars[0]["high"]
        print(
            f"\033[91mNo bars returned for iHigh with symbol={symbol}, timeframe={timeframe}, shift={shift}\033[0m"
        )
        return 0.0

    @_require_connection
    def iLow(self, symbol: str, timeframe: int, shift: int) -> float:
        """Get the low price of a specific bar based on the symbol, timeframe, and shift parameters"""
        _bars = self.get_recent_bars(symbol, timeframe, 1, shift)
        if _bars:
            return _bars[0]["low"]
        print(
            f"\033[91mNo bars returned for iLow with symbol={symbol}, timeframe={timeframe}, shift={shift}\033[0m"
        )
        return 0.0

    @_require_connection
    def iOpen(self, symbol: str, timeframe: int, shift: int) -> float:
        """Get the open price of a specific bar based on the symbol, timeframe, and shift parameters"""
        _bars = self.get_recent_bars(symbol, timeframe, 1, shift)
        if _bars:
            return _bars[0]["open"]
        print(
            f"\033[91mNo bars returned for iOpen with symbol={symbol}, timeframe={timeframe}, shift={shift}\033[0m"
        )
        return 0.0

    @_require_connection
    def is_order_opened(self, symbol: str = None, magic_number: int = None):
        """Check if there are any pending orders for a given symbol and magic number"""
        _list = MetaTrader5.orders_get()
        if _list is None:
            return False
        if symbol is None and magic_number is None:
            return len(_list) > 0
        for order in _list:
            if (symbol is None or order.symbol == symbol) and (
                magic_number is None or order.magic == magic_number
            ):
                return True
        return False

    @_require_connection
    def is_position_opened(self, symbol: str = None, magic_number: int = None):
        """Check if there are any open positions for a given symbol and magic number"""
        _list = MetaTrader5.positions_get()
        if _list is None:
            return False
        if symbol is None and magic_number is None:
            return len(_list) > 0
        for position in _list:
            if (symbol is None or position.symbol == symbol) and (
                magic_number is None or position.magic == magic_number
            ):
                return True
        return False

    def login(self) -> bool:
        """Login to MetaTrader 5 using provided account credentials"""
        try:
            return MetaTrader5.initialize(
                login=self._account_number,
                password=self._account_password,
                server=self._broker_server_name,
            )
        except (RuntimeError, TypeError, ValueError, OSError) as e:
            print(f"\033[91mFailed to initialize MetaTrader 5: {e}\033[0m")
            return False

    def open(self) -> bool:
        """Establish MetaTrader 5 connection without credentials"""
        try:
            return MetaTrader5.initialize()
        except (RuntimeError, TypeError, ValueError, OSError) as e:
            print(f"\033[91mFailed to initialize MetaTrader 5: {e}\033[0m")
            return False

    @_require_connection
    def order_delete(self, ticket: int) -> bool:
        """
        Delete a pending order by ticket number.

        Returns True if the order was accepted by the server (retcode 10009), False otherwise.
        """
        _order = self.get_order(ticket)
        if _order is None:
            print(f"\033[91mCannot delete order: ticket {ticket} not found\033[0m")
            return False
        request = {"order": ticket, "action": MetaTrader5.TRADE_ACTION_REMOVE}
        result = MetaTrader5.order_send(request)
        if result is None:
            print(
                f"\033[91mFailed to delete order: ticket {ticket}, no result returned\033[0m"
            )
            return False
        if result.retcode != MetaTrader5.TRADE_RETCODE_DONE:
            print(
                f"\033[91mFailed to delete order: ticket {ticket}, retcode={result.retcode}, comment={result.comment}\033[0m"
            )
            return False
        return True

    @_require_connection
    def order_send(
        self,
        symbol: str,
        order_type: str,
        lot: float,
        order_price: int = 0,
        slippage: int = 10,
        stop_loss: float = 0,
        take_profit: float = 0,
        order_comment: str = "",
        magic_number: int = 0,
    ) -> bool:
        """
        Send an order using absolute entry, stop-loss, and take-profit prices.

        Args:
            symbol:        Instrument symbol, e.g. "EURUSD".
            order_type:    One of "buy", "sell", "buy limit", "buy stop",
                           "sell limit", "sell stop" (case-insensitive).
            lot:           Lot size.
            order_price:   Price at which to fill the order. If 0, fills at the current market price.
            slippage:      Maximum allowed price deviation in points. Default is 10.
            stop_loss:     Absolute SL price. Pass 0 for no stop loss.
            take_profit:   Absolute TP price. Pass 0 for no take profit.
            order_comment: Free-text comment attached to the order.
            magic_number:  Expert Advisor identifier.
        """
        entry_price = order_price
        if entry_price == 0:
            entry_price = self.__get_order_entry_price(symbol, order_type)
        if entry_price is None:
            print(
                f"\033[91mFailed to determine entry price for {symbol} with order_price={order_price}: {self.last_error}\033[0m"
            )
            return False

        return self.__submit_order(
            method_name="order_send",
            symbol=symbol,
            order_type=order_type,
            lot=lot,
            entry_price=entry_price,
            slippage=slippage,
            stop_loss=stop_loss,
            take_profit=take_profit,
            order_comment=order_comment,
            magic_number=magic_number,
        )

    @_require_connection
    def order_send_pips(
        self,
        symbol: str,
        order_type: str,
        lot: float,
        order_price: float = 0,
        slippage: int = 10,
        stop_loss_pips: float = 0,
        take_profit_pips: float = 0,
        order_comment: str = "",
        magic_number: int = 0,
    ) -> bool:
        """
        Send an order using SL/TP distances expressed in pips.

        Args:
            symbol:           Instrument symbol, e.g. "EURUSD".
            order_type:       One of "buy", "sell", "buy limit", "buy stop",
                              "sell limit", "sell stop" (case-insensitive).
            lot:              Lot size.
            order_price:      Price at which to fill the order. If 0, fills at the current market price.
            slippage:         Maximum allowed price deviation in points. Default is 10.
            stop_loss_pips:   SL distance in pips from entry. Pass 0 for no stop loss.
            take_profit_pips: TP distance in pips from entry. Pass 0 for no take profit.
            order_comment:    Free-text comment attached to the order.
            magic_number:     Expert Advisor identifier.
        """
        entry_price = order_price
        if entry_price == 0:
            entry_price = self.__get_order_entry_price(symbol, order_type)
        if entry_price is None:
            print(
                f"\033[91mFailed to determine entry price for {symbol} with order_price={order_price}: {self.last_error}\033[0m"
            )
            return False

        ot = order_type.lower()
        buy_types = {"buy", "buy limit", "buy stop"}
        sell_types = {"sell", "sell limit", "sell stop"}
        pip_value = self.get_pip_value(symbol)

        if ot in buy_types:
            stop_loss = (
                (entry_price - stop_loss_pips * pip_value) if stop_loss_pips != 0 else 0
            )
            take_profit = (
                (entry_price + take_profit_pips * pip_value)
                if take_profit_pips != 0
                else 0
            )
        elif ot in sell_types:
            stop_loss = (
                (entry_price + stop_loss_pips * pip_value) if stop_loss_pips != 0 else 0
            )
            take_profit = (
                (entry_price - take_profit_pips * pip_value)
                if take_profit_pips != 0
                else 0
            )
        else:
            print(
                f"\033[91morder_send_pips: unrecognised order_type '{order_type}'\033[0m"
            )
            return False

        if not self.__validate_sl_tp(ot, entry_price, stop_loss, take_profit):
            return False

        return self.__submit_order(
            method_name="order_send_pips",
            symbol=symbol,
            order_type=order_type,
            lot=lot,
            entry_price=entry_price,
            slippage=slippage,
            stop_loss=stop_loss,
            take_profit=take_profit,
            order_comment=order_comment,
            magic_number=magic_number,
        )

    @_require_connection
    def order_modify(
        self,
        ticket: int,
        price: float,
        stop_loss: float,
        take_profit: float,
    ) -> bool:
        """
        Modify an existing pending order in MetaTrader 5.

        Returns True if the modification was accepted (retcode 10009), False otherwise.
        """
        order_info = self.get_order(ticket)
        if order_info is None:
            print(
                f"\033[91mOrder with ticket {ticket} not found: {self.last_error}\033[0m"
            )
            return False

        filling_mode = self.__get_filling_mode(order_info.symbol, is_pending=True)
        request = {
            "action": MetaTrader5.TRADE_ACTION_MODIFY,
            "order": ticket,
            "symbol": order_info.symbol,
            "volume": order_info.volume_current,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "type_time": MetaTrader5.ORDER_TIME_GTC,
        }
        if filling_mode is not None:
            request["type_filling"] = filling_mode

        result = MetaTrader5.order_send(request)
        if result is None:
            print(
                f"\033[91morder_modify failed, no result returned: {self.last_error}\033[0m"
            )
            return False
        if result.retcode != MetaTrader5.TRADE_RETCODE_DONE:
            print(
                f"\033[91morder_modify failed, retcode={result.retcode}, comment={result.comment}\033[0m"
            )
            return False
        return True

    @_require_connection
    def position_close(self, ticket: int) -> bool:
        """
        Close an open position by ticket number.

        Returns True if the position was closed successfully, False otherwise.
        """
        _position = self.get_position(ticket)
        if _position is None:
            print(
                f"\033[91mPosition with ticket {ticket} not found: {self.last_error}\033[0m"
            )
            return False

        order_type = _position.type
        symbol = _position.symbol
        lot_size = _position.volume

        if order_type == MetaTrader5.ORDER_TYPE_BUY:
            close_price = MetaTrader5.symbol_info_tick(symbol).bid
            new_order_type = MetaTrader5.ORDER_TYPE_SELL
        elif order_type == MetaTrader5.ORDER_TYPE_SELL:
            close_price = MetaTrader5.symbol_info_tick(symbol).ask
            new_order_type = MetaTrader5.ORDER_TYPE_BUY
        else:
            print(
                f"\033[91mUnrecognised position type {order_type} for ticket {ticket}\033[0m"
            )
            return False

        filling_mode = self.__get_filling_mode(symbol, is_pending=False)
        request = {
            "action": MetaTrader5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": new_order_type,
            "position": ticket,
            "price": close_price,
            "deviation": 10,
            "type_time": MetaTrader5.ORDER_TIME_GTC,
        }
        if filling_mode is not None:
            request["type_filling"] = filling_mode

        result = MetaTrader5.order_send(request)
        if result is None:
            print(
                f"\033[91morder_close failed, no result returned: {self.last_error}\033[0m"
            )
            return False
        if result.retcode != MetaTrader5.TRADE_RETCODE_DONE:
            print(
                f"\033[91morder_close failed, retcode={result.retcode}, comment={result.comment}\033[0m"
            )
            return False
        return True

    @_require_connection
    def position_modify(
        self,
        symbol: str,
        ticket: int,
        stop_loss: float,
        take_profit: float,
    ) -> bool:
        """
        Modify the Stop Loss and/or Take Profit of an open position.

        Returns True if the modification was accepted (retcode 10009), False otherwise.
        """
        result = MetaTrader5.order_send(
            {
                "action": MetaTrader5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "sl": stop_loss,
                "tp": take_profit,
                "position": ticket,
            }
        )
        if result is None:
            print(
                f"\033[91mposition_modify failed, no result returned: {self.last_error}\033[0m"
            )
            return False
        if result.retcode != MetaTrader5.TRADE_RETCODE_DONE:
            print(
                f"\033[91mposition_modify failed, retcode={result.retcode}, comment={result.comment}\033[0m"
            )
            return False
        return True

    @_require_connection
    def select_symbol(self, symbol: str, enable: bool = True) -> bool:
        """
        Ensure the specified symbol is enabled/disabled in the Market Watch.

        Returns True if the symbol is successfully enabled/disabled, False otherwise.
        """
        if not MetaTrader5.symbol_select(symbol, enable):
            print(f"\033[91mFailed to select symbol {symbol}: {self.last_error}\033[0m")
            return False
        return True


TIMEFRAME_MESSAGE = "Timeframe can be 1 for 1-Minute, 5 for 5-Minute, 15 for 15-Minute, 30 for 30-Minute, 16385 for Hourly, 16388 for 4-Hour, 16408 for Daily, 32769 for Weekly, and 49153 for Monthly."

TOOL_CLOSE = Tool(
    name="close",
    description="Close the active MetaTrader 5 connection.",
    parameters=Parameters(properties=[]),
)

TOOL_GET_ACCOUNT_INFO = Tool(
    name="get_account_info",
    description="Get account information as a dictionary. Returns account number, name, balance, equity, margin, free margin, margin level, currency, company, and profit.",
    parameters=Parameters(properties=[]),
)

TOOL_GET_HISTORY_POSITION = Tool(
    name="get_history_position",
    description="Get all deals related to the ticket number of a closed position. Unlike get_order and get_position, this method returns a list of all deals associated with the ticket, which can include order modifications, partial closes, the initial opening deal, and the closing deal.",
    parameters=Parameters(
        properties=[
            Property(
                name="ticket",
                type="integer",
                description="Ticket number of the closed position.",
                required=True,
            )
        ]
    ),
)

TOOL_GET_HISTORY_POSITIONS = Tool(
    name="get_history_positions",
    description="Get historical positions, optionally filtered by symbol, magic number, and date range. Returns a list of dictionaries with ticket, time (ISO 8601 UTC), type, volume, magic number, lot size, price, commission, swap, profit, fee, symbol, and comment for each deal.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Optional symbol filter, e.g. EURUSD.",
            ),
            Property(
                name="magic",
                type="integer",
                description="Optional magic number filter for Expert Advisors.",
            ),
            Property(
                name="from_date",
                type="string",
                description="Optional start date filter in ISO 8601 format, e.g. 2023-01-01T00:00:00Z. Defaults to January 1st of the current year if not provided.",
            ),
            Property(
                name="to_date",
                type="string",
                description="Optional end date filter in ISO 8601 format, e.g. 2023-12-31T23:59:59Z. Defaults to the current date and time if not provided.",
            ),
        ]
    ),
)

TOOL_GET_ORDER = Tool(
    name="get_order",
    description="Get a specific pending order by ticket number.",
    parameters=Parameters(
        properties=[
            Property(
                name="ticket",
                type="integer",
                description="Order ticket number.",
                required=True,
            )
        ]
    ),
)

TOOL_GET_ORDERS = Tool(
    name="get_orders",
    description="Get pending orders, optionally filtered by symbol.",
    parameters=Parameters(
        properties=[
            Property(
                name="currency_pair",
                type="string",
                description="Optional symbol filter, e.g. EURUSD.",
            )
        ]
    ),
)

TOOL_GET_PIP_VALUE = Tool(
    name="get_pip_value",
    description="Get the pip value for a symbol based on its precision and asset class.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            )
        ]
    ),
)

TOOL_GET_POSITION = Tool(
    name="get_position",
    description="Get a specific open position by ticket number.",
    parameters=Parameters(
        properties=[
            Property(
                name="ticket",
                type="integer",
                description="Position ticket number.",
                required=True,
            )
        ]
    ),
)

TOOL_GET_POSITIONS = Tool(
    name="get_positions",
    description="Get open positions, optionally filtered by symbol.",
    parameters=Parameters(
        properties=[
            Property(
                name="currency_pair",
                type="string",
                description="Optional symbol filter, e.g. EURUSD.",
            )
        ]
    ),
)

TOOL_GET_RECENT_BARS = Tool(
    name="get_recent_bars",
    description="Get recent bars for a given symbol, timeframe, and shift. Returns a list of dictionaries with time, open, high, low, close, tick_volume, spread, and real_volume for each bar.",
    parameters=Parameters(
        properties=[
            Property(
                name="currency",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="timeframe",
                type="integer",
                description="MetaTrader 5 timeframe constant. " + TIMEFRAME_MESSAGE,
                required=True,
            ),
            Property(
                name="number_of_bars",
                type="integer",
                description="Number of bars to retrieve starting from the shift.",
                required=True,
            ),
            Property(
                name="shift",
                type="integer",
                description="Bar shift, where 0 is the current bar.",
                required=False,
            ),
        ]
    ),
)

TOOL_GET_RISK = Tool(
    name="get_risk",
    description="Calculate lot size based on account risk settings and stop loss. Should only be used if needed to calculate risk-based lot size and an explicit lot size is not being provided",
    parameters=Parameters(
        properties=[
            Property(
                name="use_risk",
                type="boolean",
                description="Use percentage risk-based lot sizing.",
                required=True,
            ),
            Property(
                name="use_lot_size",
                type="boolean",
                description="Use explicit lot size instead of risk-based sizing.",
                required=True,
            ),
            Property(
                name="percent_risk",
                type="number",
                description="Percent of account equity to risk.",
                required=True,
            ),
            Property(
                name="stop_loss",
                type="number",
                description="Stop loss distance in pips.",
                required=True,
            ),
            Property(
                name="lot_size",
                type="number",
                description="Manual lot size value.",
                required=True,
            ),
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
        ]
    ),
)

TOOL_GET_SYMBOL_INFO = Tool(
    name="get_symbol_info",
    description="Get symbol information for a currency pair or instrument. Returns a dictionary with symbol, name, description, base currency, quote currency, digits, trade mode, and other relevant information.",
    parameters=Parameters(
        properties=[
            Property(
                name="currency_pair",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            )
        ]
    ),
)

TOOL_ICLOSE = Tool(
    name="iClose",
    description="Get the close price of a specific historical bar.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="timeframe",
                type="integer",
                description="MetaTrader 5 timeframe constant. " + TIMEFRAME_MESSAGE,
                required=True,
            ),
            Property(
                name="shift",
                type="integer",
                description="Bar shift, where 0 is the current bar.",
                required=True,
            ),
        ]
    ),
)

TOOL_IDATE = Tool(
    name="iDate",
    description="Get the datetime (ISO 8601 UTC) of a specific historical bar.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="timeframe",
                type="integer",
                description="MetaTrader 5 timeframe constant. " + TIMEFRAME_MESSAGE,
                required=True,
            ),
            Property(
                name="shift",
                type="integer",
                description="Bar shift, where 0 is the current bar.",
                required=True,
            ),
        ]
    ),
)

TOOL_IHIGH = Tool(
    name="iHigh",
    description="Get the high price of a specific historical bar.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="timeframe",
                type="integer",
                description="MetaTrader 5 timeframe constant. " + TIMEFRAME_MESSAGE,
                required=True,
            ),
            Property(
                name="shift",
                type="integer",
                description="Bar shift, where 0 is the current bar.",
                required=True,
            ),
        ]
    ),
)

TOOL_ILOW = Tool(
    name="iLow",
    description="Get the low price of a specific historical bar.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="timeframe",
                type="integer",
                description="MetaTrader 5 timeframe constant. " + TIMEFRAME_MESSAGE,
                required=True,
            ),
            Property(
                name="shift",
                type="integer",
                description="Bar shift, where 0 is the current bar.",
                required=True,
            ),
        ]
    ),
)

TOOL_IOPEN = Tool(
    name="iOpen",
    description="Get the open price of a specific historical bar.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="timeframe",
                type="integer",
                description="MetaTrader 5 timeframe constant. " + TIMEFRAME_MESSAGE,
                required=True,
            ),
            Property(
                name="shift",
                type="integer",
                description="Bar shift, where 0 is the current bar.",
                required=True,
            ),
        ]
    ),
)

TOOL_IS_ORDER_OPENED = Tool(
    name="is_order_opened",
    description="Check whether any pending orders match optional symbol and magic filters.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Optional symbol filter, e.g. EURUSD.",
            ),
            Property(
                name="magic_number",
                type="integer",
                description="Optional magic number filter.",
            ),
        ]
    ),
)

TOOL_IS_POSITION_OPENED = Tool(
    name="is_position_opened",
    description="Check whether any open positions match optional symbol and magic filters.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Optional symbol filter, e.g. EURUSD.",
            ),
            Property(
                name="magic_number",
                type="integer",
                description="Optional magic number filter.",
            ),
        ]
    ),
)

TOOL_LOGIN = Tool(
    name="login",
    description="Connect to MetaTrader 5 using configured account credentials.",
    parameters=Parameters(properties=[]),
)

TOOL_OPEN = Tool(
    name="open",
    description="Initialize MetaTrader 5 terminal connection without credentials.",
    parameters=Parameters(properties=[]),
)

TOOL_ORDER_DELETE = Tool(
    name="order_delete",
    description="Delete a pending order by ticket.",
    parameters=Parameters(
        properties=[
            Property(
                name="ticket",
                type="integer",
                description="Pending order ticket number to delete.",
                required=True,
            ),
        ]
    ),
)

TOOL_ORDER_SEND = Tool(
    name="order_send",
    description="Send an order using absolute stop-loss and take-profit prices.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="order_type",
                type="string",
                description="Order type: buy, sell, buy limit, buy stop, sell limit, or sell stop.",
                required=True,
            ),
            Property(
                name="lot",
                type="number",
                description="Lot size.",
                required=True,
            ),
            Property(
                name="order_price",
                type="number",
                description="Entry price for the order. If 0, fills at the current market price. Default is 0.",
                required=False,
            ),
            Property(
                name="slippage",
                type="integer",
                description="Maximum allowed price deviation in points. Default is 10.",
                required=False,
            ),
            Property(
                name="stop_loss",
                type="number",
                description="Absolute stop-loss price, or 0 to set no stop-loss. Default is 0.",
                required=False,
            ),
            Property(
                name="take_profit",
                type="number",
                description="Absolute take-profit price, or 0 to set no take-profit. Default is 0.",
                required=False,
            ),
            Property(
                name="order_comment",
                type="string",
                description="Comment attached to the order. Default is an empty string.",
                required=False,
            ),
            Property(
                name="magic_number",
                type="integer",
                description="Expert Advisor identifier. Default is 0.",
                required=False,
            ),
        ]
    ),
)

TOOL_ORDER_SEND_PIPS = Tool(
    name="order_send_pips",
    description="Send an order using stop-loss and take-profit distances in pips.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="order_type",
                type="string",
                description="Order type: buy, sell, buy limit, buy stop, sell limit, or sell stop.",
                required=True,
            ),
            Property(
                name="lot",
                type="number",
                description="Lot size.",
                required=True,
            ),
            Property(
                name="order_price",
                type="number",
                description="Price at which to fill the order. If 0, fills at the current market price. Default is 0.",
                required=False,
            ),
            Property(
                name="slippage",
                type="integer",
                description="Maximum allowed price deviation in points. Default is 10.",
                required=False,
            ),
            Property(
                name="stop_loss_pips",
                type="number",
                description="Stop-loss distance in pips, or 0. Default is 0.",
                required=False,
            ),
            Property(
                name="take_profit_pips",
                type="number",
                description="Take-profit distance in pips, or 0. Default is 0.",
                required=False,
            ),
            Property(
                name="order_comment",
                type="string",
                description="Comment attached to the order. Default is an empty string.",
                required=False,
            ),
            Property(
                name="magic_number",
                type="integer",
                description="Expert Advisor identifier. Default is 0.",
                required=False,
            ),
        ]
    ),
)

TOOL_ORDER_MODIFY = Tool(
    name="order_modify",
    description="Modify an existing pending order.",
    parameters=Parameters(
        properties=[
            Property(
                name="ticket",
                type="integer",
                description="Pending order ticket number.",
                required=True,
            ),
            Property(
                name="price",
                type="number",
                description="New order price.",
                required=True,
            ),
            Property(
                name="stop_loss",
                type="number",
                description="New stop-loss price.",
                required=True,
            ),
            Property(
                name="take_profit",
                type="number",
                description="New take-profit price.",
                required=True,
            ),
        ]
    ),
)

TOOL_POSITION_CLOSE = Tool(
    name="position_close",
    description="Close an open position by ticket number.",
    parameters=Parameters(
        properties=[
            Property(
                name="ticket",
                type="integer",
                description="Open position ticket number to close.",
                required=True,
            )
        ]
    ),
)

TOOL_POSITION_MODIFY = Tool(
    name="position_modify",
    description="Modify stop-loss and take-profit for an open position.",
    parameters=Parameters(
        properties=[
            Property(
                name="symbol",
                type="string",
                description="Instrument symbol, e.g. EURUSD.",
                required=True,
            ),
            Property(
                name="ticket",
                type="integer",
                description="Open position ticket number.",
                required=True,
            ),
            Property(
                name="stop_loss",
                type="number",
                description="New stop-loss price.",
                required=True,
            ),
            Property(
                name="take_profit",
                type="number",
                description="New take-profit price.",
                required=True,
            ),
        ]
    ),
)
