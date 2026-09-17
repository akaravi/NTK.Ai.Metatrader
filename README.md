# NTK.Ai.Metatrader (MetaTrader AI)

[![Developer](https://img.shields.io/badge/Developer-Ali%20Karavi-blue.svg)](https://alikaravi.com/)
[![Website](https://img.shields.io/badge/Website-alikaravi.com-green.svg)](https://alikaravi.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

> **Bilingual Documentation / راهنمای دو زبانه**
> - [🇮🇷 راهنمای فارسی (Persian Guide)](#-راهنمای-فارسی-persian)
> - [🇬🇧 English Guide](#-english-guide)

---

## 🇮🇷 راهنمای فارسی (Persian)

### معرفی پروژه
**NTK.Ai.Metatrader** یک دستیار و ایجنت هوشمند معاملاتی مبتنی بر هوش مصنوعی (AI-Powered Trading Assistant) برای پلتفرم‌های **MetaTrader 4** و **MetaTrader 5** است که امکان تحلیل بازار، مدیریت موقعیت‌های معاملاتی، دریافت اخبار و اجرای استراتژی‌های الگوریتمی را با استفاده از مدل‌های زبانی پیشرفته (LLMs) فراهم می‌آورد.

- **توسعه‌دهنده:** [علی کروی (Ali Karavi)](https://alikaravi.com/)
- **وب‌سایت:** [https://alikaravi.com/](https://alikaravi.com/)

---

### منابع و الگوبرداری (Acknowledgments & Inspirations)
این پروژه با الهام، الگوبرداری و بهره‌گیری از معماری پروژه‌های ارزشمند زیر بازطراحی و توسعه یافته است:
1. **[jblanked/metatrader-ai](https://github.com/jblanked/metatrader-ai)** - دستیار هوش مصنوعی متاتریدر و کتابخانه‌های MQL/Python
2. **[HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)** - پلتفرم چندعاملی هوش مصنوعی برای معاملات مالی و تحلیل هوشمند بازار

---

### جدول ویژگی‌ها و قابلیت‌ها

| قابلیت | پایتون (Python) | متاتریدر (MQL) |
| :--- | :---: | :---: |
| کاتالوگ ۵۰ استراتژی نهادی با ضرایب وزن‌دهی سفارشی ($0.5\times$ تا $5.0\times$) | ✅ | — |
| مدل اجماع احتمالات وزنی (Weighted Probability Consensus Model) | ✅ | — |
| موتور تریلینگ استاپ خودکار و ریسک‌فری هوشمند (Automated Trailing Stop & BE) | ✅ | ✅ |
| تیکت ورود فوری اسکالپ با خروج زمان‌محور (۳، ۵، ۱۰، ۱۵ و ۳۰ دقیقه) | ✅ | ✅ |
| چارت زنده تعاملی با سوئیچر خطی و کندل‌استیک شمعی ژاپنی (Chart Mode) | ✅ | — |
| ماتریس پیش‌بینی و اسناد عملکرد استراتژی‌ها بر اساس جفت‌ارز (Prediction Matrix) | ✅ | — |
| ژورنال و بازخورد هوشمند پس از معامله با محاسبه فاکتور سود (AI Debrief) | ✅ | — |
| باز کردن، بستن و ویرایش سریع سفارش‌ها و پوزیشن‌ها (1-Click Modify/BE) | ✅ | ✅ |
| دریافت سوابق معاملات، سفارش‌ها و ذخیره‌سازی پایدار در SQLite | ✅ | ✅ |
| اطلاعات حساب و مشخصات کامل متاتریدر ۵ (Build 6198، لوریج، مسیر داده) | ✅ | ✅ |
| بیش از ۲۰ اندیکاتور تکنیکال (EMA 9/21/50, RSI, ATR, VWAP, Support/Resistance) | ✅ | ✅ |
| پایش هوش بازار، جریانات ورودی/خروجی ETF و اخبار اقتصاد کلان (Market Intel) | ✅ | — |
| تقویم اقتصادی رویدادهای پرنوسان با شمارش معکوس زنده (High-Impact Calendar) | ✅ | — |
| ناوگان ایجنت‌های هوشمند چندعاملی (Multi-Agent Fleet & Signals Feed) | ✅ | — |
| سیستم چت چندنشستی با ایزولاسیون مکالمات و قابلیت کپی/ارسال مجدد | ✅ | ✅ |
| مهارت‌های ایجنت‌ها (Tradesync, Polymarket, Heartbeat, ai4trade) | ✅ | — |
| روتر هوش مصنوعی OmniRoute و انواع مدل‌ها با فال‌بک تکنیکال فارسی | ✅ | ✅ |
| ساخت اکسپرت، اندیکاتور و اسکریپت با دستور متنی | — | ✅ |
| وظایف زمان‌بندی‌شده (Cron jobs / Schedule) | ✅ | ✅ |
| اجرای زیر‌عامل‌های هوشمند (Sub-agents) | ✅ | ✅ |

### پیش‌نیازها
- سیستم‌عامل ویندوز (برای پایتون، ارتباط با MT5 نیاز به ویندوز دارد؛ کدهای MQL روی تمام نسخه‌های پشتیبانی‌شده متاتریدر اجرا می‌شوند).
- متاتریدر ۵ و پایتون ۳.۹.۷ یا بالاتر برای ماژول پایتون.
- متاتریدر ۴ یا متاتریدر ۵ برای ماژول MQL.

---

### راهنمای نصب

#### ۱. نصب ماژول پایتون (Python)

```bash
# نصب پکیج
pip install .
# یا در حالت توسعه:
pip install -e python
```

همچنین می‌توانید پیش‌نیازها را از طریق فایل `requirements.txt` نصب کنید:
```bash
pip install -r python/requirements.txt
```

#### ۲. نصب در متاتریدر (MQL)

> [!TIP]
> اگر می‌خواهید سریع شروع کنید، فایل کامپایل‌شده `mql/app.ex5` را در پوشه `Experts` متاتریدر ۵ خود کپی کرده و از پنل Navigator آن را روی چارت اجرا نمایید.

جهت استفاده از کدهای منبع در متاتریدر:
1. از منوی متاتریدر مسیر **File → Open Data Folder** را انتخاب کنید.
2. وارد پوشه `MQL5/Include` (یا `MQL4/Include`) شوید.
3. این مخزن را در این مسیر کلون کرده یا کپی نمایید:
```bash
git clone https://github.com/jblanked/metatrader-ai.git NTK.Ai.Metatrader
```

---

### نحوه استفاده

#### ۱. نسخه تحت وب (Web UI Dashboard) - دسترسی آسان در مرورگر

پروژه به صورت کامل **تحت وب (Web-based)** پیاده‌سازی شده است تا بتوانید به راحتی در مرورگر وب خروجی‌ها، گفتگو با هوش مصنوعی و اطلاعات حساب را مشاهده کنید:

```bash
python web_app.py
```
سپس آدرس زیر را در مرورگر باز کنید:
👉 **http://127.0.0.1:8000**

#### ۲. نسخه رابط گرافیکی دسکتاپ (Desktop GUI)

```bash
python app.py
```

در هر دو نسخه وب و دسکتاپ، صفحه تنظیمات کامل بدون نیاز به فایل کانفیگ در دسترس شماست.
#### ۲. اجرای تک‌مرحله‌ای (One-shot)

### قابلیت‌های سازمانی و ماژول‌های پیشرفته (Institutional-Grade Modules)

#### ۱. کاتالوگ ۵۰ استراتژی نهادی و مدل اجماع وزنی
سیستم مجهز به ۵۰ استراتژی کلاسیک و مدرن معاملاتی در ۸ دسته (پرایس اکشن SMC/ICT، تعقیب روند، شکست سطوح، الگوهای هارمونیک، واگرایی‌ها، هوش مصنوعی/کوانت، میانگین متحرک‌ها و اسکالپینگ سشن‌ها) با ضرایب وزنی پویا ($0.5\times$ تا $5.0\times$) است:
$$\text{Buy Probability} = \frac{\sum_{\text{BUY}} (P_i \times w_i)}{\sum w_i} \quad , \quad \text{Sell Probability} = \frac{\sum_{\text{SELL}} (P_i \times w_i)}{\sum w_i}$$

#### ۲. موتور تریلینگ استاپ و ریسک‌فری خودکار (Automated Trailing Stop & BE)
اسکن پیوسته و غیرمسدودکننده معاملات باز با قابلیت ارتقای خودکار حد ضرر (SL) در سود با گام‌های مشخص و ریسک‌فری یک‌کلیکه (`[BE]`).

#### ۳. سوئیچر چارت زنده شمعی ژاپنی و خطی (Interactive Chart Switcher)
امکان تغییر آنی نمای قیمت بین چارت خطی با میانگین‌های متحرک EMA 9/21 و چارت شمعی ژاپنی (Candlestick) با رنگ‌بندی صعودی و نزولی.

#### ۴. تیکت اسکالپینگ سریع با خروج زمان‌محور (Time-Based Auto-Exit)
ورود سریع در تایم‌فریم‌های یک‌دقیقه‌ای (M1) با تعیین زمان ماندگاری مجاز (۳، ۵، ۱۰، ۱۵ و ۳۰ دقیقه) و ناظر خروج خودکار در قیمت لحظه‌ای پس از اتمام زمان.

#### ۵. ژورنال و تحلیل هوشمند معاملات هوش مصنوعی (AI Post-Trade Journal)
محاسبه خودکار وین‌ریت، سود ناخالص، فاکتور سود ($\text{Profit Factor} = \frac{\sum \text{Gross Profit}}{|\sum \text{Gross Loss}|}$) و ارائه نکات استراتژیک فارسی جهت بهبود عملکرد.

#### ۶. تفکیک درصدی استراتژی‌ها و مودال تمام‌صفحه
دکمه **«📊 درصد استراتژی‌ها»** و آیکون **`[⛶]`** برای مشاهده شفاف سهم، وزن و درصد احتمال تک‌تک ۵۰ استراتژی در تصمیم معاملاتی جاری.

```python
from metatrader_ai.agent import run

response = run(
    api_key="کلید_ای_پی_ای_شما",
    account_login=12345678,
    account_password="رمز_عبور_حساب",
    broker_server_name="نام_سرور_بروکر",
    prompt="بالاترین قیمت امروز نماد ETHUSD چقدر بوده است؟",
)
print(response)
```

#### ۳. اجرای کلاس چندمرحله‌ای (Multi-turn API)

```python
from metatrader_ai.agent import Agent

agent = Agent(
    api_key="کلید_ای_پی_ای_شما",
    account_login=12345678,
    account_password="رمز_عبور_حساب",
    broker_server_name="نام_سرور_بروکر",
)
response = agent.run("لیست پوزیشن‌های باز مرا نمایش بده.")
print(response)
```

#### ۴. خط فرمان (CLI)

```bash
metatrader-ai \
   --api-key "$DEEPSEEK_API_KEY" \
   --account-login "$ACCOUNT_LOGIN" \
   --account-pass "$ACCOUNT_PASS" \
   --broker-name "$BROKER_NAME" \
   --provider deepseek
```

اجرای مستقیم یک دستور متنی:
```bash
metatrader-ai --prompt "اطلاعات حساب را نمایش بده" ...
```

#### ۵. استفاده در MQL (داخل اسکریپت یا اکسپرت)

```c++
#include <NTK.Ai.Metatrader/mql/agent.mqh>

void OnStart()
{
   Agent *agent = new Agent(
      "کلید_ای_پی_ای_شما",            // API Key
      LLM_PROVIDER_DEEPSEEK,        // ارائه‌دهنده پیش‌فرض
      LLM_MODEL_DEEPSEEK_V4_FLASH   // مدل انتخابی
   );
   string response = agent.run("وضعیت مارجین و بالانس حساب را بررسی کن.");
   Print("[AI Agent] ", response);
   delete agent;
}
```

---

### ارتباط و توسعه اختصاصی
جهت سفارشی‌سازی، پیاده‌سازی استراتژی‌های معاملاتی اختصاصی و توسعه مدل‌های پیشرفته هوش مصنوعی می‌توانید از طریق وب‌سایت رسمی اقدام فرمایید:
- **وب‌سایت:** [https://alikaravi.com/](https://alikaravi.com/)

---

### سلب مسئولیت مالی (Disclaimer)
معاملات در بازارهای مالی و فارکس شامل ریسک‌های قابل توجهی است و عملکرد گذشته تضمین‌کننده نتایج آینده نیست. این نرم‌افزار صرفاً برای اهداف آموزشی و پژوهشی ارائه شده است و هیچ‌گونه توصیه مالی محسوب نمی‌شود. پیش از تصمیم‌گیری برای سرمایه‌گذاری، تحقیقات لازم را انجام دهید. علی کروی و توسعه‌دهندگان این پروژه هیچ مسئولیتی در قبال سود یا زیان ناشی از استفاده از این نرم‌افزار بر عهده نمی‌گیرند.

---

## 🇬🇧 English Guide

### Overview
**NTK.Ai.Metatrader** is an AI-powered trading assistant and multi-agent framework for **MetaTrader 4** and **MetaTrader 5**, enabling traders to integrate advanced Large Language Models (LLMs) directly into their market analysis, position execution, and automated trading workflows.

- **Developer:** [Ali Karavi](https://alikaravi.com/)
- **Website:** [https://alikaravi.com/](https://alikaravi.com/)

---

### Acknowledgments & Inspiration
This project is inspired by, adapted from, and builds upon concepts and code from:
1. **[jblanked/metatrader-ai](https://github.com/jblanked/metatrader-ai)** - MetaTrader AI assistant and MQL/Python toolsets.
2. **[HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)** - AI-Trader: Multi-agent AI framework for financial trading and market intelligence.

---

### Features Comparison

| Feature | Python | MQL |
|---------|:------:|:---:|
| 50 Institutional Trading Strategies Catalog with custom weights ($0.5\times$ to $5.0\times$) | ✅ | — |
| Weighted Probability Consensus Model | ✅ | — |
| Automated Trailing Stop Loss & Smart Break-Even Engine | ✅ | ✅ |
| Instant Micro-Scalp Ticket with Time-Based Auto-Exit (3, 5, 10, 15, 30 min) | ✅ | ✅ |
| Interactive Live Chart with Candlestick & Line Switcher + Indicators | ✅ | — |
| Prediction Attribution Matrix & Quant Analytics by Pair | ✅ | — |
| AI Post-Trade Journal & Debrief with Profit Factor & Win Rate | ✅ | — |
| 1-Click Position Modify, Break-Even [BE], and Close-All Operations | ✅ | ✅ |
| Persistent SQLite database layer (`ntk_trader.db`) | ✅ | ✅ |
| Full Web UI Dashboard with sub-second WebSocket tick streaming | ✅ | — |
| Market Intel, Macro Economic Regime Signals, and ETF Inflow Tracking | ✅ | — |
| High-Impact Economic Calendar with Live Countdowns | ✅ | — |
| Multi-Session AI Chat with Context Isolation, Message Copy & Resend | ✅ | ✅ |
| Multi-Agent Signal Fleet & Automated Engines (Auto-Trader & Micro-Scalper) | ✅ | — |
| OmniRoute AI Router & Models with Rule-Based Technical Fallback | ✅ | ✅ |
| 20+ Technical Indicators (EMA 9/21/50, RSI, ATR, Support/Resistance) | ✅ | ✅ |
| Create expert advisors, indicators, and scripts | — | ✅ |
| Cron jobs (schedule tasks) | ✅ | ✅ |
| Launch sub-agents | ✅ | ✅ |
---

### Requirements
- Windows operating system (for Python integration with MetaTrader 5; MQL runs on any OS supported by MetaTrader).
- MetaTrader 5 and Python 3.9.7 or higher for Python integration.
- MetaTrader 4 or MetaTrader 5 for MQL integration.

---

### Installation

#### Python

```bash
pip install .
# Or install in editable mode:
pip install -e python
```

Install dependencies:
```bash
pip install -r python/requirements.txt
```

#### MQL

> [!WARNING]
> If you just want to run the pre-built expert, copy `mql/app.ex5` into your MetaTrader 5 `Experts` directory and attach it to a chart from the Navigator panel.

To set up the MQL source code:
1. In MetaTrader, click **File → Open Data Folder**.
2. Open `MQL5/Include` (or `MQL4/Include`).
3. Clone or copy this repository into the Include directory:
```bash
git clone https://github.com/jblanked/metatrader-ai.git NTK.Ai.Metatrader
```

---

### Usage


#### Web UI Dashboard & Real-Time Trading Terminal

Run the institutional web dashboard with real-time WebSocket tick streaming:
```bash
python web_app.py
```
Open **http://127.0.0.1:8000** in your browser.

### Institutional-Grade Modules

1. **50 Institutional Trading Strategies Catalog & Weighted Consensus:**
   Covers 8 specialized categories (Price Action, Smart Money SMC/ICT, Trend Following, Breakouts, Harmonic Patterns, Divergences, AI/Quant, Session Scalping) with custom weight multipliers ($0.5\times$ to $5.0\times$) and consensus probability modeling.
2. **Automated Trailing Stop Loss & Smart Break-Even Engine:**
   Background non-blocking polling engine that trails stop losses in profit and automatically locks in risk-free Break-Even stops.
3. **Interactive Candlestick & Line Chart Switcher:**
   Instant toggle between smooth line charts with EMA overlays and color-coded Japanese Candlestick bars.
4. **Micro-Scalping Ticket with Time-Based Auto-Exit:**
   Precision M1 entries with configurable maximum holding times (3, 5, 10, 15, 30 min) and automated market close watchers.
5. **AI Post-Trade Journal & Quantitative Debrief:**
   Automatic post-trade insights, Profit Factor calculation, and Persian performance optimization tips.
6. **Strategy Probability Breakdown & Full Modal Matrix:**
   Inline toggle and full-screen modal showing the exact probability percentage, signal direction, and weight contribution of each strategy.

#### Desktop GUI & In-App Settings (Python)

The application includes an **in-app Settings Tab**, allowing full configuration of MetaTrader and AI credentials without needing manual configuration files:

```bash
python app.py
```

Through the Settings UI, you can easily configure:
- MetaTrader 5 Account Login, Password, and Broker Server Name
- AI Provider (DeepSeek, OpenAI, Anthropic, Local) and API Key
- Custom Model name & custom API endpoint URL
- Click **Save & Connect** to connect MT5 and start chatting directly.

You can also launch it programmatically:

```python
from metatrader_ai.app import launch

launch()
```
#### One-shot Function

```python
from metatrader_ai.agent import run

result = run(
    api_key="YOUR_API_KEY",
    account_login=12345678,
    account_password="YOUR_PASSWORD",
    broker_server_name="YOUR_BROKER_SERVER",
    prompt="What is the daily high of ETHUSD?",
)
print(result)
```

#### Multi-turn Class API

```python
from metatrader_ai.agent import Agent

agent = Agent(
    api_key="YOUR_API_KEY",
    account_login=12345678,
    account_password="YOUR_PASSWORD",
    broker_server_name="YOUR_BROKER_SERVER",
)
response = agent.run("Show my open positions.")
print(response)
```

#### Command Line Interface (CLI)

```bash
metatrader-ai \
   --api-key "$DEEPSEEK_API_KEY" \
   --account-login "$ACCOUNT_LOGIN" \
   --account-pass "$ACCOUNT_PASS" \
   --broker-name "$BROKER_NAME" \
   --provider deepseek
```

Single prompt execution:
```bash
metatrader-ai --prompt "Show account info" ...
```

#### MQL (In-Editor / Expert Advisors)

```c++
#include <NTK.Ai.Metatrader/mql/agent.mqh>

void OnStart()
{
   Agent *agent = new Agent(
      "YOUR_API_KEY",               // API key
      LLM_PROVIDER_DEEPSEEK,        // Provider
      LLM_MODEL_DEEPSEEK_V4_FLASH   // Model
   );
   string response = agent.run("What is the current equity and balance?");
   Print("[Agent] ", response);
   delete agent;
}
```

---

### Notes & Contact
- **Developer Website:** [https://alikaravi.com/](https://alikaravi.com/)
- Supported LLM providers include DeepSeek, OpenAI, Anthropic, xAI, Local models, and more.
- For best performance, start and log into your MetaTrader 5 terminal prior to running the Python agent.

---

### Disclaimer
Trading and investing involve substantial risk. Past performance is not indicative of future results. This software is provided for educational and informational purposes only and should not be considered financial advice. Always conduct your own research and consult with a certified financial advisor before making any trading decisions. Ali Karavi and contributors are not responsible for any financial losses or damages resulting from the use of this software.
