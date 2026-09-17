import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

SETTINGS_FILE = Path("settings.json")


def get_saved_setting(key: str, default_val: str) -> str:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if key in data and data[key]:
                    return str(data[key])
        except Exception:
            pass
    return os.getenv(key, default_val)


class Settings(BaseSettings):
    # OmniRoute AI
    OMNIROUTE_BASE_URL: str = get_saved_setting("custom_url", "https://omniroute.ai.ntk.ir/v1")
    OMNIROUTE_API_KEY: str = get_saved_setting("api_key", "sk-9fc6f9a7178a0c1d-b2d998-c54c5989")
    OMNIROUTE_MODEL: str = get_saved_setting("custom_model", "trader")
    AI_PROVIDER: str = get_saved_setting("provider", "OmniRoute")

    # Server
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # Trading Defaults
    DEFAULT_SYMBOL: str = os.getenv("DEFAULT_SYMBOL", "EURUSD")
    DEFAULT_TIMEFRAME: str = os.getenv("DEFAULT_TIMEFRAME", "M15")
    DEFAULT_LOT_SIZE: float = float(os.getenv("DEFAULT_LOT_SIZE", "0.01"))
    MAX_LOT_SIZE: float = float(os.getenv("MAX_LOT_SIZE", "0.1"))
    SL_PIPS: int = int(os.getenv("SL_PIPS", "30"))
    TP_PIPS: int = int(os.getenv("TP_PIPS", "60"))
    MAGIC_NUMBER: int = int(os.getenv("MAGIC_NUMBER", "234000"))
    MAX_OPEN_POSITIONS: int = int(get_saved_setting("max_open_positions", "10"))
    HEDGE_OVERLAP_ENABLED: bool = True

    # Auto Trading
    AUTO_TRADE_ENABLED: bool = os.getenv("AUTO_TRADE_ENABLED", "false").lower() == "true"
    AUTO_TRADE_INTERVAL_SECONDS: int = int(os.getenv("AUTO_TRADE_INTERVAL_SECONDS", "60"))
    # Scalping Mode Settings
    SCALP_TIMEFRAME: str = os.getenv("SCALP_TIMEFRAME", "M1")
    SCALP_SL_PIPS: int = int(os.getenv("SCALP_SL_PIPS", "7"))
    SCALP_TP_PIPS: int = int(os.getenv("SCALP_TP_PIPS", "12"))
    SCALP_MAX_SPREAD_PIPS: float = float(os.getenv("SCALP_MAX_SPREAD_PIPS", "1.8"))
    SCALP_INTERVAL_SECONDS: int = int(os.getenv("SCALP_INTERVAL_SECONDS", "15"))

    # AI Continuous Open Position Re-Analysis & Guard
    AI_POSITION_MONITOR_ENABLED: bool = get_saved_setting("ai_position_monitor_enabled", "true").lower() in ["true", "1", "yes"]
    AI_POSITION_MONITOR_INTERVAL: int = int(get_saved_setting("ai_position_monitor_interval", "20"))

    # Daily Drawdown Circuit Breaker & Loss Protection Guard
    DAILY_LOSS_GUARD_ENABLED: bool = get_saved_setting("daily_loss_guard_enabled", "true").lower() in ["true", "1", "yes"]
    MAX_DAILY_LOSS_PERCENT: float = float(get_saved_setting("max_daily_loss_percent", "3.0"))
    # Minimum confidence threshold for automated trade execution (Auto-Trader & Scalper)
    MIN_TRADE_CONFIDENCE: float = float(get_saved_setting("min_trade_confidence", "75.0"))
    SCALP_MIN_CONFIDENCE: float = float(get_saved_setting("min_trade_confidence", "75.0"))


settings = Settings()
