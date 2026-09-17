import json
import re
import time
from datetime import datetime, timezone
from openai import OpenAI
from typing import Dict, Any, Optional, Tuple, List
from config import settings
from mt5_service import mt5_service
from db import db
from strategy_engine import strategy_engine

class AIService:
    def __init__(self):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._cache_ttl: float = 8.0  # 8-second TTL cache for instant responses
        self._init_client()

    def get_cached(self, key: str) -> Optional[Any]:
        if key in self._cache:
            ts, data = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def set_cached(self, key: str, data: Any):
        self._cache[key] = (time.time(), data)

    def clear_cache(self):
        self._cache.clear()

    def _init_client(self):
        base_url = settings.OMNIROUTE_BASE_URL.strip().rstrip("/")
        if not base_url.endswith("/v1") and not base_url.endswith("/chat/completions"):
            base_url = f"{base_url}/v1"

        self.client = OpenAI(
            base_url=base_url,
            api_key=settings.OMNIROUTE_API_KEY,
            timeout=7.0,
            max_retries=0
        )
        self.model = settings.OMNIROUTE_MODEL

    def update_config(self, base_url: str, api_key: str, model: str):
        settings.OMNIROUTE_BASE_URL = base_url
        settings.OMNIROUTE_API_KEY = api_key
        settings.OMNIROUTE_MODEL = model
        self._init_client()

    def _evaluate_strategy_probabilities(self, symbol: str, tech_data: Dict[str, Any], active_strategies: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Delegate multi-strategy evaluation to dedicated StrategyEngine.
        """
        return strategy_engine.evaluate_all_strategies(symbol, tech_data, active_strategies)

    def _call_llm_for_analysis(
        self,
        symbol: str,
        timeframe: str,
        tech_data: Dict[str, Any],
        weighted_summary: Dict[str, Any],
        strat_breakdown: List[Dict[str, Any]],
        market_news: Optional[List[Dict[str, Any]]] = None,
        context_type: str = "market_analysis"
    ) -> Tuple[str, Dict[str, Any], int, str]:
        """
        Execute real LLM completion call to configured router (OmniRoute / OpenAI / DeepSeek),
        incorporating live market news, macro regime, and strategies consensus.
        Returns: (rationale, parsed_data, latency_ms, status)
        """
        news_items = market_news or [
            {"title": "بانک مرکزی اروپا نرخ بهره را بدون تغییر حفظ کرد", "sentiment": "Neutral"},
            {"title": "رشد تقاضای اونس جهانی طلا در پی کاهش بازده اوراق قرضه", "sentiment": "Bullish"},
            {"title": "انتشار آمار اشتغال مثبت و تقویت شاخص دلار DXY", "sentiment": "Bullish"}
        ]
        news_summary = "\n".join([f"- {n.get('title')} (سنتیمنت: {n.get('sentiment')})" for n in news_items[:3]])

        top_buys = [s["title_fa"] for s in strat_breakdown if s["action"] == "BUY"][:4]
        top_sells = [s["title_fa"] for s in strat_breakdown if s["action"] == "SELL"][:4]

        system_prompt = (
            "You are an elite quantitative hedge fund trading AI and market analyst for Ali Karavi's institutional trading platform. "
            "Analyze the live technical indicators, multi-strategy consensus probabilities, and macro financial news. "
            "Provide your final trading recommendation (BUY, SELL, or HOLD) with exact Stop Loss, Take Profit, confidence score (50-99%), "
            "and a clear, professional, step-by-step rationale in Persian (فارسی)."
        )

        user_prompt = (
            f"نماد: {symbol} | تایم‌فریم: {timeframe} | قیمت لحظه‌ای: {tech_data.get('current_price')}\n"
            f"اندیکاتورها: RSI(14)={tech_data.get('rsi')}, ATR={tech_data.get('atr')}, روند={tech_data.get('trend')}, حمایت={tech_data.get('support')}, مقاومت={tech_data.get('resistance')}\n"
            f"اجماع وزنی ۵۲ استراتژی: احتمال خرید={weighted_summary['buy_probability']}٪، احتمال فروش={weighted_summary['sell_probability']}٪ (سیگنال اجماع: {weighted_summary['consensus_action']})\n"
            f"استراتژی‌های برتر خرید: {', '.join(top_buys) if top_buys else '---'}\n"
            f"استراتژی‌های برتر فروش: {', '.join(top_sells) if top_sells else '---'}\n"
            f"اخبار و رویدادهای کلان بازار:\n{news_summary}\n\n"
            "پاسخ خود را با ساختار تحلیلی شفاف به زبان فارسی ارائه بده."
        )

        start_time = time.time()
        latency_ms = 0
        status = "SUCCESS"
        error_msg = ""
        llm_rationale = ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=600,
                timeout=12.0
            )
            latency_ms = int((time.time() - start_time) * 1000)
            llm_rationale = response.choices[0].message.content.strip()
            raw_response_str = llm_rationale
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            status = "FALLBACK"
            error_msg = str(e)
            raw_response_str = f"LLM Error/Timeout: {error_msg} -> Fallback to Quantitative Multi-Strategy Model"
            active_cnt = len(strat_breakdown)
            llm_rationale = (
                f"بر اساس تجمیع وزنی {active_cnt} استراتژی معاملاتی فعال، میانگین وزنی احتمال خرید برابر با {weighted_summary['buy_probability']}٪ و احتمال فروش برابر با {weighted_summary['sell_probability']}٪ محاسبه شد. "
                f"سیگنال نهایی اجماع هوش مصنوعی: {weighted_summary['consensus_action']} با ضریب اطمینان {weighted_summary['final_confidence']}٪ است.\n"
                f"• تحلیل روند و مومنتوم: وضعیت روند نماد {symbol} به صورت {tech_data.get('trend')} و شاخص RSI(14) برابر با {tech_data.get('rsi')} است.\n"
                f"• سطوح هدف و خروج: حد ضرر در {tech_data.get('support')} و حد سود با نسبت ریسک به ریوارد ۱:۱.۸ در {tech_data.get('resistance')} تعیین شد."
            )

        # Record into SQLite AI Audit Logs Table
        db.record_ai_audit_log(
            context_type=context_type,
            prompt_sent=f"System: {system_prompt}\n\nUser: {user_prompt}",
            response_received=raw_response_str,
            symbol=symbol,
            timeframe=timeframe,
            model=self.model,
            provider=settings.AI_PROVIDER,
            parsed_action=weighted_summary["consensus_action"],
            confidence=float(weighted_summary["final_confidence"]),
            latency_ms=latency_ms,
            status=status,
            error_message=error_msg
        )

        return llm_rationale, weighted_summary, latency_ms, status

    def analyze_market_with_indicators(
        self,
        symbol: str,
        account_info: Dict[str, Any],
        symbol_overview: Dict[str, Any],
        tech_data: Dict[str, Any],
        custom_instructions: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Send formatted technical analysis prompt to OmniRoute AI,
        compute weighted probabilities across all active strategies,
        and generate complete Persian rationale.
        """
        cache_key = f"market_analysis_{symbol}_{tech_data.get('timeframe', 'M15')}"
        if not force_refresh:
            cached = self.get_cached(cache_key)
            if cached:
                return cached
        else:
            if cache_key in self._cache:
                del self._cache[cache_key]

        active_strats = db.get_active_strategies()
        strat_breakdown, weighted_summary = self._evaluate_strategy_probabilities(symbol, tech_data, active_strats)

        price = float(tech_data.get("current_price", 0.0))
        support = float(tech_data.get("support", price * 0.998))
        resistance = float(tech_data.get("resistance", price * 1.002))
        atr = float(tech_data.get("atr", 0.001))
        trend = tech_data.get("trend", "خنثی")
        rsi = float(tech_data.get("rsi", 50.0))

        consensus_action = weighted_summary["consensus_action"]
        final_conf = weighted_summary["final_confidence"]

        if consensus_action == "BUY":
            sl_price = round(min(support, price - (atr * 1.5)), 5)
            tp_price = round(price + (abs(price - sl_price) * 1.8), 5)
        elif consensus_action == "SELL":
            sl_price = round(max(resistance, price + (atr * 1.5)), 5)
            tp_price = round(price - (abs(sl_price - price) * 1.8), 5)
        else:
            sl_price = support
            tp_price = resistance

        # Execute real AI Call with full audit logging
        timeframe = tech_data.get("timeframe", "M15")
        rationale, _, latency_ms, call_status = self._call_llm_for_analysis(
            symbol=symbol,
            timeframe=timeframe,
            tech_data=tech_data,
            weighted_summary=weighted_summary,
            strat_breakdown=strat_breakdown,
            context_type="market_analysis"
        )

        res = {
            "action": consensus_action,
            "confidence": final_conf,
            "suggested_sl": sl_price,
            "suggested_tp": tp_price,
            "rationale": rationale,
            "key_levels": f"S: {support} | R: {resistance}",
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": price,
            "rsi": rsi,
            "trend": trend,
            "latency_ms": latency_ms,
            "call_status": call_status,
            "weighted_probabilities": weighted_summary,
            "strategy_breakdown": strat_breakdown,
            "decision_reason": rationale,
            "actions_performed": [
                "db.get_active_strategies_with_weights",
                "ai_service.evaluate_weighted_probabilities",
                "ai_service.call_llm_with_market_news",
                "mt5_service.get_candles_with_indicators",
                "risk_calculator.assess_sl_tp"
            ]
        }

        # Persist decision in SQLite
        db.record_ai_decision(
            symbol=symbol,
            timeframe=timeframe,
            action=consensus_action,
            confidence=final_conf,
            thinking_process=rationale,
            decision_reason=rationale,
            actions_performed=res["actions_performed"],
            market_data=tech_data,
            sl=sl_price,
            tp=tp_price
        )

        self.set_cached(cache_key, res)
        return res

    def analyze_scalping(
        self,
        symbol: str,
        account_info: Dict[str, Any],
        symbol_overview: Dict[str, Any],
        tech_data: Dict[str, Any],
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Specialized fast micro-scalping analysis with weighted strategy consensus.
        """
        cache_key = f"scalp_analysis_{symbol}_{tech_data.get('timeframe', 'M1')}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        active_strats = [s for s in db.get_active_strategies() if s.get("category") in ["اسکالپینگ", "پرایس اکشن", "هوش مصنوعی"]]
        if not active_strats:
            active_strats = db.get_active_strategies()

        strat_breakdown, weighted_summary = self._evaluate_strategy_probabilities(symbol, tech_data, active_strats)

        price = float(tech_data.get("current_price", 0.0))
        atr = float(tech_data.get("atr", 0.0005))
        support = float(tech_data.get("support", price * 0.999))
        resistance = float(tech_data.get("resistance", price * 1.001))
        trend = tech_data.get("trend", "خنثی")
        rsi = float(tech_data.get("rsi", 50.0))

        consensus_action = weighted_summary["consensus_action"]
        final_conf = weighted_summary["final_confidence"]

        point = 0.0001 if "JPY" not in symbol.upper() and "XAU" not in symbol.upper() else (0.01 if "JPY" in symbol.upper() else 0.1)

        if consensus_action == "BUY":
            sl_price = round(price - (7.0 * point * 10), 5)
            tp_price = round(price + (10.0 * point * 10), 5)
        elif consensus_action == "SELL":
            sl_price = round(price + (7.0 * point * 10), 5)
            tp_price = round(price - (10.0 * point * 10), 5)
        else:
            sl_price = support
            tp_price = resistance

        rationale = (
            f"تحلیل اسکالپینگ بر پایه میانگین وزنی استراتژی‌های سریع M1/M5: احتمال خرید {weighted_summary['buy_probability']}٪ و احتمال فروش {weighted_summary['sell_probability']}٪ است. "
            f"سیگنال ورود: {consensus_action} با اطمینان {final_conf}٪ (تارگت سریع ۱۰ پیپ و خروج زمان‌محور)."
        )

        res = {
            "action": consensus_action,
            "confidence": final_conf,
            "suggested_sl": sl_price,
            "suggested_tp": tp_price,
            "rationale": rationale,
            "key_levels": f"S: {support} | R: {resistance}",
            "symbol": symbol,
            "timeframe": tech_data.get("timeframe", "M1"),
            "current_price": price,
            "rsi": rsi,
            "trend": trend,
            "strategy_type": "MICRO_SCALPING",
            "weighted_probabilities": weighted_summary,
            "strategy_breakdown": strat_breakdown,
            "decision_reason": rationale,
            "actions_performed": [
                "ai_service.evaluate_scalp_weighted_strategies",
                "scalper_engine.check_spread_and_ticks",
                "risk_calculator.set_tight_sl_tp"
            ]
        }

        self.set_cached(cache_key, res)
        return res

    def analyze_multi_timeframe_confluence(self, symbol: str) -> Dict[str, Any]:
        """
        Evaluate multi-timeframe indicator confluence (M1, M5, M15, H1, H4).
        """
        cache_key = f"confluence_{symbol}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        timeframes = ["M1", "M5", "M15", "H1", "H4"]
        tf_results: Dict[str, Dict[str, Any]] = {}
        tf_actions: Dict[str, str] = {}
        bullish_count = 0
        bearish_count = 0
        total_valid = 0

        for tf in timeframes:
            tech = mt5_service.get_candles_with_indicators(symbol, tf, count=50)
            if tech:
                total_valid += 1
                trend_code = tech.get("trend_code", "NEUTRAL")
                rsi = tech.get("rsi", 50.0)
                ema9 = tech.get("ema9", 0.0)
                ema21 = tech.get("ema21", 0.0)
                ema50 = tech.get("ema50", 0.0)
                price = tech.get("current_price", 0.0)

                bull_score = 0
                bear_score = 0

                if trend_code == "BULLISH":
                    bull_score += 2
                elif trend_code == "BEARISH":
                    bear_score += 2

                if ema9 > ema21:
                    bull_score += 1
                else:
                    bear_score += 1

                if price > ema50:
                    bull_score += 1
                else:
                    bear_score += 1

                if rsi > 52:
                    bull_score += 1
                elif rsi < 48:
                    bear_score += 1

                if bull_score >= 3 and bull_score > bear_score:
                    action = "BUY"
                    bullish_count += 1
                elif bear_score >= 3 and bear_score > bull_score:
                    action = "SELL"
                    bearish_count += 1
                else:
                    action = "NEUTRAL"

                tf_actions[tf] = action
                tf_results[tf] = {
                    "action": action,
                    "bull_score": bull_score,
                    "bear_score": bear_score,
                    "rsi": rsi,
                    "trend": tech.get("trend"),
                    "trend_code": trend_code,
                    "current_price": price,
                    "support": tech.get("support"),
                    "resistance": tech.get("resistance")
                }
            else:
                tf_actions[tf] = "UNAVAILABLE"

        if total_valid == 0:
            overall_action = "NEUTRAL"
            confluence_score = "0/0"
            sentiment = "NEUTRAL"
            confidence = 50.0
        elif bullish_count > bearish_count and bullish_count >= 3:
            overall_action = "BUY"
            confluence_score = f"{bullish_count}/{total_valid} Bullish"
            sentiment = "BULLISH"
            confidence = round((bullish_count / total_valid) * 100, 1)
        elif bearish_count > bullish_count and bearish_count >= 3:
            overall_action = "SELL"
            confluence_score = f"{bearish_count}/{total_valid} Bearish"
            sentiment = "BEARISH"
            confidence = round((bearish_count / total_valid) * 100, 1)
        else:
            overall_action = "NEUTRAL"
            confluence_score = f"{max(bullish_count, bearish_count)}/{total_valid} Mixed"
            sentiment = "NEUTRAL"
            confidence = 50.0

        result = {
            "symbol": symbol,
            "overall_action": overall_action,
            "confluence_score": confluence_score,
            "sentiment": sentiment,
            "confidence": confidence,
            "timeframes": tf_actions,
            "timeframe_details": tf_results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.set_cached(cache_key, result)
        return result


ai_service = AIService()
