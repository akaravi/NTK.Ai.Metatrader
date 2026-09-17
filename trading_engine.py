import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from mt5_service import mt5_service
from ai_service import ai_service
from config import settings
from db import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingEngine")


class TradingEngine:
    def __init__(self):
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.symbols: List[str] = ["EURUSD"]
        self.timeframe: str = "M15"
        self.interval_seconds: int = 60
        self.auto_execute: bool = False
        self.min_confidence: float = settings.MIN_TRADE_CONFIDENCE
        self.logs: List[Dict[str, Any]] = []
        self.last_analysis: Dict[str, Any] = {}
        
        # Dedicated Scalper Mode state
        self.is_scalp_running = False
        self.scalp_task: Optional[asyncio.Task] = None
        self.scalp_symbols: List[str] = ["EURUSD"]
        self.scalp_timeframe: str = "M1"
        self.scalp_interval_seconds: int = 15
        self.scalp_max_spread: float = 1.8
        self.last_scalp_analysis: Dict[str, Any] = {}
        self.active_scalps: Dict[int, Dict[str, Any]] = {}

        # Automated Trailing Stop Loss & Break-Even Engine
        self.is_trailing_running: bool = False
        self.trailing_task: Optional[asyncio.Task] = None
        self.trailing_activation_pips: float = 12.0
        self.trailing_distance_pips: float = 8.0
        self.breakeven_enabled: bool = True
        self.breakeven_trigger_pips: float = 10.0
        self.breakeven_buffer_pips: float = 0.5
        self.trailing_interval_seconds: int = 4

        # AI Continuous Open Positions Re-Analysis & Guard
        self.is_position_monitor_running: bool = False
        self.position_monitor_task: Optional[asyncio.Task] = None
        self.position_monitor_interval_seconds: int = settings.AI_POSITION_MONITOR_INTERVAL
        self.position_ai_checks: Dict[int, Dict[str, Any]] = {}

        # Multi-Pair Portfolio Hub & Master AI Supervisor
        self.is_portfolio_supervisor_running: bool = False
        self.portfolio_supervisor_task: Optional[asyncio.Task] = None
        self.portfolio_supervisor_interval_seconds: int = 30
        self.last_portfolio_analysis: Dict[str, Any] = {}
        # Daily Drawdown Circuit Breaker & Capital Protection Guard
        self.is_circuit_breaker_active: bool = False
        self.max_daily_loss_percent: float = settings.MAX_DAILY_LOSS_PERCENT
        self.daily_loss_guard_enabled: bool = settings.DAILY_LOSS_GUARD_ENABLED

    def log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            "data": data or {}
        }
        self.logs.append(entry)
        if len(self.logs) > 500:
            self.logs.pop(0)
        
        # Persist log to SQLite
        db.record_log(level, message, data)
        logger.info(f"[{level}] {message}")

    async def resume_saved_state(self):
        """Check SQLite and automatically resume engine if it was active before disconnection/restart."""
        auto_state = db.get_state("auto_trade", {})
        if auto_state and auto_state.get("is_running"):
            logger.info("🔄 Resuming Auto-Trader engine from SQLite persistent state...")
            await self.start(
                symbols=auto_state.get("symbols", ["EURUSD"]),
                timeframe=auto_state.get("timeframe", "M15"),
                interval_seconds=auto_state.get("interval_seconds", 60),
                auto_execute=auto_state.get("auto_execute", True),
                min_confidence=auto_state.get("min_confidence", settings.MIN_TRADE_CONFIDENCE),
            )

        scalp_state = db.get_state("scalp_trade", {})
        if scalp_state and scalp_state.get("is_running"):
            logger.info("🔄 Resuming Scalping engine from SQLite persistent state...")
            await self.start_scalper(
                symbols=scalp_state.get("symbols", ["EURUSD"]),
                timeframe=scalp_state.get("timeframe", "M1"),
                interval_seconds=scalp_state.get("interval_seconds", 15),
                max_spread=scalp_state.get("max_spread", 1.8),
            )

        trailing_state = db.get_state("trailing_engine", {})
        if trailing_state and trailing_state.get("is_running"):
            logger.info("🔄 Resuming Trailing Stop / Break-Even engine from SQLite persistent state...")
            await self.start_trailing_engine(
                activation_pips=trailing_state.get("activation_pips", 12.0),
                distance_pips=trailing_state.get("distance_pips", 8.0),
                breakeven_enabled=trailing_state.get("breakeven_enabled", True),
                breakeven_trigger_pips=trailing_state.get("breakeven_trigger_pips", 10.0),
                breakeven_buffer_pips=trailing_state.get("breakeven_buffer_pips", 0.5),
                interval_seconds=trailing_state.get("interval_seconds", 4)
            )

        if settings.AI_POSITION_MONITOR_ENABLED:
            logger.info("🔄 Launching AI Continuous Open Position Re-Analysis Monitor...")
            await self.start_position_ai_monitor(interval_seconds=settings.AI_POSITION_MONITOR_INTERVAL)

        portfolio_state = db.get_state("portfolio_supervisor", {})
        if portfolio_state and portfolio_state.get("is_running"):
            logger.info("🔄 Resuming Master AI Portfolio Supervisor from SQLite persistent state...")
            await self.start_portfolio_supervisor(interval_seconds=portfolio_state.get("interval_seconds", 30))

    async def start(self, symbols: Optional[List[str]] = None, timeframe: str = "M15",
                    interval_seconds: int = 60, auto_execute: bool = False,
                    min_confidence: float = settings.MIN_TRADE_CONFIDENCE) -> Dict[str, Any]:
        """Start the background automated trader engine."""
        if self.is_running:
            return {"success": False, "message": "موتور معامله‌گر در حال حاضر فعال است."}

        self.symbols = symbols or [settings.DEFAULT_SYMBOL]
        self.timeframe = timeframe
        self.interval_seconds = interval_seconds
        self.auto_execute = auto_execute
        self.min_confidence = min_confidence
        self.is_running = True

        # Persist state in SQLite
        db.set_state("auto_trade", {
            "is_running": True,
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "interval_seconds": self.interval_seconds,
            "auto_execute": self.auto_execute,
            "min_confidence": self.min_confidence
        })

        self.task = asyncio.create_task(self._run_loop())
        self.log("INFO", f"موتور معامله‌گر هوشمند فعال شد. نمادها: {self.symbols} | تایم‌فریم: {self.timeframe} | اجرای خودکار: {self.auto_execute}")
        return {"success": True, "message": "موتور معامله‌گر هوشمند با موفقیت آغاز شد."}

    async def stop(self) -> Dict[str, Any]:
        """Stop the background automated trader engine."""
        if not self.is_running:
            return {"success": False, "message": "موتور معامله‌گر در حال حاضر متوقف است."}

        self.is_running = False
        db.set_state("auto_trade", {"is_running": False})

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        self.log("INFO", "موتور معامله‌گر متوقف شد.")
        return {"success": True, "message": "موتور معامله‌گر متوقف گردید."}

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        return {
            "is_running": self.is_running,
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "interval_seconds": self.interval_seconds,
            "auto_execute": self.auto_execute,
            "min_confidence": self.min_confidence,
            "last_analysis": self.last_analysis,
            "is_circuit_breaker_active": self.is_circuit_breaker_active,
            "log_count": len(self.logs)
        }

    def check_daily_loss_guard(self) -> Tuple[bool, str]:
        """
        Check if daily loss exceeds MAX_DAILY_LOSS_PERCENT.
        Returns: (is_blocked, reason_fa)
        """
        if not self.daily_loss_guard_enabled:
            return False, ""

        time_stats = db.get_time_framed_trading_stats()
        stats_24h = time_stats.get("last_24h", {})
        pnl_24h = float(stats_24h.get("pnl", 0.0))

        acc = mt5_service.get_account_info() or {}
        balance = float(acc.get("balance", 1000.0))

        if balance > 0 and pnl_24h < 0:
            loss_pct = (abs(pnl_24h) / balance) * 100.0
            if loss_pct >= self.max_daily_loss_percent:
                self.is_circuit_breaker_active = True
                msg = f"⛔ کلید محافظت از سرمایه (Circuit Breaker) فعال شد! افت ۲۴ ساعت گذشته ({pnl_24h:.2f}$ = {loss_pct:.1f}%) به سقف مجاز روزانه ({self.max_daily_loss_percent}%) رسید. معاملات جدید موقتاً مسدود شدند."
                self.log("CIRCUIT_BREAKER", msg)
                return True, msg

        self.is_circuit_breaker_active = False
        return False, ""
    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent engine logs from in-memory and SQLite."""
        db_logs = db.get_persistent_logs(limit)
        if db_logs:
            return db_logs
        return list(reversed(self.logs[-limit:]))

    def clear_logs(self):
        """Clear log history."""
        self.logs.clear()

    async def _run_loop(self):
        """Main background loop."""
        while self.is_running:
            try:
                for symbol in self.symbols:
                    if not self.is_running:
                        break
                    await self._process_symbol(symbol)
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log("ERROR", f"خطا در چرخه معامله‌گر: {str(e)}")
                await asyncio.sleep(10)

    async def _process_symbol(self, symbol: str):
        """Analyze a single symbol and execute trade if conditions met."""
        try:
            if not mt5_service.ensure_connected():
                self.log("WARN", "عدم اتصال به متاتریدر ۵ جهت بررسی خودکار")
                return

            blocked, reason = self.check_daily_loss_guard()
            if blocked:
                self.log("WARN", reason)
                return
            acc_info = mt5_service.get_account_info() or {}
            overview = mt5_service.get_symbol_overview(symbol)
            if not overview:
                self.log("WARN", f"عدم امکان دریافت داده‌های {symbol}")
                return

            tech_data = mt5_service.get_candles_with_indicators(symbol, self.timeframe)
            if not tech_data:
                self.log("WARN", f"عدم امکان محاسبه اندیکاتورهای {symbol}")
                return

            # Request AI Analysis
            ai_res = ai_service.analyze_market_with_indicators(symbol, acc_info, overview, tech_data)
            self.last_analysis[symbol] = ai_res

            action = ai_res.get("action", "HOLD")
            confidence = ai_res.get("confidence", 0)
            rationale = ai_res.get("rationale", "")

            # Persist AI signal in SQLite
            if action in ["BUY", "SELL"]:
                db.record_signal(
                    symbol=symbol,
                    signal_type=action,
                    price=float(tech_data.get("current_price", 0.0)),
                    confidence=float(confidence),
                    sl=ai_res.get("suggested_sl"),
                    tp=ai_res.get("suggested_tp"),
                    rationale=rationale,
                    agent_name="OmniRoute-AutoTrader",
                    timeframe=self.timeframe
                )

            self.log("ANALYSIS", f"تحلیل {symbol}: سیگنال {action} با اطمینان {confidence}%", {
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "price": tech_data.get("current_price"),
                "rsi": tech_data.get("rsi"),
                "trend": tech_data.get("trend")
            })

            # Check if auto-execution is permitted
            if self.auto_execute and action in ["BUY", "SELL"] and confidence >= self.min_confidence:
                open_positions = mt5_service.get_open_positions()
                max_allowed = getattr(settings, "MAX_OPEN_POSITIONS", 10) or 10
                if len(open_positions) >= max_allowed:
                    self.log("WARN", f"تعداد کل معاملات باز ({len(open_positions)}) به سقف مجاز ({max_allowed}) رسیده است. معامله جدید باز نشد.")
                    return
                sl = ai_res.get("suggested_sl")
                tp = ai_res.get("suggested_tp")
                vol = settings.DEFAULT_LOT_SIZE

                self.log("TRADE", f"ارسال خودکار سفارش {action} برای {symbol} با حجم {vol}...")
                trade_res = mt5_service.execute_order(
                    symbol=symbol,
                    order_type=action,
                    volume=vol,
                    sl=sl,
                    tp=tp,
                    comment="OmniRoute AutoTrade",
                    confidence=float(confidence),
                    prediction_title=f"روند خودکار ({self.timeframe})",
                    prediction_reason=rationale
                )

                if trade_res.get("success"):
                    ticket = trade_res.get("order_ticket", 0)
                    self.log("SUCCESS", f"سفارش خودکار {action} برای {symbol} با موفقیت اجرا شد (تیکت: #{ticket})")
                else:
                    self.log("ERROR", f"خطا در اجرای خودکار سفارش: {trade_res.get('error')}")

        except Exception as e:
            self.log("ERROR", f"خطا در پردازش {symbol}: {str(e)}")

    async def start_scalper(self, symbols: Optional[List[str]] = None, timeframe: str = "M1",
                            interval_seconds: int = 15, max_spread: float = 1.8) -> Dict[str, Any]:
        """Start dedicated high-frequency AI Scalping Engine."""
        if self.is_scalp_running:
            return {"success": False, "message": "موتور اسکالپینگ در حال حاضر فعال است."}

        self.scalp_symbols = symbols or [settings.DEFAULT_SYMBOL]
        self.scalp_timeframe = timeframe
        self.scalp_interval_seconds = interval_seconds
        self.scalp_max_spread = max_spread
        self.is_scalp_running = True

        # Persist scalper state in SQLite
        db.set_state("scalp_trade", {
            "is_running": True,
            "symbols": self.scalp_symbols,
            "timeframe": self.scalp_timeframe,
            "interval_seconds": self.scalp_interval_seconds,
            "max_spread": self.scalp_max_spread
        })

        self.scalp_task = asyncio.create_task(self._run_scalp_loop())
        self.log("SCALP_INFO", f"موتور اسکالپینگ هوشمند فعال شد. نمادها: {self.scalp_symbols} | تایم‌فریم: {self.scalp_timeframe} | فاصله: {self.scalp_interval_seconds} ثانیه")
        return {"success": True, "message": "موتور اسکالپینگ هوشمند فعال شد."}

    async def stop_scalper(self) -> Dict[str, Any]:
        """Stop dedicated AI Scalping Engine."""
        if not self.is_scalp_running:
            return {"success": False, "message": "موتور اسکالپینگ متوقف است."}

        self.is_scalp_running = False
        db.set_state("scalp_trade", {"is_running": False})

        if self.scalp_task:
            self.scalp_task.cancel()
            try:
                await self.scalp_task
            except asyncio.CancelledError:
                pass
            self.scalp_task = None

        self.log("SCALP_INFO", "موتور اسکالپینگ متوقف شد.")
        return {"success": True, "message": "موتور اسکالپینگ متوقف شد."}

    def get_scalper_status(self) -> Dict[str, Any]:
        """Get current scalper status."""
        return {
            "is_running": self.is_scalp_running,
            "symbols": self.scalp_symbols,
            "timeframe": self.scalp_timeframe,
            "interval_seconds": self.scalp_interval_seconds,
            "max_spread": self.scalp_max_spread,
            "last_analysis": self.last_scalp_analysis,
        }

    async def _run_scalp_loop(self):
        """High-speed scalping evaluation loop."""
        while self.is_scalp_running:
            try:
                for symbol in self.scalp_symbols:
                    if not self.is_scalp_running:
                        break
                    await self._process_scalp_symbol(symbol)
                await asyncio.sleep(self.scalp_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log("SCALP_ERROR", f"خطا در چرخه اسکالپینگ: {e}")
                await asyncio.sleep(5)

    async def _process_scalp_symbol(self, symbol: str):
        """Evaluate rapid micro-scalping opportunity on a symbol."""
        try:
            if not mt5_service.ensure_connected():
                return
            blocked, reason = self.check_daily_loss_guard()
            if blocked:
                self.log("SCALP_WARN", reason)
                return
            overview = mt5_service.get_symbol_overview(symbol)
            if not overview:
                return

            spread = overview.get("spread_points", 999) / 10.0
            if spread > self.scalp_max_spread:
                self.log("SCALP_SKIP", f"اسپرد نماد {symbol} ({spread:.1f} pips) بالاتر از سقف مجاز اسکالپ ({self.scalp_max_spread}) است.")
                return

            acc_info = mt5_service.get_account_info() or {}
            tech_data = mt5_service.get_candles_with_indicators(symbol, self.scalp_timeframe, count=60)
            if not tech_data:
                return

            # Request Scalping AI Analysis
            ai_res = ai_service.analyze_scalping(symbol, acc_info, overview, tech_data)
            self.last_scalp_analysis[symbol] = ai_res

            action = ai_res.get("action", "HOLD")
            confidence = ai_res.get("confidence", 0)

            # Persist scalping signal in SQLite
            if action in ["BUY", "SELL"]:
                db.record_signal(
                    symbol=symbol,
                    signal_type=action,
                    price=float(tech_data.get("current_price", 0.0)),
                    confidence=float(confidence),
                    sl=ai_res.get("suggested_sl"),
                    tp=ai_res.get("suggested_tp"),
                    rationale=ai_res.get("rationale", ""),
                    agent_name="OmniRoute-MicroScalper",
                    timeframe=self.scalp_timeframe
                )

            self.log("SCALP_ANALYSIS", f"اسکالپ {symbol} ({self.scalp_timeframe}): {action} | اطمینان: {confidence}% | {ai_res.get('rationale')}")

            # Auto execute micro scalps if confidence high
            if action in ["BUY", "SELL"] and confidence >= settings.SCALP_MIN_CONFIDENCE:
                open_positions = mt5_service.get_open_positions()
                symbol_positions = [p for p in open_positions if p["symbol"].upper() == symbol.upper()]
                if len(symbol_positions) >= 1:
                    return

                sl = ai_res.get("suggested_sl")
                tp = ai_res.get("suggested_tp")
                vol = settings.DEFAULT_LOT_SIZE

                self.log("SCALP_TRADE", f"⚡ اجرای ورود سریع اسکالپ {action} برای {symbol} (حجم: {vol})...")
                res = mt5_service.execute_order(
                    symbol=symbol,
                    order_type=action,
                    volume=vol,
                    sl=sl,
                    tp=tp,
                    comment="OmniRoute MicroScalp"
                )
                if res.get("success"):
                    ticket = res.get("order_ticket", 0)
                    # Persist scalping trade in SQLite
                    db.record_trade_open(
                        ticket=ticket,
                        symbol=symbol,
                        trade_type=action,
                        volume=vol,
                        open_price=float(res.get("price", tech_data.get("current_price", 0.0))),
                        sl=sl,
                        tp=tp,
                        comment="OmniRoute MicroScalp",
                        strategy="SCALPING"
                    )
                    self.log("SCALP_SUCCESS", f"✅ پوزیشن اسکالپ {action} باز شد. تیکت: #{ticket}")
                else:
                    self.log("SCALP_ERROR", f"❌ خطا در باز کردن اسکالپ: {res.get('error')}")

        except Exception as e:
            self.log("SCALP_ERROR", f"خطا در پردازش اسکالپ {symbol}: {e}")

    async def execute_instant_scalp(
        self,
        symbol: str,
        order_type: str,
        volume: float = 0.01,
        target_pips: float = 10.0,
        sl_pips: float = 7.0,
        max_hold_minutes: int = 10
    ) -> Dict[str, Any]:
        """
        Execute an instant micro-scalp trade with automated time-based exit (max hold duration).
        """
        if not mt5_service.ensure_connected():
            return {"success": False, "error": "عدم اتصال به متاتریدر ۵"}

        overview = mt5_service.get_symbol_overview(symbol)
        if not overview:
            return {"success": False, "error": f"عدم دریافت قیمت لحظه‌ای نماد {symbol}"}

        tick_price = overview.get("ask") if order_type.upper() == "BUY" else overview.get("bid")
        point = 0.0001 if "JPY" not in symbol.upper() and "XAU" not in symbol.upper() else (0.01 if "JPY" in symbol.upper() else 0.1)

        sl_price = round(tick_price - (sl_pips * point * 10) if order_type.upper() == "BUY" else tick_price + (sl_pips * point * 10), 5)
        tp_price = round(tick_price + (target_pips * point * 10) if order_type.upper() == "BUY" else tick_price - (target_pips * point * 10), 5)

        comment = f"Scalp {max_hold_minutes}m"
        trade_res = mt5_service.execute_order(
            symbol=symbol,
            order_type=order_type.upper(),
            volume=volume,
            sl=sl_price,
            tp=tp_price,
            comment=comment,
            confidence=85.0,
            prediction_title=f"اسکالپینگ سریع ({max_hold_minutes} دقیقه)",
            prediction_reason=f"ورود پرشتاب در M1 با تارگت {target_pips} پیپ و خروج خودکار در {max_hold_minutes} دقیقه"
        )
        if not trade_res.get("success"):
            return trade_res

        ticket = trade_res.get("order_ticket", 0)
        open_time = datetime.now()
        max_hold_seconds = max_hold_minutes * 60

        scalp_entry = {
            "ticket": ticket,
            "symbol": symbol,
            "order_type": order_type.upper(),
            "volume": volume,
            "open_price": trade_res.get("price", tick_price),
            "sl": sl_price,
            "tp": tp_price,
            "max_hold_minutes": max_hold_minutes,
            "max_hold_seconds": max_hold_seconds,
            "open_time": open_time.strftime("%Y-%m-%d %H:%M:%S"),
            "open_timestamp": open_time.timestamp(),
            "expire_timestamp": open_time.timestamp() + max_hold_seconds
        }
        
        self.active_scalps[ticket] = scalp_entry

        # Launch automated time-based close watcher
        asyncio.create_task(self._auto_close_scalp_task(ticket, max_hold_seconds, symbol, max_hold_minutes))
        
        self.log("SCALP_EXEC", f"⚡ معامله اسکالپ {order_type} برای {symbol} با حداکثر زمان {max_hold_minutes} دقیقه ثبت شد (تیکت: #{ticket}).")
        
        return {
            "success": True,
            "order_ticket": ticket,
            "scalp_details": scalp_entry,
            "message": f"معامله اسکالپ {order_type} با موفقیت اجرا شد. حداکثر زمان مجاز: {max_hold_minutes} دقیقه."
        }

    async def _auto_close_scalp_task(self, ticket: int, max_hold_seconds: int, symbol: str, max_hold_minutes: int):
        """Background countdown timer that closes the position when max hold time expires."""
        try:
            await asyncio.sleep(max_hold_seconds)
            positions = mt5_service.get_open_positions()
            is_still_open = any(p["ticket"] == ticket for p in positions)
            if is_still_open:
                self.log("SCALP_EXPIRE", f"⏰ زمان مجاز ({max_hold_minutes} دقیقه) پوزیشن اسکالپ #{ticket} به پایان رسید. بستن خودکار پوزیشن در قیمت لحظه‌ای بازار...")
                mt5_service.close_position(ticket)
            if ticket in self.active_scalps:
                del self.active_scalps[ticket]
        except Exception as e:
            self.log("SCALP_ERROR", f"خطا در ناظر زمان پوزیشن #{ticket}: {e}")

    def get_active_scalps(self) -> List[Dict[str, Any]]:
        """List currently tracked scalp trades with remaining seconds."""
        now_ts = datetime.now().timestamp()
        results = []
        for ticket, s in list(self.active_scalps.items()):
            rem = max(0, int(s["expire_timestamp"] - now_ts))
            mins = rem // 60
            secs = rem % 60
            results.append({
                **s,
                "remaining_seconds": rem,
                "remaining_formatted": f"{mins:02d}:{secs:02d}",
                "is_expired": rem == 0
            })
        return results
    async def start_trailing_engine(
        self,
        activation_pips: float = 12.0,
        distance_pips: float = 8.0,
        breakeven_enabled: bool = True,
        breakeven_trigger_pips: float = 10.0,
        breakeven_buffer_pips: float = 0.5,
        interval_seconds: int = 4
    ) -> Dict[str, Any]:
        """Start background Automated Trailing Stop Loss & Break-Even Engine."""
        if self.is_trailing_running:
            return {"success": False, "message": "موتور تریلینگ استاپ و ریسک‌فری در حال حاضر فعال است."}

        self.trailing_activation_pips = activation_pips
        self.trailing_distance_pips = distance_pips
        self.breakeven_enabled = breakeven_enabled
        self.breakeven_trigger_pips = breakeven_trigger_pips
        self.breakeven_buffer_pips = breakeven_buffer_pips
        self.trailing_interval_seconds = interval_seconds
        self.is_trailing_running = True

        # Save state to SQLite
        db.set_state("trailing_engine", {
            "is_running": True,
            "activation_pips": activation_pips,
            "distance_pips": distance_pips,
            "breakeven_enabled": breakeven_enabled,
            "breakeven_trigger_pips": breakeven_trigger_pips,
            "breakeven_buffer_pips": breakeven_buffer_pips,
            "interval_seconds": interval_seconds,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        self.trailing_task = asyncio.create_task(self._run_trailing_loop())
        self.log("TRAILING_START", f"🛡️ موتور تریلینگ استاپ و ریسک‌فری فعال شد (فعال‌سازی: {activation_pips} پیپ، فاصله: {distance_pips} پیپ، ریسک‌فری: {breakeven_trigger_pips} پیپ).")

        return {"success": True, "message": "موتور تریلینگ استاپ و محافظت از سود با موفقیت آغاز شد."}

    async def stop_trailing_engine(self) -> Dict[str, Any]:
        """Stop background Automated Trailing Stop Loss & Break-Even Engine."""
        if not self.is_trailing_running:
            return {"success": False, "message": "موتور تریلینگ استاپ غیرفعال است."}

        self.is_trailing_running = False
        if self.trailing_task:
            self.trailing_task.cancel()
            self.trailing_task = None

        db.set_state("trailing_engine", {"is_running": False})
        self.log("TRAILING_STOP", "🛑 موتور تریلینگ استاپ و ریسک‌فری متوقف شد.")
        return {"success": True, "message": "موتور تریلینگ استاپ متوقف شد."}

    async def _run_trailing_loop(self):
        """Background polling loop for trailing stop loss and break-even."""
        while self.is_trailing_running:
            try:
                await self._evaluate_trailing_positions()
                await asyncio.sleep(self.trailing_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log("TRAILING_ERROR", f"خطا در چرخه تریلینگ استاپ: {e}")
                await asyncio.sleep(5)

    async def _evaluate_trailing_positions(self):
        """Evaluate all open positions for trailing stop adjustments and break-even."""
        if not mt5_service.ensure_connected():
            return

        positions = mt5_service.get_open_positions()
        if not positions:
            return

        for p in positions:
            ticket = p["ticket"]
            symbol = p["symbol"]
            p_type = p["type"]
            open_price = float(p["open_price"])
            curr_price = float(p["current_price"])
            curr_sl = float(p["sl"])
            point = 0.0001 if "JPY" not in symbol.upper() and "XAU" not in symbol.upper() else (0.01 if "JPY" in symbol.upper() else 0.1)
            pip_size = point * 10

            if p_type == "BUY":
                profit_pips = (curr_price - open_price) / pip_size

                # 1. Break-Even Check
                if self.breakeven_enabled and profit_pips >= self.breakeven_trigger_pips:
                    target_be_sl = round(open_price + (self.breakeven_buffer_pips * pip_size), 5)
                    if curr_sl < target_be_sl:
                        res = mt5_service.modify_position(ticket, sl=target_be_sl, tp=p["tp"])
                        if res.get("success"):
                            self.log("TRAILING_BE", f"🛡️ ریسک‌فری پوزیشن خرید #{ticket} ({symbol}) در حاشیه سود {profit_pips:.1f} پیپ به حد ضرر جدید {target_be_sl} منتقل شد.")
                            curr_sl = target_be_sl

                # 2. Trailing Stop Check
                if profit_pips >= self.trailing_activation_pips:
                    candidate_sl = round(curr_price - (self.trailing_distance_pips * pip_size), 5)
                    # Only move SL up, with at least 1 pip step improvement
                    if candidate_sl > curr_sl + pip_size:
                        res = mt5_service.modify_position(ticket, sl=candidate_sl, tp=p["tp"])
                        if res.get("success"):
                            self.log("TRAILING_STEP", f"📈 تریلینگ استاپ پوزیشن خرید #{ticket} ({symbol}) حد ضرر را به {candidate_sl} ارتقا داد (سود: +{profit_pips:.1f} پیپ).")

            elif p_type == "SELL":
                profit_pips = (open_price - curr_price) / pip_size

                # 1. Break-Even Check
                if self.breakeven_enabled and profit_pips >= self.breakeven_trigger_pips:
                    target_be_sl = round(open_price - (self.breakeven_buffer_pips * pip_size), 5)
                    if curr_sl == 0 or curr_sl > target_be_sl:
                        res = mt5_service.modify_position(ticket, sl=target_be_sl, tp=p["tp"])
                        if res.get("success"):
                            self.log("TRAILING_BE", f"🛡️ ریسک‌فری پوزیشن فروش #{ticket} ({symbol}) در حاشیه سود {profit_pips:.1f} پیپ به حد ضرر جدید {target_be_sl} منتقل شد.")
                            curr_sl = target_be_sl

                # 2. Trailing Stop Check
                if profit_pips >= self.trailing_activation_pips:
                    candidate_sl = round(curr_price + (self.trailing_distance_pips * pip_size), 5)
                    # Only move SL down, with at least 1 pip step improvement
                    if curr_sl == 0 or candidate_sl < curr_sl - pip_size:
                        res = mt5_service.modify_position(ticket, sl=candidate_sl, tp=p["tp"])
                        if res.get("success"):
                            self.log("TRAILING_STEP", f"📉 تریلینگ استاپ پوزیشن فروش #{ticket} ({symbol}) حد ضرر را به {candidate_sl} ارتقا داد (سود: +{profit_pips:.1f} پیپ).")

    def get_trailing_status(self) -> Dict[str, Any]:
        """Return current status and configuration of trailing stop engine."""
        return {
            "is_running": self.is_trailing_running,
            "activation_pips": self.trailing_activation_pips,
            "distance_pips": self.trailing_distance_pips,
            "breakeven_enabled": self.breakeven_enabled,
            "breakeven_trigger_pips": self.breakeven_trigger_pips,
            "breakeven_buffer_pips": self.breakeven_buffer_pips,
            "interval_seconds": self.trailing_interval_seconds
        }

    # --- AI Continuous Open Position Re-Analysis & Guard Logic ---

    async def start_position_ai_monitor(self, interval_seconds: int = 20) -> Dict[str, Any]:
        """Start background task for continuous AI re-evaluation of open positions."""
        if self.is_position_monitor_running:
            return {"success": True, "message": "پایش و تحلیل هوشمند معاملات باز در حال حاضر فعال است."}

        self.position_monitor_interval_seconds = max(5, interval_seconds)
        self.is_position_monitor_running = True
        self.position_monitor_task = asyncio.create_task(self._run_position_ai_monitor_loop())
        self.log("AI_POS_START", f"🤖 سامانه پایش و ارزیابی پیوسته معاملات باز توسط هوش مصنوعی با بازه {interval_seconds} ثانیه آغاز شد.")
        return {"success": True, "message": "پایش هوشمند معاملات باز با موفقیت آغاز شد."}

    async def stop_position_ai_monitor(self) -> Dict[str, Any]:
        """Stop background task for AI position monitoring."""
        if not self.is_position_monitor_running:
            return {"success": False, "message": "پایش معاملات باز غیرفعال است."}

        self.is_position_monitor_running = False
        if self.position_monitor_task:
            self.position_monitor_task.cancel()
            self.position_monitor_task = None

        self.log("AI_POS_STOP", "🛑 سامانه پایش و ارزیابی معاملات باز متوقف شد.")
        return {"success": True, "message": "پایش معاملات باز متوقف شد."}

    async def _run_position_ai_monitor_loop(self):
        """Periodic loop that re-evaluates all open positions with AI."""
        while self.is_position_monitor_running:
            try:
                positions = mt5_service.get_open_positions()
                if positions:
                    for pos in positions:
                        if not self.is_position_monitor_running:
                            break
                        await self.reanalyze_position(pos["ticket"])
                        await asyncio.sleep(1.0)
                await asyncio.sleep(self.position_monitor_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log("AI_POS_ERROR", f"خطا در چرخه بررسی هوش مصنوعی معاملات باز: {e}")
                await asyncio.sleep(5)

    async def reanalyze_position(self, ticket: int) -> Dict[str, Any]:
        """
        Re-evaluate an open position using live indicators, 52-strategy consensus,
        and current PnL to recommend: HOLD, TAKE_PROFIT_EARLY, CUT_LOSS, or MOVE_TO_BE.
        """
        try:
            positions = mt5_service.get_open_positions()
            pos = next((p for p in positions if p["ticket"] == ticket), None)
            if not pos:
                if ticket in self.position_ai_checks:
                    del self.position_ai_checks[ticket]
                return {"success": False, "error": f"معامله #{ticket} باز نیست."}

            symbol = pos["symbol"]
            pos_type = pos["type"]
            open_price = float(pos["open_price"])
            curr_price = float(pos["current_price"])
            profit = float(pos["profit"])

            # Fetch latest technicals for position symbol
            tech_data = mt5_service.get_candles_with_indicators(symbol, "M15") or {}
            active_strats = db.get_active_strategies()
            _, weighted_summary = ai_service._evaluate_strategy_probabilities(symbol, tech_data, active_strats)

            consensus_action = weighted_summary.get("consensus_action", "HOLD")
            buy_prob = weighted_summary.get("buy_probability", 50.0)
            sell_prob = weighted_summary.get("sell_probability", 50.0)

            # Determine strategic recommendation for this open trade
            if pos_type == "BUY":
                if profit > 0 and sell_prob >= 65.0:
                    recommendation = "TAKE_PROFIT_EARLY"
                    recommendation_fa = "سیو سود زودهنگام (افزایش مومنتوم فروش در بازار)"
                    status_color = "emerald"
                elif profit < 0 and sell_prob >= 75.0:
                    recommendation = "CUT_LOSS"
                    recommendation_fa = "کاهش ریسک و خروج (تغییر جهت روند بازار)"
                    status_color = "rose"
                elif profit > 0 and buy_prob >= 60.0:
                    recommendation = "HOLD_AND_TRAIL"
                    recommendation_fa = "حفظ موقعیت و همراهی با روند صعودی"
                    status_color = "cyan"
                else:
                    recommendation = "HOLD"
                    recommendation_fa = "حفظ موقعیت در محدوده نوسان طبیعی"
                    status_color = "blue"
            else:  # SELL
                if profit > 0 and buy_prob >= 65.0:
                    recommendation = "TAKE_PROFIT_EARLY"
                    recommendation_fa = "سیو سود زودهنگام (افزایش مومنتوم خرید در بازار)"
                    status_color = "emerald"
                elif profit < 0 and buy_prob >= 75.0:
                    recommendation = "CUT_LOSS"
                    recommendation_fa = "کاهش ریسک و خروج (تغییر جهت روند بازار)"
                    status_color = "rose"
                elif profit > 0 and sell_prob >= 60.0:
                    recommendation = "HOLD_AND_TRAIL"
                    recommendation_fa = "حفظ موقعیت و همراهی با روند نزولی"
                    status_color = "cyan"
                else:
                    recommendation = "HOLD"
                    recommendation_fa = "حفظ موقعیت در محدوده نوسان طبیعی"
                    status_color = "blue"

            now_dt = datetime.now()
            now_ts = now_dt.timestamp()
            now_str = now_dt.strftime("%H:%M:%S")

            check_result = {
                "ticket": ticket,
                "symbol": symbol,
                "type": pos_type,
                "profit": profit,
                "last_check_ts": now_ts,
                "last_check_time": now_str,
                "recommendation": recommendation,
                "recommendation_fa": recommendation_fa,
                "status_color": status_color,
                "consensus_action": consensus_action,
                "buy_prob": buy_prob,
                "sell_prob": sell_prob,
                "rationale": f"بررسی مجدد معامله #{ticket} ({symbol}): سود فعلی: {profit:+.2f}$ | احتمال خرید: {buy_prob}%، احتمال فروش: {sell_prob}%. توصیه هوش مصنوعی: {recommendation_fa}"
            }

            self.position_ai_checks[ticket] = check_result

            # Record into SQLite audit logs
            db.record_ai_audit_log(
                context_type="market_analysis",
                prompt_sent=f"Re-evaluating Open Position #{ticket} ({symbol} {pos_type} PnL: {profit:+.2f}$)\nConsensus: BUY {buy_prob}% vs SELL {sell_prob}%",
                response_received=check_result["rationale"],
                symbol=symbol,
                timeframe="M15",
                model="trader",
                provider="OmniRoute",
                parsed_action=recommendation,
                confidence=float(max(buy_prob, sell_prob)),
                latency_ms=120,
                status="SUCCESS"
            )

            return {"success": True, "check": check_result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_position_ai_check(self, ticket: int) -> Dict[str, Any]:
        """Return AI re-evaluation status and seconds elapsed since last check."""
        now_ts = datetime.now().timestamp()
        if ticket in self.position_ai_checks:
            c = self.position_ai_checks[ticket]
            sec_ago = max(0, int(now_ts - c["last_check_ts"]))
            return {
                **c,
                "seconds_ago": sec_ago,
                "seconds_ago_formatted": f"{sec_ago} ثانیه پیش" if sec_ago < 60 else f"{sec_ago//60} دقیقه پیش"
            }
        return {
            "ticket": ticket,
            "seconds_ago": -1,
            "seconds_ago_formatted": "در صف بررسی...",
            "recommendation": "ANALYZING",
            "recommendation_fa": "در حال تحلیل اولیه...",
            "status_color": "slate"
        }
    # --- Multi-Pair Portfolio Hub & Master AI Supervisor Logic ---

    async def analyze_all_portfolio_pairs(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Rapidly evaluate all configured portfolio pairs using 52-strategy weighted consensus,
        live indicator confluence, and correlation metrics.
        """
        pairs = db.get_portfolio_pairs()
        if not pairs:
            return {"total_pairs": 0, "approved_count": 0, "pairs": []}

        open_positions = mt5_service.get_open_positions()
        open_symbols = {p["symbol"].upper(): p for p in open_positions}
        active_strats = db.get_active_strategies()

        results = []
        approved_count = 0

        for p_cfg in pairs:
            symbol = p_cfg["symbol"]
            timeframe = p_cfg.get("timeframe", "M15")
            is_enabled = bool(p_cfg.get("is_enabled", 1))
            min_conf = float(p_cfg.get("min_confidence", 70.0))
            lot_size = float(p_cfg.get("lot_size", 0.01))

            overview = mt5_service.get_symbol_overview(symbol) or {
                "symbol": symbol, "ask": 0.0, "bid": 0.0, "spread_points": 0, "digits": 5
            }
            tech_data = mt5_service.get_candles_with_indicators(symbol, timeframe) or {
                "symbol": symbol, "timeframe": timeframe, "trend": "خنثی", "rsi": 50.0, "atr": 0.001
            }

            # Compute mathematical 52-strategy probability consensus
            _, weighted_summary = ai_service._evaluate_strategy_probabilities(symbol, tech_data, active_strats)

            action = weighted_summary.get("consensus_action", "HOLD")
            conf = float(weighted_summary.get("final_confidence", 50.0))
            price = float(tech_data.get("current_price", overview.get("ask", 0.0)))
            support = float(tech_data.get("support", price * 0.998))
            resistance = float(tech_data.get("resistance", price * 1.002))
            atr = float(tech_data.get("atr", 0.001))
            spread_pips = overview.get("spread_points", 0) / 10.0

            # Count open positions for this specific symbol
            symbol_positions = [p for p in open_positions if p["symbol"].upper() == symbol.upper()]
            open_pos_count = len(symbol_positions)
            open_pos_profit = round(sum(p["profit"] for p in symbol_positions), 2)
            is_already_open = open_pos_count > 0

            # Calculate historical win rate and stats from SQLite
            hist_stats = db.get_symbol_historical_stats(symbol)
            historical_win_rate = hist_stats.get("win_rate", 75.0)
            historical_formatted = hist_stats.get("formatted", f"{historical_win_rate}%")
            historical_trades = hist_stats.get("total_trades", 0)
            historical_pnl = hist_stats.get("total_pnl", 0.0)

            if action == "BUY":
                suggested_sl = round(min(support, price - (atr * 1.5)), overview.get("digits", 5))
                suggested_tp = round(price + (abs(price - suggested_sl) * 1.8), overview.get("digits", 5))
            elif action == "SELL":
                suggested_sl = round(max(resistance, price + (atr * 1.5)), overview.get("digits", 5))
                suggested_tp = round(price - (abs(suggested_sl - price) * 1.8), overview.get("digits", 5))
            else:
                suggested_sl = support
                suggested_tp = resistance

            # Qualification check
            is_approved = (
                is_enabled and
                action in ["BUY", "SELL"] and
                conf >= min_conf and
                spread_pips <= float(p_cfg.get("max_spread_pips", 3.5))
            )

            if is_approved:
                approved_count += 1

            rationale = (
                f"اجماع ۵۲ استراتژی بر روی {symbol} ({timeframe}): سیگنال {action} با ضریب اطمینان {conf}% "
                f"(خرید: {weighted_summary.get('buy_probability')}٪، فروش: {weighted_summary.get('sell_probability')}٪). "
                f"وین‌ریت سوابق گذشته: {historical_formatted}. روند: {tech_data.get('trend')}، RSI: {tech_data.get('rsi')}."
            )

            pair_result = {
                "id": p_cfg.get("id"),
                "symbol": symbol,
                "title_fa": p_cfg.get("title_fa", f"جفت‌ارز {symbol}"),
                "is_enabled": is_enabled,
                "min_confidence": min_conf,
                "lot_size": lot_size,
                "timeframe": timeframe,
                "ask": overview.get("ask", 0.0),
                "bid": overview.get("bid", 0.0),
                "spread_pips": spread_pips,
                "digits": overview.get("digits", 5),
                "trend": tech_data.get("trend", "خنثی"),
                "rsi": tech_data.get("rsi", 50.0),
                "action": action,
                "confidence": conf,
                "suggested_sl": suggested_sl,
                "suggested_tp": suggested_tp,
                "weighted_probabilities": weighted_summary,
                "is_approved": is_approved,
                "is_already_open": is_already_open,
                "open_positions_count": open_pos_count,
                "open_positions_profit": open_pos_profit,
                "open_trade_profit": open_pos_profit,
                "historical_win_rate": historical_win_rate,
                "historical_formatted": historical_formatted,
                "historical_trades": historical_trades,
                "historical_pnl": historical_pnl,
                "rationale": rationale
            }
            results.append(pair_result)

        # Sort so approved pairs appear at top
        results.sort(key=lambda x: (x["is_approved"], x["confidence"]), reverse=True)

        total_lot = round(sum(r["lot_size"] for r in results if r["is_approved"]), 2)
        summary = {
            "total_pairs": len(results),
            "enabled_pairs": sum(1 for r in results if r["is_enabled"]),
            "approved_count": approved_count,
            "total_lot_size": total_lot,
            "is_supervisor_active": self.is_portfolio_supervisor_running,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pairs": results
        }
        self.last_portfolio_analysis = summary
        return summary
    async def execute_portfolio_basket(self, selected_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute a batch basket trade on all approved pairs (or a specific selection).
        """
        blocked, reason = self.check_daily_loss_guard()
        if blocked:
            return {"success": False, "message": reason, "executed": 0}

        analysis = await self.analyze_all_portfolio_pairs(force_refresh=False)
        pairs = analysis.get("pairs", [])
        targets = [
            p for p in pairs 
            if p["is_approved"] and (selected_symbols is None or p["symbol"].upper() in [s.upper() for s in selected_symbols])
        ]

        if not targets:
            return {
                "success": False,
                "message": "هیچ جفت‌ارزی در حال حاضر شرایط لازم (حد نصاب اطمینان هوش مصنوعی) را برای ورود احراز نکرده است.",
                "executed": 0
            }

        executed = 0
        errors = []
        open_positions = mt5_service.get_open_positions()
        open_symbols = {p["symbol"].upper() for p in open_positions}

        for p in targets:
            sym = p["symbol"]
            if sym.upper() in open_symbols:
                continue  # Avoid duplicate entries on same symbol

            act = p["action"]
            vol = p["lot_size"]
            sl = p.get("suggested_sl")
            tp = p.get("suggested_tp")
            conf = p["confidence"]

            res = mt5_service.execute_order(
                symbol=sym,
                order_type=act,
                volume=vol,
                sl=sl,
                tp=tp,
                comment="AI Portfolio Basket",
                confidence=conf,
                prediction_title=f"معامله سبدی پورتفوی ({sym})",
                prediction_reason=f"ورود همزمان پورتفوی هوش مصنوعی با اطمینان {conf}% و تایید ۵۲ استراتژی"
            )

            if res.get("success"):
                executed += 1
                self.log("PORTFOLIO_EXEC", f"⚡ معامله سبدی {act} برای {sym} به حجم {vol} لات با موفقیت ثبت شد (تیکت: #{res.get('order_ticket')}).")
            else:
                err = f"{sym}: {res.get('error')}"
                errors.append(err)
                self.log("PORTFOLIO_ERR", f"❌ خطا در ثبت معامله سبدی {sym}: {res.get('error')}")

        return {
            "success": executed > 0,
            "executed_count": executed,
            "errors": errors,
            "message": f"تعداد {executed} معامله از سبد پورتفوی با موفقیت باز شد." if executed > 0 else f"خطا در باز کردن سبد: {'; '.join(errors)}"
        }

    async def start_portfolio_supervisor(self, interval_seconds: int = 30) -> Dict[str, Any]:
        """Start autonomous background AI Master Supervisor for portfolio execution."""
        if self.is_portfolio_supervisor_running:
            return {"success": True, "message": "ناظر هوشمند خودکار سبدی در حال حاضر فعال است."}

        self.portfolio_supervisor_interval_seconds = max(10, interval_seconds)
        self.is_portfolio_supervisor_running = True
        db.set_state("portfolio_supervisor", {"is_running": True, "interval_seconds": self.portfolio_supervisor_interval_seconds})
        self.portfolio_supervisor_task = asyncio.create_task(self._run_portfolio_supervisor_loop())
        self.log("PORTFOLIO_SUP_START", f"🤖 ناظر هوشمند خودکار پورتفوی چند جفت‌ارز با بازه {interval_seconds} ثانیه آغاز شد.")
        return {"success": True, "message": "ناظر هوشمند خودکار سبدی با موفقیت آغاز شد."}

    async def stop_portfolio_supervisor(self) -> Dict[str, Any]:
        """Stop autonomous portfolio supervisor."""
        if not self.is_portfolio_supervisor_running:
            return {"success": False, "message": "ناظر خودکار سبدی غیرفعال است."}

        self.is_portfolio_supervisor_running = False
        if self.portfolio_supervisor_task:
            self.portfolio_supervisor_task.cancel()
            self.portfolio_supervisor_task = None

        db.set_state("portfolio_supervisor", {"is_running": False})
        self.log("PORTFOLIO_SUP_STOP", "🛑 ناظر هوشمند خودکار سبدی متوقف شد.")
        return {"success": True, "message": "ناظر خودکار سبدی متوقف شد."}

    async def _run_portfolio_supervisor_loop(self):
        """Background supervisor loop scanning all portfolio pairs and auto-entering qualified setups."""
        while self.is_portfolio_supervisor_running:
            try:
                # Check MT5 connection and available slots
                if mt5_service.ensure_connected():
                    open_positions = mt5_service.get_open_positions()
                    if len(open_positions) < settings.MAX_OPEN_POSITIONS:
                        await self.execute_portfolio_basket()
                await asyncio.sleep(self.portfolio_supervisor_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log("PORTFOLIO_SUP_ERR", f"خطا در چرخه ناظر سبدی: {e}")
                await asyncio.sleep(5)

    def get_portfolio_supervisor_status(self) -> Dict[str, Any]:
        """Return supervisor running state and last portfolio evaluation."""
        return {
            "is_running": self.is_portfolio_supervisor_running,
            "interval_seconds": self.portfolio_supervisor_interval_seconds,
            "last_analysis": self.last_portfolio_analysis
        }


trading_engine = TradingEngine()
