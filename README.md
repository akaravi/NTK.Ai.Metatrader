# NTK.Ai.Metatrader 🚀

[![Developer](https://img.shields.io/badge/Developer-Ali%20Karavi-007acc.svg?style=for-the-badge&logo=codeforces&logoColor=white)](https://alikaravi.com/)
[![Website](https://img.shields.io/badge/Website-alikaravi.com-2ea44f.svg?style=for-the-badge&logo=safari&logoColor=white)](https://alikaravi.com/)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-3776ab.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MetaTrader 5](https://img.shields.io/badge/MetaTrader-5%20Build%206198+-red.svg?style=for-the-badge&logo=meta&logoColor=white)](https://www.metatrader5.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

> **Bilingual Documentation / راهنمای دو زبانه**
> - [🇮🇷 راهنمای جامع فارسی (Persian Documentation)](#-راهنمای-جامع-فارسی-persian)
> - [🇬🇧 English Comprehensive Guide](#-english-comprehensive-guide)

---

## 🇮🇷 راهنمای جامع فارسی (Persian)

### معرفی پروژه
**NTK.Ai.Metatrader** پلتفرم و دستیار پیشرفته معاملاتی هوش مصنوعی (AI-Powered Quantitative Trading System) است که ارتباط مستقیم، دوطرفه و فوق‌سریع میان **MetaTrader 5 (و MetaTrader 4)**، موتورهای هوش مصنوعی زبانی (LLMs مانند OmniRoute, OpenAI, DeepSeek, Claude) و یک کاتالوگ گسترده از **۵۰ استراتژی کمی و نهادی** برقرار می‌سازد.

این سیستم با معماری مدرن، دشبورد وب فوق‌پاسخگو (FastAPI + WebSockets)، پایگاه داده محلی پایدار SQLite و کدهای بومی MQL5، فرآیند تحلیل بازار، تصمیم‌گیری الگوریتمی، ورود و خروج، مدیریت ریسک پویا، اسکالپینگ با خروج زمان‌محور و نظارت مستمر بر پوزیشن‌ها را به صورت خودکار و نیمه‌خودکار فراهم می‌کند.

- **توسعه‌دهنده:** [علی کروی (Ali Karavi)](https://alikaravi.com/)
- **وب‌سایت:** [https://alikaravi.com/](https://alikaravi.com/)

---

### معماری کلی سیستم (System Architecture)

```
                     ┌─────────────────────────────────────────────────────────┐
                     │                 OmniRoute / OpenAI / Claude             │
                     │          (LLM Multi-Agent Quantitative Reasoner)        │
                     └────────────────────────────┬────────────────────────────┘
                                                  │  AI Prompts & Confluence
                                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       NTK.Ai.Metatrader Core                                           │
│                                                                                                        │
│   ┌─────────────────────┐    ┌───────────────────────────┐    ┌────────────────────────────────────┐   │
│   │   Strategy Engine   │    │      Trading Engine       │    │            MT5 Service             │   │
│   │  • 50 Quant Strats  │◄──►│  • Auto-Trader Engine     │◄──►│  • Sub-Second Tick Streamer        │   │
│   │  • Weighted Voting  │    │  • M1/M5 Micro-Scalper    │    │  • 1-Click Execution & Orders      │   │
│   │  • Dynamic Weights  │    │  • Trailing Stop & BE     │    │  • 20+ Real-Time Indicators        │   │
│   │  • Strategy Matrix  │    │  • AI Position Guard      │    │  • Currency Exposure & Correlation │   │
│   └──────────┬──────────┘    └─────────────┬─────────────┘    └─────────────────┬──────────────────┘   │
│              │                             │                                    │                      │
│              ▼                             ▼                                    ▼                      │
│   ┌────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                             SQLite Persistence Layer (ntk_trader.db)                           │   │
│   │  • Decisions  • Trades  • Debriefs  • Strategy Performance  • Prediction Matrix  • Chat State   │   │
│   └────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              ▲                                                         │
│                                              │ State & Live Bus                                        │
│                                              ▼                                                         │
│   ┌────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                       FastAPI Web Dashboard & High-Speed WebSocket Server                      │   │
│   │  • Interactive Candle/Line Chart  • 1-Click Position Ops  • Economic Calendar  • AI Debrief     │   │
│   └────────────────────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────┬─────────────────────────────────────────────────────────┘
                                               │ IPC / Network Bridge
                                               ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              MetaTrader 5 Terminal / MQL5 Native EA                                    │
│   • app.mq5 (Live Trading Expert Advisor)       • Tools (Indicators, Chart-Draw, Panel, Backtesting)   │
│   • TesterCache (fxsaber MultiTester)           • LLM / Session Bridge (session.mqh, llm.mqh)          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### جدول مقایسه قابلیت‌ها

| قابلیت و ابزار | ماژول پایتون (Python) | ماژول متاتریدر (MQL5) |
| :--- | :---: | :---: |
| **کاتالوگ ۵۰ استراتژی نهادی** با اوزان سفارشی ($0.5\times$ تا $5.0\times$) | ✅ | — |
| **مدل اجماع احتمالات وزنی** (Weighted Probability Consensus Model) | ✅ | — |
| **موتور معاملاتی خودکار** (Auto-Trading Engine) بر مبنای کانفلوئنس استراتژی‌ها | ✅ | ✅ |
| **موتور میکرو-اسکالپینگ** (M1/M5 Scalper) با خروج زمان‌محور (۳ تا ۳۰ دقیقه) | ✅ | ✅ |
| **تریلینگ استاپ خودکار و ریسک‌فری هوشمند** (Automated Trailing Stop & BE) | ✅ | ✅ |
| **ناظر هوشمند پوزیشن‌های باز** (AI Continuous Position Monitor & Guard) | ✅ | — |
| **چارت زنده تعاملی** با قابلیت سوئیچ بین حالت شمعی (Candlestick) و خطی (Line) | ✅ | — |
| **ماتریس پیش‌بینی و اسناد عملکرد** جفت‌ارزها (Prediction Attribution Matrix) | ✅ | — |
| **ژورنال و بازخورد هوشمند پس از معامله** (AI Post-Trade Debrief) با محاسبه سودآوری | ✅ | — |
| **مدیریت سریع سفارش‌ها و پوزیشن‌ها** (1-Click Modify, Break-Even, Close All) | ✅ | ✅ |
| **بستن یک‌کلیکه معاملات سودده** (Close Profitable Only) | ✅ | ✅ |
| **ماتریس همبستگی نمادها و سنجش ریسک ارزها** (Net Currency Exposure) | ✅ | — |
| **تقویم اقتصادی رویدادهای پرنوسان** با شمارش معکوس زنده | ✅ | — |
| **پایش اخبار اقتصاد کلان و جریانات ETF** (Macro Market Intel) | ✅ | — |
| **سیستم چت چندنشستی هوش مصنوعی** با ایزولاسیون کامل کانتکست و ارسال مجدد | ✅ | ✅ |
| **روتر هوش مصنوعی OmniRoute** با فال‌بک تکنیکال به زبان فارسی | ✅ | ✅ |
| **بیش از ۲۰ اندیکاتور تکنیکال بومی** (EMA 9/21/50/200, RSI, ATR, VWAP, Bollinger, SMC) | ✅ | ✅ |
| **تولید خودکار اکسپرت، اندیکاتور و اسکریپت MQL5** با دستور متنی | — | ✅ |
| **بهینه‌سازی سریع استراتژی‌ها در متاتریدر** با کش فریم‌ورک fxsaber | — | ✅ |

---

### کاتالوگ ۵۰ استراتژی کمی و نهادی (50 Institutional Strategies)

سیستم دارای ۵۰ استراتژی فرمول‌نویسی‌شده و مجزا در ۸ دسته تحلیلی است:

1. **تعقیب روند (Trend Following):**
   - EMA 9/21 Golden Cross، EMA 50/200 Golden/Death Cross، SuperTrend ATR، Triple EMA 8/13/21، ADX Trend Strength، Parabolic SAR، Keltner Channels، Donchian Breakout، Ichimoku Cloud Break، Guppy Multiple Moving Average (GMMA).
2. **اسکالپینگ و مومنتوم سریع (Scalping & Micro-Momentum):**
   - M1/M5 Fast Momentum، VWAP Institutional Scalp، Fast Stochastic 5/3/3، Fast EMA Ribbon Pullback، Order Flow Tick Imbalance، 1-Min Micro Range Breakout، Tick Volume Divergence، London Open Session Breakout.
3. **پرایس‌اکشن و اسمارت مانی (SMC / ICT):**
   - SMC Order Block Retest، Fair Value Gap (FVG)، Liquidity Sweep & Reversal، Market Structure Shift (MSS/CHoCH)، Pin Bar & Level Rejection، Supply & Demand Zones، Quasimodo Level (QML)، Breaker Block Retest.
4. **نوسان‌گیری و بازگشت به میانگین (Mean Reversion & Volatility):**
   - Bollinger Bands Reversion، RSI Extreme Reversion (10/90)، ATR Volatility Expansion، 2-Sigma Standard Deviation Channel، KDJ Swing Oscillation، Williams %R Dynamic Range.
5. **مومنتوم و اسیلاتورها (Momentum & Oscillators):**
   - MACD Histogram Divergence، RSI 14 Trend Momentum، Stochastic RSI Momentum Cross، CCI Extreme Reversal (±200)، Momentum Velocity Chaikin Money Flow (CMF).
6. **الگوهای کلاسیک و هندسی (Chart Patterns & Geometry):**
   - Double Top / Double Bottom، Head & Shoulders Structural، Ascending / Descending Triangle، Bull / Bear Flag Volume Break، Fibonacci Golden Pocket (61.8%-78.6%)، Rectangle Consolidation Range.
7. **کانفلوئنس و چند تایم‌فریمه (Multi-Timeframe & Confluence):**
   - MTF Triple Screen Trend Align، Volume Profile High Volume Node (HVN)، RSI + MACD Dual Confirmation، Moving Average Envelope Squeeze، Multi-Oscillator Heatmap Consensus.
8. **رژیم بازار، سشن‌ها و کلان (Market Regime & Macro):**
   - High-Impact News Filter، New York Session Open Reversal، Asian Session High/Low Liquidity Sweep، Weekend Gap Fill Momentum، Multi-Pair Currency Strength Divergence، Institutional Dark Pool Liquidity Cluster.

---

### موتورهای معاملاتی خودکار و هوشمند

1. **موتور Auto-Trader:** پایش دوره‌ای نمادهای منتخب، تجمیع آرای ۵۰ استراتژی با اعمال اوزان اختصاصی ($0.5\times$ تا $5.0\times$)، محاسبه احتمال وزنی نهایی و صدور خودکار سفارش در صورت عبور از آستانه اطمینان (Confidence Threshold).
2. **موتور Micro-Scalper (M1/M5):** اسکالپینگ پرسرعت روی تایم‌فریم‌های یک و پنج دقیقه با فیلتر اسپرد (حداکثر ۱.۸ پیپ)، تعیین خودکار حد سود و حد ضرر کوتاه (۷ و ۱۲ پیپ) و **خروج زمان‌محور هوشمند** (در صورتی که پس از ۳، ۵، ۱۰ یا ۱۵ دقیقه معامله به هدف نرسد).
3. **موتور Automated Trailing Stop & Break-Even:** رصد لحظه‌ای تیک‌ها، انتقال خودکار حد ضرر به نقطه ورود به همراه بافر (Break-Even) پس از دستیابی به سود معین و تریل کردن استاپ با فاصله مشخص از قیمت روز.
4. **موتور AI Continuous Open Positions Guard:** تحلیل دوره‌ای مجدد پوزیشن‌های باز توسط هوش مصنوعی جهت شناسایی الگوهای بازگشتی خطرناک و هشدار خروج پیش از رسیدن به حد ضرر.
5. **موتور Portfolio Supervisor & Correlation Matrix:** محاسبه خالص ریسک بر اساس ارزهای پایه و جلوگیری از باز شدن پوزیشن‌های هم‌جهت روی جفت‌ارزهای با همبستگی بالا.

---

### راه‌اندازی و نصب گام‌به‌گام (Quickstart Guide)

#### پیش‌نیازها:
- سیستم عامل ویندوز (Windows 10 یا 11).
- متاتریدر ۵ نصب‌شده و در حال اجرا (با فعال بودن گزینه **Algo Trading**).
- پایتون نسخه 3.9.7 یا بالاتر.

#### ۱. کلون و راه‌اندازی محیط مجازی:
```bash
git clone https://github.com/alikaravi/NTK.Ai.Metatrader.git
cd NTK.Ai.Metatrader

python -m venv .venv
# فعال‌سازی در ویندوز:
.venv\Scripts\activate
```

#### ۲. نصب وابستگی‌های پایتون:
```bash
pip install -r python/requirements.txt
```

#### ۳. تنظیم کلیدها و پیکربندی (`settings.json` یا متغیرهای محیطی):
فایل `settings.json` در ریشه پروژه را به صورت زیر پیکربندی نمایید:
```json
{
  "provider": "OmniRoute",
  "custom_url": "https://omniroute.ai.ntk.ir/v1",
  "api_key": "YOUR_OMNIROUTE_OR_OPENAI_API_KEY",
  "custom_model": "trader",
  "account_login": "YOUR_MT5_LOGIN",
  "account_password": "YOUR_MT5_PASSWORD",
  "account_server": "YOUR_BROKER_SERVER",
  "max_open_positions": 10
}
```

#### ۴. اجرای پلتفرم وب و موتورهای هوش مصنوعی:
```bash
python app.py
```
سپس مرورگر خود را باز کرده و به آدرس زیر بروید:
👉 **`http://127.0.0.1:8000`**

---

### نصب و اجرای ماژول MQL5 در MetaTrader 5

1. محتویات پوشه `mql/` را در مسیر `MQL5/Experts/NTK_Ai_Metatrader/` در دایرکتوری داده‌های متاتریدر ۵ کپی کنید.
2. فایل `app.mq5` را در MetaEditor باز کرده و دکمه **Compile (F7)** را بزنید.
3. در ترمینال متاتریدر ۵، از پنل Navigator اکسپرت **app** را به چارت مورد نظر اضافه نمایید.
4. در تنظیمات اکسپرت، گزینه **Allow Algorithmic Trading** و دسترسی‌های WebRequest به آدرس `http://127.0.0.1:8000` را فعال کنید.

---

### مرجع اندپوینت‌های مهم API (RESTful Endpoints)

| متد | مسیر (Route) | توضیحات |
| :--- | :--- | :--- |
| `GET` | `/api/account` | دریافت اطلاعات حساب، موجودی، اکوئیتی و مارجین زنده |
| `GET` | `/api/terminal/status` | وضعیت اتصال به ترمینال MT5 و مجوز الگوتریدینگ |
| `GET` | `/api/symbols` | لیست تمام نمادهای قابل معامله در بروکر |
| `GET` | `/api/symbol/{symbol}/overview` | اطلاعات بید، اسک، اسپرد و مشخصات نماد |
| `GET` | `/api/symbol/{symbol}/technical` | کندل‌ها و ۲۰ اندیکاتور تکنیکال محاسبه‌شده |
| `GET` | `/api/analyze/market/{symbol}` | تحلیل کامل بازار، اجماع ۵۰ استراتژی و نتیجه هوش مصنوعی |
| `GET` | `/api/analyze/confluence/{symbol}` | تحلیل همگرایی تایم‌فریم‌های چندگانه (M1 تا H4) |
| `GET` | `/api/positions` | لیست پوزیشن‌های باز به همراه وضعیت بررسی هوش مصنوعی |
| `POST` | `/api/order/execute` | ثبت سفارش خرید یا فروش با حجم، حد سود و حد ضرر |
| `POST` | `/api/position/{ticket}/close` | بستن فوری یک پوزیشن بر اساس شماره تیکت |
| `POST` | `/api/positions/close-all` | بستن تمام پوزیشن‌های باز حساب یا نماد مشخص |
| `POST` | `/api/positions/close-profitable` | بستن سریع معاملات دارای سود مثبت |
| `POST` | `/api/position/{ticket}/modify` | ویرایش حد سود (TP) و حد ضرر (SL) پوزیشن |
| `POST` | `/api/position/{ticket}/breakeven` | انتقال حد ضرر به نقطه ورود با بافر سفارشی |
| `POST` | `/api/engine/auto-trade/start` | فعال‌سازی موتور معامله خودکار |
| `POST` | `/api/engine/scalp/start` | فعال‌سازی موتور میکرو-اسکالپینگ M1/M5 |
| `POST` | `/api/engine/trailing/start` | فعال‌سازی موتور تریلینگ استاپ و ریسک‌فری |
| `GET` | `/api/strategies/catalog` | کاتالوگ ۵۰ استراتژی با قابلیت تغییر وزن و فعال/غیرفعال‌سازی |
| `POST` | `/api/strategies/optimize` | بهینه‌سازی خودکار اوزان استراتژی‌ها بر اساس عملکرد واقعی |
| `GET` | `/api/portfolio/correlation` | ماتریس همبستگی نمادهای پورتفولیو |
| `GET` | `/api/portfolio/exposure` | خالص ریسک و حجم باز بر اساس هر ارز |
| `GET` | `/api/calendar/high-impact` | تقویم اقتصادی رویدادهای پرنوسان با شمارش معکوس |
| `WS` | `/ws/ticks` | استریم وب‌سوکت تیک‌ها، قیمت زنده و وضعیت معاملات |

---

## 🇬🇧 English Comprehensive Guide

### Project Overview
**NTK.Ai.Metatrader** is an advanced, production-ready AI quantitative trading system and bridge that seamlessly unifies **MetaTrader 5 & MetaTrader 4**, Large Language Models (LLMs via OmniRoute, OpenAI, Claude, DeepSeek), and a robust library of **50 Institutional Quantitative Strategies**.

Built with a high-performance FastAPI backend, real-time WebSocket tick streaming, an embedded responsive Web UI, a local persistent SQLite database, and native MQL5 Expert Advisors, this platform enables automated market analysis, multi-strategy consensus voting, micro-scalping with time-based exits, continuous position surveillance, trailing stop loss automation, and multi-session AI chat with prompt isolation.

- **Author & Developer:** [Ali Karavi](https://alikaravi.com/)
- **Website:** [https://alikaravi.com/](https://alikaravi.com/)
- **License:** [MIT License](LICENSE)

---

### Core Architecture & Technical Highlights

1. **Institutional Strategy Evaluation Engine (`strategy_engine.py`):**
   - 50 mathematically rigorous strategies categorized into 8 distinct quant groups.
   - Dynamic weighting mechanism ($0.5\times$ to $5.0\times$ multiplier).
   - Weighted Probability Consensus Model aggregating individual strategy probabilities into unified market direction signals.

2. **Automated Trading & Execution Engines (`trading_engine.py`):**
   - **Auto-Trader Engine:** Continuous evaluation of selected pairs, triggering automated orders when confidence exceeds specified thresholds.
   - **Micro-Scalper Engine (M1/M5):** Rapid execution targeting 5–15 pips with strict spread checks and **time-based exits** (3, 5, 10, 15, 30 min).
   - **Automated Trailing Stop & Break-Even Engine:** Sub-second tick monitoring that moves stop loss to entry price (BE) with an offset buffer and trails profits dynamically.
   - **AI Position Guard:** Background worker that periodically inspects open trades for adverse reversal patterns and recommends early closure.
   - **Portfolio Risk Supervisor:** Calculates currency exposure and correlation matrices to prevent over-leveraging correlated pairs.

3. **Multi-Model AI Router & Reasoning (`ai_service.py`):**
   - Integrates with OmniRoute, OpenAI, DeepSeek, and Anthropic LLMs.
   - Seamless rule-based Persian/English technical fallback when offline or when latency thresholds are exceeded.
   - Multi-timeframe confluence synthesis (M1, M5, M15, M30, H1, H4, D1).

4. **Persistent SQLite Database Layer (`db.py`):**
   - Full persistence for decisions, executed orders, position events, strategy attribution matrix, historical chat sessions, economic calendar events, and post-trade AI debriefs with profit factor metrics.

5. **MetaTrader 5 High-Speed Service (`mt5_service.py` & `mql/`):**
   - Native Python `MetaTrader5` integration for sub-second quote streaming, order placement, 1-click modifications, and multi-symbol ticks.
   - Complete MQL5 package (`app.mq5`, `tools/`, `session.mqh`, `llm.mqh`, `TesterCache`) for on-chart execution, backtesting, and EA generation.

---

### Repository File Structure

```
NTK.Ai.Metatrader/
│
├── app.py                      # Main application bootstrap & CLI runner
├── web_app.py                  # FastAPI server, WebSocket hub & REST endpoints
├── config.py                   # Pydantic configuration & environment settings
├── db.py                       # SQLite database manager & 50-strategy catalog
├── mt5_service.py              # MetaTrader 5 service, tick streamer & order router
├── ai_service.py               # AI reasoning service & multi-model LLM router
├── strategy_engine.py          # 50 Institutional quantitative strategies engine
├── trading_engine.py           # Auto-trader, micro-scalper, trailing stop & supervisor
├── settings.json               # Local persistent configuration file
├── requirements.txt            # Root dependencies reference
├── LICENSE                     # MIT License
│
├── data/                       # Local SQLite database directory
│   └── ntk_trader.db           # Persistent SQLite database
│
├── static/                     # Web UI static assets
│   ├── css/style.css           # Modern dark-theme stylesheet
│   └── js/app.js               # Reactive frontend client & WebSocket handler
│
├── templates/                  # Frontend HTML templates
│   └── index.html              # Single-page dashboard interface
│
├── python/                     # Core Python package (metatrader_ai)
│   ├── app.py                  # Standalone CLI entrypoint
│   ├── agent.py                # Agent coordinator
│   ├── requirements.txt        # Package requirements
│   ├── pyproject.toml          # Package build configuration
│   └── metatrader_ai/          # Python sub-package
│       ├── agent.py            # Agent class & session management
│       ├── llm.py              # LLM providers (OmniRoute, OpenAI, DeepSeek, Local)
│       ├── cli.py              # CLI argument parser
│       └── tools/              # MT5 tools, dispatchers, build tools
│
├── mql/                        # Native MQL5 Expert Advisors & Libraries
│   ├── app.mq5                 # Main Expert Advisor for MetaTrader 5
│   ├── agent.mqh               # MQL Agent class
│   ├── llm.mqh                 # MQL HTTP WebRequest LLM bridge
│   ├── schedule.mqh            # Task scheduler
│   ├── session.mqh             # Session manager
│   ├── tools/                  # Indicators, Chart-Draw, Panel, Backtesting
│   │   └── fxsaber/            # MultiTester & TesterCache high-speed framework
│   └── tests/                  # MQL test suites
│
├── context/                    # Context files & MQL builder prompt specifications
│   ├── prompt.md               # Base AI prompts
│   ├── trade.md                # Trade rules context
│   ├── mql.md                  # MQL5 reference context
│   └── builder/                # Modular builder context (EA, Indicator, Script, etc.)
│
└── workflows/                  # Agent workflow definitions
    └── response.md             # Standard response schema
```

---

### Quick Installation & Usage

#### 1. Clone & Setup Python Virtual Environment:
```bash
git clone https://github.com/alikaravi/NTK.Ai.Metatrader.git
cd NTK.Ai.Metatrader

python -m venv .venv
# On Windows:
.venv\Scripts\activate
```

#### 2. Install Dependencies:
```bash
pip install -r python/requirements.txt
```

#### 3. Configure Settings (`settings.json`):
```json
{
  "provider": "OmniRoute",
  "custom_url": "https://omniroute.ai.ntk.ir/v1",
  "api_key": "YOUR_API_KEY",
  "custom_model": "trader",
  "account_login": "12345678",
  "account_password": "password",
  "account_server": "Broker-Server",
  "max_open_positions": 10
}
```

#### 4. Launch the Web Platform:
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

### Disclaimer & Risk Warning

Trading financial instruments, forex, commodities, and derivatives involves substantial risk of loss and is not suitable for every investor. Past performance is not indicative of future results. **NTK.Ai.Metatrader** is provided for educational, research, and algorithmic trading assistance purposes only and does not constitute financial advice.

---

### License & Attribution

- Developed by **[Ali Karavi](https://alikaravi.com/)**
- Licensed under the **[MIT License](LICENSE)**.
