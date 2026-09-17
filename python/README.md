# NTK.Ai.Metatrader (MetaTrader AI Python Module)

[![Developer](https://img.shields.io/badge/Developer-Ali%20Karavi-blue.svg)](https://alikaravi.com/)
[![Website](https://img.shields.io/badge/Website-alikaravi.com-green.svg)](https://alikaravi.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

---

> **Bilingual Documentation / راهنمای دو زبانه**
> - [🇮🇷 راهنمای فارسی پایتون](#-راهنمای-فارسی-پایتون-persian)
> - [🇬🇧 English Python Guide](#-english-python-guide)

---

## 🇮🇷 راهنمای فارسی پایتون (Persian)

### معرفی
ماژول پایتون **NTK.Ai.Metatrader** یک پکیج قدرتمند برای اتصال مدل‌های هوش مصنوعی (LLMs مانند DeepSeek و OpenAI) به متاتریدر ۵ است.

- **توسعه‌دهنده:** [علی کروی (Ali Karavi)](https://alikaravi.com/)
- **وب‌سایت:** [https://alikaravi.com/](https://alikaravi.com/)

---

### منابع و الگوبرداری (Inspirations & Credits)
- **[jblanked/metatrader-ai](https://github.com/jblanked/metatrader-ai)**
- **[HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)**

---

### نصب

```bash
pip install -r requirements.txt
pip install -e .
```

### نحوه استفاده

#### ۱. رابط گرافیکی دسکتاپ (Desktop GUI)

```python
from metatrader_ai.app import launch
from metatrader_ai.llm import DEEPSEEK  # یا OPENAI

launch(
    api_key="کلید_ای_پی_ای_شما",
    account_login=12345678,
    account_password="رمز_عبور_حساب",
    broker_server_name="نام_سرور_بروکر",
    model=DEEPSEEK,
)
```

#### ۲. اجرای تک‌مرحله‌ای (One-shot)

```python
from metatrader_ai.agent import run

result = run(
    api_key="کلید_ای_پی_ای_شما",
    account_login=12345678,
    account_password="رمز_عبور_حساب",
    broker_server_name="نام_سرور_بروکر",
    prompt="بالاترین قیمت امروز نماد ETHUSD چقدر بوده است؟",
)
print(result)
```

#### ۳. ایجنت چند مرحله‌ای (Multi-turn API)

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

---

## 🇬🇧 English Python Guide

### Overview
The **NTK.Ai.Metatrader** Python module connects LLM agents with the MetaTrader 5 terminal to automate market queries, trades, and strategy testing.

- **Developer:** [Ali Karavi](https://alikaravi.com/)
- **Website:** [https://alikaravi.com/](https://alikaravi.com/)

---

### Acknowledgments & Inspiration
- **[jblanked/metatrader-ai](https://github.com/jblanked/metatrader-ai)**
- **[HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)**

---

### Installation

```bash
pip install -r requirements.txt
pip install -e .
```

### Quickstart

```python
from metatrader_ai.agent import Agent

agent = Agent(
    api_key="YOUR_API_KEY",
    account_login=12345678,
    account_password="YOUR_PASSWORD",
    broker_server_name="YOUR_BROKER_SERVER",
)
response = agent.run("What is the current equity and open positions?")
print(response)
```

---

### Disclaimer
Trading involves risk. This software is for educational and research purposes. Ali Karavi is not responsible for any trading losses.
