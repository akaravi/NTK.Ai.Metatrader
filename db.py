"""SQLite Database Manager for NTK.Ai.Metatrader.

Developed by Ali Karavi (https://alikaravi.com/)
Provides persistent storage, 50-strategy catalog with weight multipliers,
decision audit trail, prediction attribution matrix, and multi-session chat history.
"""

import os
import json
import sqlite3
import csv
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "ntk_trader.db"

# 50 Institutional Trading Strategies Catalog with Weights
DEFAULT_STRATEGIES_50 = [
    # 1. Trend Following (10 Strategies)
    {"id": "strat_ema_cross_9_21", "name": "EMA 9/21 Golden Cross", "title_fa": "تقاطع طلایی EMA 9 و EMA 21", "category": "تعقیب روند", "description_fa": "ورود در پولبک به EMA 21 با تایید شیب روند میانگین‌های متحرک.", "is_active": 1, "win_rate": 78.5, "weight": 1.5, "risk_level": "کم", "icon": "trending-up", "timeframe_default": "M15"},
    {"id": "strat_ema_cross_50_200", "name": "EMA 50/200 Golden/Death Cross", "title_fa": "تقاطع کلاسیک EMA 50 و EMA 200", "category": "تعقیب روند", "description_fa": "تایید چرخش‌های بزرگ روند ماژور بازار بر اساس تقاطع طلایی و مرگ.", "is_active": 1, "win_rate": 81.0, "weight": 2.0, "risk_level": "کم", "icon": "trending-up", "timeframe_default": "H4"},
    {"id": "strat_supertrend_atr", "name": "SuperTrend ATR Volatility", "title_fa": "سوپرترند و تعقیب نوسانات ATR", "category": "تعقیب روند", "description_fa": "ورود با تغییر رنگ خط سوپرترند و تعقیب سود تا تغییر جهت روند.", "is_active": 1, "win_rate": 80.0, "weight": 1.5, "risk_level": "کم", "icon": "compass", "timeframe_default": "H1"},
    {"id": "strat_triple_ema", "name": "Triple EMA 8/13/21 System", "title_fa": "سیستم سه‌گانه EMA 8/13/21", "category": "تعقیب روند", "description_fa": "فیلتر شتاب روند با سه میانگین متحرک نمایی کوتاه و میان‌مدت.", "is_active": 1, "win_rate": 77.0, "weight": 1.0, "risk_level": "کم", "icon": "activity", "timeframe_default": "M15"},
    {"id": "strat_adx_trend", "name": "ADX Trend Strength Filter", "title_fa": "فیلتر قدرت روند با شاخص ADX", "category": "تعقیب روند", "description_fa": "ورود در روند تنها زمانی که شاخص ADX بالای ۲۵ و خطوط DMI هم‌راستا باشند.", "is_active": 1, "win_rate": 76.0, "weight": 1.0, "risk_level": "متوسط", "icon": "gauge", "timeframe_default": "H1"},
    {"id": "strat_parabolic_sar", "name": "Parabolic SAR Velocity Trail", "title_fa": "پارابولیک سار و تعقیب شتاب قیمت", "category": "تعقیب روند", "description_fa": "ورود و تعیین حد ضرر متحرک بر مبنای نقاط پارابولیک سار.", "is_active": 1, "win_rate": 73.5, "weight": 1.0, "risk_level": "متوسط", "icon": "chevrons-up", "timeframe_default": "M15"},
    {"id": "strat_keltner_channels", "name": "Keltner Channel Trend Ride", "title_fa": "کانال‌های کلتنر و کانال رگرسیون", "category": "تعقیب روند", "description_fa": "معامله در جهت خروج قیمت از باندهای کلتنر همراه با شتاب نوسان.", "is_active": 1, "win_rate": 75.0, "weight": 1.0, "risk_level": "کم", "icon": "maximize-2", "timeframe_default": "H1"},
    {"id": "strat_donchian_break", "name": "Donchian 20-Day Breakout", "title_fa": "شکست کانال دانچیان (سیستم لاک‌پشت‌ها)", "category": "تعقیب روند", "description_fa": "ورود در سقف و کف ۲۰ دوره‌ای دانچیان جهت گرفتن روندهای بزرگ.", "is_active": 1, "win_rate": 74.5, "weight": 1.2, "risk_level": "متوسط", "icon": "shield", "timeframe_default": "D1"},
    {"id": "strat_ichimoku_cloud", "name": "Ichimoku Kumo Cloud Break", "title_fa": "ابر کومو و ایچیموکو کینکو هیو", "category": "تعقیب روند", "description_fa": "تایید شکست ابر کومو همراه با تقاطع تنکان‌سن و کیجون‌سن.", "is_active": 1, "win_rate": 79.0, "weight": 1.5, "risk_level": "کم", "icon": "cloud-rain", "timeframe_default": "H4"},
    {"id": "strat_gmma_ribbon", "name": "Guppy Multiple Moving Average", "title_fa": "روبان میانگین‌های گامی (GMMA)", "category": "تعقیب روند", "description_fa": "تطبیق رفتار خریداران کوتاه‌مدت با سرمایه‌گذاران بلندمدت در روبان GMMA.", "is_active": 1, "win_rate": 77.5, "weight": 1.0, "risk_level": "کم", "icon": "git-branch", "timeframe_default": "M15"},

    # 2. Scalping & Micro-Momentum (8 Strategies)
    {"id": "strat_m1_scalp", "name": "M1/M5 Fast Momentum Scalp", "title_fa": "اسکالپینگ پرسرعت مومنتوم (M1/M5)", "category": "اسکالپینگ", "description_fa": "شکار تیک‌های پرشتاب با تارگت‌های ۵ تا ۱۵ پیپ و خروج زمان‌محور ۳ تا ۱۰ دقیقه.", "is_active": 1, "win_rate": 84.0, "weight": 2.0, "risk_level": "متوسط", "icon": "zap", "timeframe_default": "M1"},
    {"id": "strat_vwap_scalp", "name": "VWAP Institutional Scalp", "title_fa": "اسکالپینگ با حجم موزون قیمت (VWAP)", "category": "اسکالپینگ", "description_fa": "معامله در پولبک‌ها به میانگین موزون حجمی روزانه (VWAP).", "is_active": 1, "win_rate": 82.5, "weight": 1.5, "risk_level": "کم", "icon": "bar-chart", "timeframe_default": "M5"},
    {"id": "strat_stoch_fast_scalp", "name": "Fast Stochastic 5/3/3 Scalp", "title_fa": "اسکالپ استوکاستیک سریع ۵/۳/۳", "category": "اسکالپینگ", "description_fa": "تقاطع سریع خطوط %K و %D در محدوده‌های ۲۰ و ۸۰ در تایم ۱ دقیقه.", "is_active": 1, "win_rate": 79.0, "weight": 1.2, "risk_level": "متوسط", "icon": "fast-forward", "timeframe_default": "M1"},
    {"id": "strat_ema_ribbon_pullback", "name": "Fast EMA Ribbon Pullback", "title_fa": "پولبک به روبان میانگین‌های سریع", "category": "اسکالپینگ", "description_fa": "ورود در برخورد اول کندل‌های ۵ دقیقه به روبان فشرده EMAها.", "is_active": 1, "win_rate": 81.0, "weight": 1.5, "risk_level": "کم", "icon": "layers", "timeframe_default": "M5"},
    {"id": "strat_order_flow_imbalance", "name": "Order Flow Tick Imbalance", "title_fa": "عدم تعادل جریان سفارشات تیک", "category": "اسکالپینگ", "description_fa": "شناسایی برتری حجم خریداران بر فروشندگان در اردرهای لحظه‌ای.", "is_active": 1, "win_rate": 83.0, "weight": 1.8, "risk_level": "متوسط", "icon": "cpu", "timeframe_default": "M1"},
    {"id": "strat_1min_range_break", "name": "1-Min Micro Range Breakout", "title_fa": "شکست دامنه فشرده ۱ دقیقه‌ای", "category": "اسکالپینگ", "description_fa": "انفجار قیمت پس از فشردگی حداقل ۵ کندل ۱ دقیقه.", "is_active": 1, "win_rate": 80.5, "weight": 1.2, "risk_level": "متوسط", "icon": "box", "timeframe_default": "M1"},
    {"id": "strat_tick_divergence_scalp", "name": "Tick Volume Divergence Scalp", "title_fa": "واگرایی حجم تیک در اسکالپ", "category": "اسکالپینگ", "description_fa": "عدم همراهی حجم تیک با سقف و کف‌های جدید در M1.", "is_active": 1, "win_rate": 81.5, "weight": 1.5, "risk_level": "متوسط", "icon": "git-pull-request", "timeframe_default": "M1"},
    {"id": "strat_london_open_scalp", "name": "London Open Session Breakout", "title_fa": "اسکالپ گشایش سشن لندن", "category": "اسکالپینگ", "description_fa": "شکار جهت نقدینگی در ۳۰ دقیقه اول گشایش بازار لندن.", "is_active": 1, "win_rate": 83.5, "weight": 1.8, "risk_level": "متوسط", "icon": "clock", "timeframe_default": "M5"},

    # 3. Price Action & Smart Money (8 Strategies)
    {"id": "strat_sr_breakout", "name": "Support & Resistance Breakout", "title_fa": "شکست سطوح کلیدی حمایت و مقاومت", "category": "پرایس اکشن", "description_fa": "ورود در شکست معتبر سقف یا کف ۳۰ کندل اخیر با تایید حجم.", "is_active": 1, "win_rate": 76.0, "weight": 1.5, "risk_level": "متوسط", "icon": "layers", "timeframe_default": "M15"},
    {"id": "strat_order_block_smc", "name": "SMC Order Block Retest", "title_fa": "اوردر بلاک اسمارت مانی (SMC)", "category": "پرایس اکشن", "description_fa": "ورود در پولبک به بیس سفارشات نهادی اوردر بلاک در تایم‌فریم ۱ ساعته.", "is_active": 1, "win_rate": 86.0, "weight": 2.0, "risk_level": "کم", "icon": "box", "timeframe_default": "H1"},
    {"id": "strat_fvg_imbalance", "name": "Fair Value Gap Imbalance (FVG)", "title_fa": "شکاف ارزش منصفانه (FVG)", "category": "پرایس اکشن", "description_fa": "پر شدن گپ‌های نقدینگی ۳ کندلی اسمارت مانی و ادامه جهت روند.", "is_active": 1, "win_rate": 84.5, "weight": 1.8, "risk_level": "کم", "icon": "align-justify", "timeframe_default": "M15"},
    {"id": "strat_liquidity_sweep", "name": "Liquidity Sweep & Reversal", "title_fa": "شکار نقدینگی و بازگشت شتابدار", "category": "پرایس اکشن", "description_fa": "جمع‌آوری استاپ‌های بالا/پایین سقف‌های برابر و چرخش سریع قیمت.", "is_active": 1, "win_rate": 85.0, "weight": 2.0, "risk_level": "کم", "icon": "crosshair", "timeframe_default": "M15"},
    {"id": "strat_market_structure_shift", "name": "Market Structure Shift (MSS/CHoCH)", "title_fa": "تغییر ساختار بازار (MSS / CHoCH)", "category": "پرایس اکشن", "description_fa": "شکست سقف یا کف ساختاری معتبر و تایید تغییر جهت فاز بازار.", "is_active": 1, "win_rate": 83.0, "weight": 1.8, "risk_level": "کم", "icon": "shuffle", "timeframe_default": "H1"},
    {"id": "strat_pinbar_rejection", "name": "Pin Bar & Level Rejection", "title_fa": "پین‌بار و ریجکشن از سطوح کلیدی", "category": "پرایس اکشن", "description_fa": "کندل‌های با سایه بلند نشان‌دهنده عدم پذیرش قیمت در حمایت/مقاومت.", "is_active": 1, "win_rate": 78.0, "weight": 1.2, "risk_level": "متوسط", "icon": "pin", "timeframe_default": "H1"},
    {"id": "strat_supply_demand_zones", "name": "Supply & Demand Zone Reaction", "title_fa": "زون‌های عرضه و تقاضا (Supply/Demand)", "category": "پرایس اکشن", "description_fa": "ورود در نواحی انباشت سفارشات دست‌نخورده عرضه و تقاضا.", "is_active": 1, "win_rate": 82.0, "weight": 1.5, "risk_level": "کم", "icon": "target", "timeframe_default": "H4"},
    {"id": "strat_quasimodo_qml", "name": "Quasimodo Level Reversal (QML)", "title_fa": "الگوی کوازیمودو و سطح QML", "category": "پرایس اکشن", "description_fa": "الگوی پیشرفته بازگشتی پرایس‌اکشن با ساختار HH-LL-LH.", "is_active": 1, "win_rate": 81.5, "weight": 1.5, "risk_level": "متوسط", "icon": "cpu", "timeframe_default": "H1"},

    # 4. Mean Reversion & Volatility (6 Strategies)
    {"id": "strat_bollinger_reversion", "name": "Bollinger Bands Mean Reversion", "title_fa": "باندهای بولینگر و بازگشت به میانگین", "category": "نوسان‌گیری", "description_fa": "خرید در باند پایینی و فروش در باند بالایی در فازهای رنج بازار.", "is_active": 1, "win_rate": 73.0, "weight": 1.0, "risk_level": "کم", "icon": "git-commit", "timeframe_default": "M15"},
    {"id": "strat_rsi_extreme_reversion", "name": "RSI Extreme Oversold/Overbought (10/90)", "title_fa": "بازگشت از اشباع شدید RSI (۱۰/۹۰)", "category": "نوسان‌گیری", "description_fa": "ورود سریع هنگام رسیدن RSI به سطوح بیش از حد فشرده ۱۰ یا ۹۰.", "is_active": 1, "win_rate": 77.5, "weight": 1.5, "risk_level": "متوسط", "icon": "activity", "timeframe_default": "M15"},
    {"id": "strat_atr_volatility_bands", "name": "ATR Volatility Expansion Channel", "title_fa": "کانال‌های انبساط نوسان ATR", "category": "نوسان‌گیری", "description_fa": "معامله در جهت جهش‌های بزرگ نوسانی با شاخص ATR.", "is_active": 1, "win_rate": 74.0, "weight": 1.0, "risk_level": "متوسط", "icon": "bar-chart-2", "timeframe_default": "H1"},
    {"id": "strat_std_dev_channel", "name": "2-Sigma Standard Deviation Channel", "title_fa": "کانال انحراف معیار ۲ سیگما", "category": "نوسان‌گیری", "description_fa": "بازگشت قیمت از دو انحراف معیار آماری به خط تعادل مرکزی.", "is_active": 1, "win_rate": 75.0, "weight": 1.2, "risk_level": "کم", "icon": "sliders", "timeframe_default": "M15"},
    {"id": "strat_kdj_oscillator", "name": "KDJ Momentum Swing Oscillation", "title_fa": "نوسان‌گیر مومنتوم KDJ", "category": "نوسان‌گیری", "description_fa": "سیگنال نوسانی تقاطع خطوط K و D با خط J در محدوده‌های افراطی.", "is_active": 1, "win_rate": 73.5, "weight": 1.0, "risk_level": "متوسط", "icon": "activity", "timeframe_default": "M15"},
    {"id": "strat_williams_r_extreme", "name": "Williams %R Dynamic Range Reversal", "title_fa": "اشباع شاخص ویلیامز (%R)", "category": "نوسان‌گیری", "description_fa": "ورود در نقاط بازگشت خط درصد ویلیامز از سطوح -۲۰ و -۸۰.", "is_active": 1, "win_rate": 74.0, "weight": 1.0, "risk_level": "متوسط", "icon": "refresh-ccw", "timeframe_default": "M15"},

    # 5. Oscillators & Divergences (6 Strategies)
    {"id": "strat_rsi_divergence", "name": "RSI Classic & Hidden Divergence", "title_fa": "واگرایی کلاسیک و مخفی RSI", "category": "واگرایی‌ها", "description_fa": "شناسایی ضعف مومنتوم در قله‌ها و دره‌های قیمتی با تایید واگرایی RSI.", "is_active": 1, "win_rate": 79.5, "weight": 1.8, "risk_level": "متوسط", "icon": "activity", "timeframe_default": "H1"},
    {"id": "strat_macd_hist_divergence", "name": "MACD Histogram Divergence", "title_fa": "واگرایی میله‌های هیستوگرام MACD", "category": "واگرایی‌ها", "description_fa": "کاهش حجم هیستوگرام MACD همراه با ایجاد سقف‌های جدید در قیمت.", "is_active": 1, "win_rate": 78.0, "weight": 1.5, "risk_level": "متوسط", "icon": "bar-chart-2", "timeframe_default": "M15"},
    {"id": "strat_cci_divergence", "name": "CCI Commodity Channel Divergence", "title_fa": "واگرایی کانال کالا (CCI)", "category": "واگرایی‌ها", "description_fa": "واگرایی معتبر شاخص CCI در خروج از باند +۱۰۰ یا -۱۰۰.", "is_active": 1, "win_rate": 75.0, "weight": 1.2, "risk_level": "متوسط", "icon": "trending-down", "timeframe_default": "H1"},
    {"id": "strat_multi_oscillator_confluence", "name": "RSI + Stoch + CCI Triple Confluence", "title_fa": "تلاقی همزمان ۳ نوسانگر (RSI+Stoch+CCI)", "category": "واگرایی‌ها", "description_fa": "سیگنال فوق‌العاده قوی تایید همزمان اشباع و برگشت در ۳ اسیلاتور.", "is_active": 1, "win_rate": 82.0, "weight": 1.8, "risk_level": "کم", "icon": "check-circle", "timeframe_default": "M15"},
    {"id": "strat_volume_delta_divergence", "name": "Volume Delta vs Price Divergence", "title_fa": "واگرایی دلتای حجم معاملات", "category": "واگرایی‌ها", "description_fa": "افزایش قیمت همراه با کاهش حجم واقعی تیکت‌ها که خبر از برگشت می‌دهد.", "is_active": 1, "win_rate": 80.0, "weight": 1.5, "risk_level": "متوسط", "icon": "pie-chart", "timeframe_default": "M5"},
    {"id": "strat_ao_twin_peaks", "name": "Awesome Oscillator Twin Peaks", "title_fa": "قله‌های دوقلوی اندیکاتور Awesome", "category": "واگرایی‌ها", "description_fa": "تشکیل دو قله در یک سمت خط صفر اندیکاتور AO با ارتفاع کاهشی.", "is_active": 1, "win_rate": 76.0, "weight": 1.2, "risk_level": "متوسط", "icon": "mountain", "timeframe_default": "H1"},

    # 6. Chart Patterns & Candlesticks (5 Strategies)
    {"id": "strat_double_bottom_top", "name": "Double Bottom / Top (W & M)", "title_fa": "الگوی سقف و کف دوقلو (W و M)", "category": "الگوهای کلاسیک", "description_fa": "ورود در شکست خط گردن الگوهای کلاسیک بازگشتی سقف و کف دوقلو.", "is_active": 1, "win_rate": 77.0, "weight": 1.4, "risk_level": "متوسط", "icon": "grid", "timeframe_default": "H1"},
    {"id": "strat_head_and_shoulders", "name": "Head & Shoulders Reversal", "title_fa": "الگوی سر و شانه و خط گردن", "category": "الگوهای کلاسیک", "description_fa": "معامله معتبر در شکست خط گردن الگوی سر و شانه مستقیم و معکوس.", "is_active": 1, "win_rate": 78.5, "weight": 1.5, "risk_level": "متوسط", "icon": "user", "timeframe_default": "H4"},
    {"id": "strat_price_action_patterns", "name": "Hammer & Engulfing Candlesticks", "title_fa": "الگوهای کندل‌استیک چکش و پوشا", "category": "الگوهای کلاسیک", "description_fa": "تایید الگوهای بازگشتی Hammer, Engulfing و Shooting Star در سطوح معتبر.", "is_active": 1, "win_rate": 76.5, "weight": 1.2, "risk_level": "متوسط", "icon": "bar-chart", "timeframe_default": "H1"},
    {"id": "strat_chart_flags_pennants", "name": "Continuation Flags & Triangles", "title_fa": "الگوهای ادامه‌دهنده پرچم و مثلث", "category": "الگوهای کلاسیک", "description_fa": "ورود در شکست پرچم‌های صعودی/نزولی و مثلث‌های همگرا در جهت روند.", "is_active": 1, "win_rate": 75.5, "weight": 1.2, "risk_level": "متوسط", "icon": "flag", "timeframe_default": "H1"},
    {"id": "strat_harmonic_gartley", "name": "Harmonic Pattern Fibonacci Ratios", "title_fa": "الگوهای هارمونیک و نسبت‌های فیبوناچی", "category": "الگوهای کلاسیک", "description_fa": "نواحی برگشتی PRZ بر اساس نسبت‌های دقیق فیبوناچی ۶۱.۸ و ۷۸.۶ درصد.", "is_active": 1, "win_rate": 78.0, "weight": 1.5, "risk_level": "متوسط", "icon": "git-merge", "timeframe_default": "H1"},

    # 7. Quantitative & AI Systems (4 Strategies)
    {"id": "strat_confluence_5tf", "name": "5TF AI Multi-Timeframe Confluence", "title_fa": "همگرایی ۵ تایم‌فریمی هوش مصنوعی", "category": "هوش مصنوعی و کوانت", "description_fa": "محاسبه همگرایی و اجماع ریاضی حداقل ۴ تایم‌فریم معاملاتی از ۵ تایم‌فریم.", "is_active": 1, "win_rate": 85.5, "weight": 2.0, "risk_level": "کم", "icon": "sparkles", "timeframe_default": "M15"},
    {"id": "strat_stat_arb_pairs", "name": "Statistical Arbitrage & Correlation", "title_fa": "آربیتراژ آماری و همبستگی جفت‌ارزها", "category": "هوش مصنوعی و کوانت", "description_fa": "معامله در انحراف مقطعی همبستگی نمادهای وابسته (طلا و دلار، یورو و فرانک).", "is_active": 1, "win_rate": 81.0, "weight": 1.5, "risk_level": "کم", "icon": "cpu", "timeframe_default": "H1"},
    {"id": "strat_zscore_mean_reversion", "name": "Quant Z-Score Price Spread", "title_fa": "کوانت Z-Score انحراف قیمت از میانگین", "category": "هوش مصنوعی و کوانت", "description_fa": "محاسبه نمره زد آماری و ورود زمانی که قیمت بیش از ۲ انحراف از نرمال فاصله دارد.", "is_active": 1, "win_rate": 79.0, "weight": 1.4, "risk_level": "کم", "icon": "code", "timeframe_default": "M15"},
    {"id": "strat_ml_regime_switch", "name": "Machine Learning Market Regime Switch", "title_fa": "شناساگر یادگیری ماشین رژیم بازار", "category": "هوش مصنوعی و کوانت", "description_fa": "تشخیص خودکار تغییر فاز از روند به رنج با مدل احتمالی چندمتغیره.", "is_active": 1, "win_rate": 83.0, "weight": 1.8, "risk_level": "کم", "icon": "brain", "timeframe_default": "M15"},

    # 8. Risk Management & Fundamental (3 Strategies)
    {"id": "strat_smart_hedging", "name": "Smart Hedging & Overlap Recovery", "title_fa": "هجینگ و همپوشانی معاملات جهت پوشش ریسک", "category": "مدیریت ریسک", "description_fa": "بازگشایی هوشمند پوزیشن‌های معکوس در نقاط پیوت جهت قفل سود و جبران دراداون تا سقف ۱۰ معامله.", "is_active": 1, "win_rate": 88.0, "weight": 2.0, "risk_level": "کم", "icon": "shield-check", "timeframe_default": "M15"},
    {"id": "strat_macro_news_arbitrage", "name": "Macro Economic News Arbitrage", "title_fa": "آربیتراژ اخبار کلان اقتصادی (CPI/NFP)", "category": "فاندامنتال", "description_fa": "ورود در جهت رویدادهای پرنوسان تقویم اقتصادی همراه با بررسی انحراف پیش‌بینی.", "is_active": 1, "win_rate": 78.0, "weight": 1.5, "risk_level": "بالا", "icon": "globe", "timeframe_default": "M15"},
    {"id": "strat_etf_flow_following", "name": "Crypto & Equity ETF Flow Following", "title_fa": "تعقیب جریانات ورودی صندوق‌های ETF", "category": "فاندامنتال", "description_fa": "معامله در جهت ورود یا خروج خالص حجم سرمایه صندوق‌های بزرگ سرمایه‌گذاری.", "is_active": 1, "win_rate": 79.5, "weight": 1.5, "risk_level": "کم", "icon": "dollar-sign", "timeframe_default": "H4"}
]


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def init_db(self):
        """Create tables and apply schema migrations if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Trades History Table with Prediction Tracking & Attribution
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket INTEGER UNIQUE,
                    symbol TEXT NOT NULL,
                    type TEXT NOT NULL,
                    volume REAL NOT NULL,
                    open_price REAL NOT NULL,
                    close_price REAL,
                    sl REAL,
                    tp REAL,
                    profit REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'OPEN',
                    comment TEXT,
                    strategy TEXT DEFAULT 'MANUAL',
                    confidence REAL DEFAULT 0.0,
                    prediction_title TEXT DEFAULT 'تحلیل تکنیکال',
                    prediction_reason TEXT DEFAULT '',
                    prediction_outcome TEXT DEFAULT 'PENDING',
                    accuracy_score REAL DEFAULT 0.0,
                    open_time TEXT,
                    close_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Safe column migrations for existing databases
            existing_cols = [r[1] for r in cursor.execute("PRAGMA table_info(trades)").fetchall()]
            new_columns = [
                ("confidence", "REAL DEFAULT 0.0"),
                ("prediction_title", "TEXT DEFAULT 'تحلیل تکنیکال'"),
                ("prediction_reason", "TEXT DEFAULT ''"),
                ("prediction_outcome", "TEXT DEFAULT 'PENDING'"),
                ("accuracy_score", "REAL DEFAULT 0.0"),
            ]
            for col_name, col_type in new_columns:
                if col_name not in existing_cols:
                    try:
                        cursor.execute(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass

            # 2. Strategies Catalog Table (مرکز ۵۰ استراتژی معاملاتی با ضرایب وزنی)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategies_config (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    title_fa TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description_fa TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    win_rate REAL DEFAULT 75.0,
                    weight REAL DEFAULT 1.0,
                    risk_level TEXT DEFAULT 'متوسط',
                    icon TEXT DEFAULT 'trending-up',
                    timeframe_default TEXT DEFAULT 'M15',
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Safe column migration for weight
            strat_cols = [r[1] for r in cursor.execute("PRAGMA table_info(strategies_config)").fetchall()]
            if "weight" not in strat_cols:
                try:
                    cursor.execute("ALTER TABLE strategies_config ADD COLUMN weight REAL DEFAULT 1.0")
                except Exception:
                    pass

            # Seed or update the 50 strategies catalog
            for s in DEFAULT_STRATEGIES_50:
                cursor.execute("""
                    INSERT INTO strategies_config (id, name, title_fa, category, description_fa, is_active, win_rate, weight, risk_level, icon, timeframe_default)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        title_fa=excluded.title_fa,
                        category=excluded.category,
                        description_fa=excluded.description_fa,
                        win_rate=excluded.win_rate,
                        risk_level=excluded.risk_level,
                        icon=excluded.icon,
                        timeframe_default=excluded.timeframe_default
                """, (s["id"], s["name"], s["title_fa"], s["category"], s["description_fa"], s["is_active"], s["win_rate"], s.get("weight", 1.0), s["risk_level"], s["icon"], s["timeframe_default"]))

            # 3. AI Signals History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT DEFAULT 'OmniRoute-AI',
                    symbol TEXT NOT NULL,
                    timeframe TEXT DEFAULT 'M15',
                    type TEXT NOT NULL,
                    price REAL NOT NULL,
                    sl REAL,
                    tp REAL,
                    confidence REAL,
                    rationale TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. AI Thinking & Decision Audit Trail Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT DEFAULT 'M15',
                    action TEXT NOT NULL,
                    confidence REAL DEFAULT 50.0,
                    thinking_process TEXT NOT NULL,
                    decision_reason TEXT NOT NULL,
                    actions_performed TEXT NOT NULL,
                    market_data TEXT,
                    sl REAL,
                    tp REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 5. Engine State & Resumption Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS engine_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 6. Persistent System & Engine Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. Multi-Session Chat Tables (Isolated Contexts)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("SELECT id FROM chat_sessions WHERE id = 'default'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO chat_sessions (id, title) VALUES ('default', 'گفتگوی اصلی')")

            # 8. Copy Trade Subscriptions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    leader_id INTEGER NOT NULL,
                    leader_name TEXT NOT NULL,
                    auto_copy INTEGER DEFAULT 1,
                    copy_ratio REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 9. AI Communications & Payload Audit Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_type TEXT NOT NULL,
                    symbol TEXT DEFAULT 'EURUSD',
                    timeframe TEXT DEFAULT 'M15',
                    model TEXT DEFAULT 'trader',
                    provider TEXT DEFAULT 'OmniRoute',
                    prompt_sent TEXT NOT NULL,
                    response_received TEXT NOT NULL,
                    parsed_action TEXT DEFAULT 'HOLD',
                    confidence REAL DEFAULT 50.0,
                    latency_ms INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'SUCCESS',
                    error_message TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 10. Multi-Pair Portfolio Configuration Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_pairs_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    title_fa TEXT DEFAULT '',
                    is_enabled INTEGER DEFAULT 1,
                    min_confidence REAL DEFAULT 70.0,
                    lot_size REAL DEFAULT 0.01,
                    timeframe TEXT DEFAULT 'M15',
                    max_spread_pips REAL DEFAULT 2.5,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Seed default 10 major pairs
            default_portfolio_10 = [
                ("EURUSD", "یورو / دلار آمریکا", 1, 70.0, 0.01, "M15"),
                ("GBPUSD", "پوند بریتانیا / دلار", 1, 70.0, 0.01, "M15"),
                ("USDJPY", "دلار آمریکا / ین ژاپن", 1, 75.0, 0.01, "M15"),
                ("USDCHF", "دلار آمریکا / فرانک سوئیس", 1, 70.0, 0.01, "M15"),
                ("AUDUSD", "دلار استرالیا / دلار", 1, 70.0, 0.01, "M15"),
                ("USDCAD", "دلار آمریکا / دلار کانادا", 1, 70.0, 0.01, "M15"),
                ("NZDUSD", "دلار نیوزیلند / دلار", 1, 70.0, 0.01, "M15"),
                ("EURGBP", "یورو / پوند بریتانیا", 1, 75.0, 0.01, "M15"),
                ("XAUUSD", "انس جهانی طلا (Gold)", 1, 75.0, 0.01, "M15"),
                ("BTCUSD", "بیت‌کوین / دلار (Crypto)", 1, 80.0, 0.01, "M15"),
            ]
            for sym, tfa, en, mconf, lot, tf in default_portfolio_10:
                cursor.execute("""
                    INSERT OR IGNORE INTO portfolio_pairs_config (symbol, title_fa, is_enabled, min_confidence, lot_size, timeframe)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sym, tfa, en, mconf, lot, tf))

            conn.commit()

    # --- Strategy Catalog Operations with Weights ---

    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Retrieve all 50 strategies with their active status and weights."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM strategies_config ORDER BY is_active DESC, weight DESC, win_rate DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching strategies: {e}")
            return DEFAULT_STRATEGIES_50

    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """Retrieve only currently active strategies with weight multipliers."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM strategies_config WHERE is_active = 1 ORDER BY weight DESC, win_rate DESC")
                rows = cursor.fetchall()
                if rows:
                    return [dict(row) for row in rows]
                return [s for s in DEFAULT_STRATEGIES_50 if s["is_active"] == 1]
        except Exception as e:
            print(f"Error fetching active strategies: {e}")
            return DEFAULT_STRATEGIES_50

    def toggle_strategy(self, strategy_id: str, is_active: bool) -> bool:
        """Toggle a strategy active or inactive."""
        active_val = 1 if is_active else 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE strategies_config
                    SET is_active = ?, updated_at = ?
                    WHERE id = ?
                """, (active_val, now, strategy_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error toggling strategy {strategy_id}: {e}")
            return False

    def update_strategy_weight(self, strategy_id: str, weight: float) -> bool:
        """Update strategy weight multiplier (e.g. 0.5 to 5.0)."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE strategies_config
                    SET weight = ?, updated_at = ?
                    WHERE id = ?
                """, (max(0.1, min(10.0, float(weight))), now, strategy_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating strategy weight for {strategy_id}: {e}")
            return False

    # --- Quantitative Attribution & Prediction Matrix Operations ---

    def get_symbol_strategy_matrix(self) -> List[Dict[str, Any]]:
        """
        Compute Win Rate, Total Trades, Average Confidence, and Total PnL
        cross-tabulated by Symbol and Strategy/Prediction Title.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        symbol,
                        COALESCE(prediction_title, strategy) as strategy_tag,
                        COUNT(id) as total_trades,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as win_count,
                        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as loss_count,
                        ROUND(AVG(confidence), 1) as avg_confidence,
                        ROUND(SUM(profit), 2) as total_pnl,
                        ROUND(AVG(profit), 2) as avg_pnl
                    FROM trades
                    WHERE status = 'CLOSED'
                    GROUP BY symbol, strategy_tag
                    ORDER BY total_pnl DESC
                """)
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    d = dict(row)
                    total = d["total_trades"]
                    wins = d["win_count"]
                    win_rate = round((wins / total) * 100, 1) if total > 0 else 0.0
                    d["win_rate"] = win_rate
                    d["accuracy_score"] = win_rate
                    d["effectiveness"] = "عالی (High)" if win_rate >= 75 else ("خوب (Moderate)" if win_rate >= 50 else "نیاز به بهینه‌سازی")
                    results.append(d)
                return results
        except Exception as e:
            print(f"Error computing strategy matrix: {e}")
            return []

    def get_pair_performance_breakdown(self) -> List[Dict[str, Any]]:
        """
        Compute performance metrics per currency pair (EURUSD, XAUUSD, BTCUSD, etc.)
        with best-performing strategy recommendation.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        symbol,
                        COUNT(id) as total_trades,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as win_count,
                        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as loss_count,
                        ROUND(AVG(confidence), 1) as avg_confidence,
                        ROUND(SUM(profit), 2) as total_pnl,
                        ROUND(AVG(profit), 2) as avg_pnl
                    FROM trades
                    WHERE status = 'CLOSED'
                    GROUP BY symbol
                    ORDER BY total_pnl DESC
                """)
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    d = dict(row)
                    total = d["total_trades"]
                    wins = d["win_count"]
                    win_rate = round((wins / total) * 100, 1) if total > 0 else 0.0
                    d["win_rate"] = win_rate
                    
                    cursor.execute("""
                        SELECT COALESCE(prediction_title, strategy) as best_strat, SUM(profit) as pnl,
                               COUNT(id) as cnt,
                               ROUND((SUM(CASE WHEN profit > 0 THEN 1.0 ELSE 0.0 END) / COUNT(id)) * 100, 1) as wr
                        FROM trades
                        WHERE symbol = ? AND status = 'CLOSED'
                        GROUP BY best_strat
                        ORDER BY pnl DESC LIMIT 1
                    """, (d["symbol"],))
                    best_row = cursor.fetchone()
                    if best_row:
                        d["best_strategy"] = best_row["best_strat"]
                        d["best_strategy_winrate"] = best_row["wr"]
                        d["recommendation_fa"] = f"برای {d['symbol']} استراتژی «{best_row['best_strat']}» با وین‌ریت {best_row['wr']}% بیشترین بازدهی را دارد."
                    else:
                        d["best_strategy"] = "تحلیل تکنیکال استاندارد"
                        d["best_strategy_winrate"] = win_rate
                        d["recommendation_fa"] = f"برای {d['symbol']} سابقه کافی جهت تعیین استراتژی برتر موجود نیست."

                    results.append(d)
                return results
        except Exception as e:
            print(f"Error computing pair breakdown: {e}")
            return []

    def get_predictions_audit_log(self, limit: int = 50, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve full prediction audit log: confidence %, Persian rationale,
        actual outcome (WIN/LOSS), accuracy %, and profit.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if symbol:
                    cursor.execute("""
                        SELECT id, ticket, symbol, type, volume, open_price, close_price, sl, tp, profit,
                               status, strategy, confidence, prediction_title, prediction_reason,
                               prediction_outcome, accuracy_score, open_time, close_time
                        FROM trades
                        WHERE symbol = ?
                        ORDER BY id DESC LIMIT ?
                    """, (symbol, limit))
                else:
                    cursor.execute("""
                        SELECT id, ticket, symbol, type, volume, open_price, close_price, sl, tp, profit,
                               status, strategy, confidence, prediction_title, prediction_reason,
                               prediction_outcome, accuracy_score, open_time, close_time
                        FROM trades
                        ORDER BY id DESC LIMIT ?
                    """, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching prediction audit log: {e}")
            return []

    # --- Trades Operations & Performance Analytics ---

    def record_trade_open(self, ticket: int, symbol: str, trade_type: str, volume: float,
                          open_price: float, sl: Optional[float] = None, tp: Optional[float] = None,
                          comment: str = "", strategy: str = "MANUAL", confidence: float = 75.0,
                          prediction_title: str = "تحلیل تکنیکال", prediction_reason: str = "",
                          open_time: str = "") -> bool:
        """Record or update an open trade with prediction tags and rationale."""
        now = open_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (ticket, symbol, type, volume, open_price, sl, tp, status, comment, strategy,
                                        confidence, prediction_title, prediction_reason, prediction_outcome, accuracy_score, open_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, ?, 'PENDING', 0.0, ?)
                    ON CONFLICT(ticket) DO UPDATE SET
                        sl=excluded.sl,
                        tp=excluded.tp,
                        confidence=excluded.confidence,
                        prediction_title=excluded.prediction_title,
                        prediction_reason=excluded.prediction_reason
                """, (ticket, symbol, trade_type, volume, open_price, sl, tp, comment, strategy,
                      confidence, prediction_title, prediction_reason, now))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording trade: {e}")
            return False

    def record_trade_close(self, ticket: int, close_price: float, profit: float, close_time: str = "") -> bool:
        """Update closed trade parameters with automated outcome and accuracy score calculation."""
        now = close_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        outcome = "WIN" if profit > 0 else ("LOSS" if profit < 0 else "BREAKEVEN")
        accuracy = 100.0 if profit > 0 else (50.0 if profit == 0 else 0.0)

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE trades
                    SET close_price = ?, profit = ?, status = 'CLOSED', close_time = ?,
                        prediction_outcome = ?, accuracy_score = ?
                    WHERE ticket = ?
                """, (close_price, profit, now, outcome, accuracy, ticket))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording trade close: {e}")
            return False

    def get_trades_history(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get history of trades from SQLite."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute("SELECT * FROM trades WHERE status = ? ORDER BY id DESC LIMIT ?", (status, limit))
                else:
                    cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching trades: {e}")
            return []

    def get_ai_trade_insights(self, limit: int = 20) -> Dict[str, Any]:
        """
        Generate AI Post-Trade Journal & Quantitative Performance Insights.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM trades
                    WHERE status = 'CLOSED'
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                if not rows:
                    return {
                        "total_closed": 0,
                        "win_rate": 0.0,
                        "total_pnl": 0.0,
                        "profit_factor": 1.0,
                        "best_pair": "---",
                        "summary_fa": "هنوز معامله بسته‌شده‌ای برای تحلیل ژورنال هوش مصنوعی ثبت نشده است.",
                        "actionable_tips": [
                            "برای فعال‌سازی ژورنال، اجازه دهید اولین معاملات اسکالپ یا اتوماتیک به تارگت برسند.",
                            "در صورت تغییر روند، از قابلیت ریسک‌فری (Break-Even) یک‌کلیکه استفاده کنید."
                        ],
                        "recent_journals": []
                    }

                trades = [dict(r) for r in rows]
                total = len(trades)
                wins = [t for t in trades if t["profit"] > 0]
                losses = [t for t in trades if t["profit"] < 0]
                win_count = len(wins)
                win_rate = round((win_count / total) * 100, 1) if total > 0 else 0.0
                total_pnl = round(sum(t["profit"] for t in trades), 2)
                gross_profit = sum(t["profit"] for t in wins)
                gross_loss = abs(sum(t["profit"] for t in losses))
                profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 1.0)

                # Pair performance
                symbol_pnl = {}
                for t in trades:
                    sym = t["symbol"]
                    symbol_pnl[sym] = symbol_pnl.get(sym, 0.0) + t["profit"]
                best_pair = max(symbol_pnl.items(), key=lambda x: x[1])[0] if symbol_pnl else "EURUSD"

                # Generate Persian Post-Mortem Journals for each trade
                journals = []
                for t in trades[:10]:
                    is_win = t["profit"] > 0
                    pnl_str = f"+{t['profit']:.2f}$" if is_win else f"{t['profit']:.2f}$"
                    journals.append({
                        "ticket": t["ticket"],
                        "symbol": t["symbol"],
                        "type": t["type"],
                        "profit": t["profit"],
                        "pnl_str": pnl_str,
                        "status": t["prediction_outcome"],
                        "strategy": t["prediction_title"] or t["strategy"],
                        "confidence": t["confidence"],
                        "close_time": t["close_time"] or t["created_at"],
                        "lesson_fa": f"معامله {t['symbol']} با سود {pnl_str} بسته شد. مدیریت ریسک مطلوب و پایبندی به تارگت رعایت شد." if is_win else f"معامله {t['symbol']} با زیان {pnl_str} بسته شد. پیشنهاد می‌شود در نوسانات شدید حد ضرر با فاصله ATR تنظیم گردد."
                    })

                summary_fa = f"از میان {total} معامله اخیر، نرخ برد به {win_rate}% و سود خالص به {total_pnl:+.2f}$ رسیده است. بهترین جفت‌ارز بازدهی {best_pair} بوده است."
                actionable_tips = [
                    f"جفت‌ارز {best_pair} بالاترین بازدهی را نشان داده است؛ تمرکز روی این نماد توصیه می‌شود.",
                    "استفاده از تریلینگ استاپ خودکار برای حفظ سودهای بالاتر از ۱۰ پیپ فعال شود.",
                    "در ساعات انتشار اخبار پرریسک، اسپرد را در سقف ۱.۵ پیپ محدود نمایید."
                ]

                return {
                    "total_closed": total,
                    "win_rate": win_rate,
                    "total_pnl": total_pnl,
                    "profit_factor": profit_factor,
                    "best_pair": best_pair,
                    "summary_fa": summary_fa,
                    "actionable_tips": actionable_tips,
                    "recent_journals": journals
                }
        except Exception as e:
            print(f"Error computing AI trade insights: {e}")
            return {
                "total_closed": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "profit_factor": 1.0,
                "best_pair": "---",
                "summary_fa": "خطا در پردازش اطلاعات ژورنال",
                "actionable_tips": [],
                "recent_journals": []
            }

    def get_time_framed_trading_stats(self) -> Dict[str, Any]:
        """
        Compute real-time trading statistics:
        - Last 1 hour (total, wins, win_rate, pnl)
        - Last 24 hours (total, wins, win_rate, pnl)
        - Last 7 days / Week (total, wins, win_rate, pnl)
        - Overall summary
        """
        now = datetime.now()
        ts_1h = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        ts_24h = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        ts_7d = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

        def _calc_stats(cursor, time_filter: Optional[str] = None):
            if time_filter:
                cursor.execute("""
                    SELECT 
                        COUNT(id) as total,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
                        COALESCE(SUM(profit), 0.0) as pnl
                    FROM trades
                    WHERE COALESCE(close_time, created_at, '') >= ?
                """, (time_filter,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(id) as total,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
                        COALESCE(SUM(profit), 0.0) as pnl
                    FROM trades
                """)
            row = cursor.fetchone()
            total = row["total"] or 0
            wins = row["wins"] or 0
            losses = row["losses"] or 0
            pnl = round(float(row["pnl"] or 0.0), 2)
            wr = round((wins / total) * 100, 1) if total > 0 else 0.0
            return {
                "total": total,
                "wins": wins,
                "losses": losses,
                "win_rate": wr,
                "pnl": pnl,
                "formatted": f"{total} معامله ({wins} موفق - {wr}%)" if total > 0 else "۰ معامله (۰ موفق)"
            }

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                return {
                    "last_1h": _calc_stats(cursor, ts_1h),
                    "last_24h": _calc_stats(cursor, ts_24h),
                    "last_7d": _calc_stats(cursor, ts_7d),
                    "all_time": _calc_stats(cursor, None)
                }
        except Exception as e:
            print(f"Error computing time framed stats: {e}")
            empty_stat = {"total": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "pnl": 0.0, "formatted": "۰ معامله (۰ موفق)"}
            return {"last_1h": empty_stat, "last_24h": empty_stat, "last_7d": empty_stat, "all_time": empty_stat}

    def get_performance_summary(self) -> Dict[str, Any]:
        """Compute performance analytics: Win Rate, Profit Factor, Net PnL, Total Trades."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT profit, status, confidence FROM trades WHERE status = 'CLOSED'")
                rows = cursor.fetchall()
                
                total = len(rows)
                if total == 0:
                    return {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0.0,
                        "gross_profit": 0.0,
                        "gross_loss": 0.0,
                        "net_pnl": 0.0,
                        "profit_factor": 0.0,
                        "avg_confidence": 0.0
                    }

                wins = [r["profit"] for r in rows if r["profit"] > 0]
                losses = [abs(r["profit"]) for r in rows if r["profit"] < 0]
                confidences = [r["confidence"] for r in rows if r["confidence"] and r["confidence"] > 0]
                
                gross_profit = sum(wins)
                gross_loss = sum(losses)
                win_count = len(wins)
                loss_count = len(losses)
                win_rate = round((win_count / total) * 100, 1) if total > 0 else 0.0
                profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 1.0)
                net_pnl = round(gross_profit - gross_loss, 2)
                avg_conf = round(sum(confidences) / len(confidences), 1) if confidences else 75.0

                return {
                    "total_trades": total,
                    "winning_trades": win_count,
                    "losing_trades": loss_count,
                    "win_rate": win_rate,
                    "gross_profit": round(gross_profit, 2),
                    "gross_loss": round(gross_loss, 2),
                    "net_pnl": net_pnl,
                    "profit_factor": profit_factor,
                    "avg_confidence": avg_conf
                }
        except Exception as e:
            print(f"Error calculating stats: {e}")
            return {"total_trades": 0, "win_rate": 0.0, "net_pnl": 0.0}

    # --- AI Communication & Audit Log Operations ---

    def record_ai_audit_log(
        self,
        context_type: str,
        prompt_sent: str,
        response_received: str,
        symbol: str = "EURUSD",
        timeframe: str = "M15",
        model: str = "trader",
        provider: str = "OmniRoute",
        parsed_action: str = "HOLD",
        confidence: float = 50.0,
        latency_ms: int = 0,
        status: str = "SUCCESS",
        error_message: str = ""
    ) -> int:
        """Record complete sent prompt, raw LLM response, latency, and status across all contexts."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ai_audit_logs (
                        context_type, symbol, timeframe, model, provider, prompt_sent,
                        response_received, parsed_action, confidence, latency_ms, status,
                        error_message, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    context_type, symbol, timeframe, model, provider, prompt_sent,
                    response_received, parsed_action, confidence, latency_ms, status,
                    error_message, now
                ))
                conn.commit()
                return cursor.lastrowid or 0
        except Exception as e:
            print(f"Error recording AI audit log: {e}")
            return 0

    def get_ai_audit_logs(self, context_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch AI communication logs filtered by context type or all."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if context_type and context_type.lower() != "all":
                    cursor.execute("""
                        SELECT * FROM ai_audit_logs
                        WHERE context_type = ?
                        ORDER BY id DESC LIMIT ?
                    """, (context_type, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM ai_audit_logs
                        ORDER BY id DESC LIMIT ?
                    """, (limit,))
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching AI audit logs: {e}")
            return []

    def get_ai_contexts_summary(self) -> Dict[str, Any]:
        """Return status, total counts, and latest activity timestamp for each context."""
        contexts = {
            "market_analysis": {"title": "تحلیل جامع بازار", "icon": "line-chart", "count": 0, "status": "active", "latest": "---"},
            "scalper": {"title": "اسکالپینگ سریع M1/M5", "icon": "zap", "count": 0, "status": "active", "latest": "---"},
            "chat": {"title": "دستیار گفتگوی هوشمند", "icon": "message-square", "count": 0, "status": "active", "latest": "---"},
            "fleet": {"title": "ناوگان ایجنت‌ها", "icon": "bot", "count": 0, "status": "active", "latest": "---"},
            "news_intel": {"title": "هوش بازار و اخبار کلان", "icon": "newspaper", "count": 0, "status": "active", "latest": "---"},
        }
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT context_type, COUNT(id) as cnt, MAX(created_at) as last_time
                    FROM ai_audit_logs
                    GROUP BY context_type
                """)
                for row in cursor.fetchall():
                    ctx = row["context_type"]
                    if ctx in contexts:
                        contexts[ctx]["count"] = row["cnt"]
                        contexts[ctx]["latest"] = row["last_time"]

                # Also count total logs
                cursor.execute("SELECT COUNT(id) FROM ai_audit_logs")
                total_logs = cursor.fetchone()[0]
                return {"contexts": contexts, "total_logs": total_logs}
        except Exception as e:
            print(f"Error getting AI context summary: {e}")
            return {"contexts": contexts, "total_logs": 0}

    # --- Multi-Pair Portfolio Hub Operations ---

    def get_portfolio_pairs(self) -> List[Dict[str, Any]]:
        """Fetch all configured portfolio pairs ordered by enabled status and id."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM portfolio_pairs_config ORDER BY is_enabled DESC, id ASC")
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching portfolio pairs: {e}")
            return []

    def get_symbol_historical_stats(self, symbol: str) -> Dict[str, Any]:
        """Fetch historical win rate, wins, losses, total PnL, and accuracy for a specific currency pair."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(id) as total_trades,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
                        COALESCE(SUM(profit), 0.0) as total_pnl,
                        AVG(confidence) as avg_confidence
                    FROM trades
                    WHERE UPPER(symbol) = ? AND status = 'CLOSED'
                """, (symbol.upper(),))
                row = cursor.fetchone()
                if row and row["total_trades"] > 0:
                    total = row["total_trades"]
                    wins = row["wins"] or 0
                    losses = row["losses"] or 0
                    wr = round((wins / total) * 100, 1)
                    pnl = round(float(row["total_pnl"]), 2)
                    return {
                        "total_trades": total,
                        "wins": wins,
                        "losses": losses,
                        "win_rate": wr,
                        "total_pnl": pnl,
                        "formatted": f"{wr}% ({wins} برد / {losses} باخت)"
                    }
                else:
                    return {
                        "total_trades": 0,
                        "wins": 0,
                        "losses": 0,
                        "win_rate": 75.0,
                        "total_pnl": 0.0,
                        "formatted": "75.0% (مبنای استراتژی)"
                    }
        except Exception as e:
            print(f"Error fetching symbol stats for {symbol}: {e}")
            return {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 75.0, "total_pnl": 0.0, "formatted": "75.0%"}

    def add_portfolio_pair(self, symbol: str, title_fa: str = "", min_confidence: float = 70.0, lot_size: float = 0.01, timeframe: str = "M15") -> bool:
        """Add a new currency pair to the portfolio hub."""
        sym_clean = symbol.strip().upper()
        title = title_fa.strip() or f"جفت‌ارز {sym_clean}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO portfolio_pairs_config (symbol, title_fa, is_enabled, min_confidence, lot_size, timeframe, created_at)
                    VALUES (?, ?, 1, ?, ?, ?, ?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        title_fa=excluded.title_fa,
                        min_confidence=excluded.min_confidence,
                        lot_size=excluded.lot_size,
                        timeframe=excluded.timeframe,
                        is_enabled=1
                """, (sym_clean, title, min_confidence, lot_size, timeframe, now))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding portfolio pair: {e}")
            return False

    def remove_portfolio_pair(self, symbol: str) -> bool:
        """Remove a currency pair from the portfolio hub."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM portfolio_pairs_config WHERE symbol = ?", (symbol.upper(),))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error removing portfolio pair {symbol}: {e}")
            return False

    def update_portfolio_pair(self, symbol: str, is_enabled: Optional[bool] = None, min_confidence: Optional[float] = None, lot_size: Optional[float] = None, timeframe: Optional[str] = None) -> bool:
        """Update settings, confidence threshold, or enable status for a pair."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                updates = []
                params = []
                if is_enabled is not None:
                    updates.append("is_enabled = ?")
                    params.append(1 if is_enabled else 0)
                if min_confidence is not None:
                    updates.append("min_confidence = ?")
                    params.append(float(min_confidence))
                if lot_size is not None:
                    updates.append("lot_size = ?")
                    params.append(float(lot_size))
                if timeframe is not None:
                    updates.append("timeframe = ?")
                    params.append(str(timeframe))

                if not updates:
                    return True

                params.append(symbol.upper())
                query = f"UPDATE portfolio_pairs_config SET {', '.join(updates)} WHERE symbol = ?"
                cursor.execute(query, tuple(params))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating portfolio pair {symbol}: {e}")
            return False
    def export_trades_csv(self) -> str:
        """Export all trades to CSV format."""
        trades = self.get_trades_history(limit=500)
        output = io.StringIO()
        if trades:
            writer = csv.DictWriter(output, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)
        return output.getvalue()

    # --- Multi-Session Chat Operations ---

    def create_chat_session(self, session_id: str, title: str = "گفتگوی جدید") -> Dict[str, Any]:
        """Create a new chat session with isolated context."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_sessions (id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id) DO NOTHING
                """, (session_id, title, now, now))
                conn.commit()
                return {"id": session_id, "title": title, "created_at": now}
        except Exception as e:
            print(f"Error creating chat session: {e}")
            return {"id": session_id, "title": title}

    def get_chat_sessions(self) -> List[Dict[str, Any]]:
        """List all active chat sessions with message counts."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.id, s.title, s.created_at, s.updated_at, COUNT(m.id) as message_count
                    FROM chat_sessions s
                    LEFT JOIN chat_messages m ON s.id = m.session_id
                    GROUP BY s.id
                    ORDER BY s.updated_at DESC
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching chat sessions: {e}")
            return [{"id": "default", "title": "گفتگوی اصلی", "message_count": 0}]

    def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session and its messages."""
        if session_id == "default":
            return self.clear_chat_messages("default")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting chat session: {e}")
            return False

    def update_chat_session_title(self, session_id: str, title: str) -> bool:
        """Update session title."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?", (title[:40], now, session_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating session title: {e}")
            return False

    def record_chat_message(self, session_id: str, role: str, content: str) -> bool:
        """Save chat conversation message to a specific session."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO chat_sessions (id, title, updated_at) VALUES (?, 'گفتگو', ?) ON CONFLICT(id) DO UPDATE SET updated_at = ?", (session_id, now, now))
                cursor.execute("INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)", (session_id, role, content, now))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording chat message: {e}")
            return False

    def get_chat_messages(self, session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve message history for a specific session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, session_id, role, content, created_at
                    FROM chat_messages
                    WHERE session_id = ?
                    ORDER BY id ASC
                    LIMIT ?
                """, (session_id, limit))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching chat messages for {session_id}: {e}")
            return []

    def clear_chat_messages(self, session_id: str) -> bool:
        """Clear all messages in a session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing chat messages: {e}")
            return False

    # --- AI Decisions & Thinking Trail Operations ---

    def record_ai_decision(self, symbol: str, timeframe: str, action: str, confidence: float,
                           thinking_process: str, decision_reason: str, actions_performed: List[str] | str,
                           market_data: Optional[Dict[str, Any]] = None, sl: Optional[float] = None,
                           tp: Optional[float] = None) -> bool:
        """Record detailed AI thinking process, executed actions, and decision rationale."""
        actions_str = json.dumps(actions_performed, ensure_ascii=False) if isinstance(actions_performed, list) else str(actions_performed)
        market_str = json.dumps(market_data or {}, ensure_ascii=False) if market_data else "{}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ai_decisions (symbol, timeframe, action, confidence, thinking_process, decision_reason, actions_performed, market_data, sl, tp, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, timeframe, action, confidence, thinking_process, decision_reason, actions_str, market_str, sl, tp, now))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording AI decision: {e}")
            return False

    def get_ai_decisions(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Retrieve recent AI decisions with full thinking chain and action logs."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ai_decisions ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    d = dict(row)
                    try:
                        d["actions_performed"] = json.loads(d["actions_performed"])
                    except Exception:
                        d["actions_performed"] = [d["actions_performed"]] if d["actions_performed"] else []
                    try:
                        d["market_data"] = json.loads(d["market_data"])
                    except Exception:
                        d["market_data"] = {}
                    results.append(d)
                return results
        except Exception as e:
            print(f"Error fetching AI decisions: {e}")
            return []

    # --- Signals Operations ---

    def record_signal(self, symbol: str, signal_type: str, price: float,
                      confidence: float = 75.0, sl: Optional[float] = None, tp: Optional[float] = None,
                      rationale: str = "", agent_name: str = "OmniRoute-AI", timeframe: str = "M15") -> bool:
        """Save AI analysis signal."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO signals (agent_name, symbol, timeframe, type, price, sl, tp, confidence, rationale)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (agent_name, symbol, timeframe, signal_type, price, sl, tp, confidence, rationale))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording signal: {e}")
            return False

    def get_signals_history(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Get signal history from SQLite."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching signals: {e}")
            return []

    # --- Engine State Resumption Operations ---

    def set_state(self, key: str, value: Any) -> bool:
        """Store persistent state key-value."""
        str_val = json.dumps(value) if not isinstance(value, str) else value
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO engine_state (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """, (key, str_val, now))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error setting state: {e}")
            return False

    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve persistent state key-value."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM engine_state WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    try:
                        return json.loads(row["value"])
                    except Exception:
                        return row["value"]
                return default
        except Exception as e:
            print(f"Error getting state: {e}")
            return default

    # --- Logs Operations ---

    def record_log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Store log entry into SQLite."""
        data_str = json.dumps(data) if data else "{}"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO logs (level, message, data) VALUES (?, ?, ?)", (level, message, data_str))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording log: {e}")
            return False

    def get_persistent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve logs from SQLite."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []


db = DatabaseManager()
