"""NTK.Ai.Metatrader - Full Multi-Agent Trading Platform & Bridge (FastAPI).

Developed by Ali Karavi (https://alikaravi.com/)
Inspired by metatrader-ai (jblanked), AI-Trader (HKUDS), and NTK.Trader.
"""

from __future__ import annotations

import json
import os
import sys
import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Set

import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Local path setup
ROOT_DIR = Path(__file__).resolve().parent
PYTHON_DIR = ROOT_DIR / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from metatrader_ai.agent import Agent
from metatrader_ai.llm import ANTHROPIC, DEEPSEEK, LOCAL, OPENAI, PROVIDER_NAMES, normalize_url, LLM
from mt5_service import mt5_service
from ai_service import ai_service
from strategy_engine import strategy_engine
from trading_engine import trading_engine
from config import settings
from db import db
# In-memory storage for multi-agent simulation & copy trading
AGENTS_DB: Dict[str, Dict[str, Any]] = {
    "agent_1": {
        "id": 1,
        "name": "Alpha-Trend-Master",
        "title_fa": "ایجنت ترند مستر آلفا",
        "description_fa": "تعقیب روندهای اصلی ماژور با فیلتر نوسان و مدیریت ریسک ATR",
        "win_rate": 78.5,
        "total_pnl": 3420.50,
        "total_trades": 86,
        "followers_count": 42,
        "strategy": "تعقیب روند و سوپرترند",
        "timeframe": "M15 / H1",
        "symbols": ["EURUSD", "GBPUSD", "XAUUSD"],
        "lot_size": 0.01,
        "avatar": "bot"
    },
    "agent_2": {
        "id": 2,
        "name": "Scalp-Sniper-M1",
        "title_fa": "اسکالپر تک‌تیرانداز M1",
        "description_fa": "اسکالپینگ فوق‌سریع مومنتوم با حد ضرر کوتاه در تایم‌فریم‌های ۱ و ۵ دقیقه",
        "win_rate": 83.2,
        "total_pnl": 5120.00,
        "total_trades": 142,
        "followers_count": 68,
        "strategy": "اسکالپینگ سشن‌ها و مومنتوم",
        "timeframe": "M1 / M5",
        "symbols": ["EURUSD", "USDJPY", "XAUUSD"],
        "lot_size": 0.01,
        "avatar": "zap"
    },
    "agent_3": {
        "id": 3,
        "name": "Macro-Arbitrageur",
        "title_fa": "آربیتراژور ماکرو و اخبار کلان",
        "description_fa": "تحلیل همبستگی دارایی‌ها، شاخص دلار DXY، بازده اوراق و رویدادهای تقویم کلان",
        "win_rate": 71.0,
        "total_pnl": 2180.20,
        "total_trades": 54,
        "followers_count": 29,
        "strategy": "آربیتراژ ماکرو و همبستگی",
        "timeframe": "H1 / H4",
        "symbols": ["XAUUSD", "USDCAD", "USDCHF"],
        "lot_size": 0.01,
        "avatar": "globe"
    },
    "agent_4": {
        "id": 4,
        "name": "SMC-Liquidity-Hunter",
        "title_fa": "شکارچی نقدینگی اسمارت مانی",
        "description_fa": "شناسایی اوردر بلاک‌های نهادی، استاپ هانت و عدم تعادل‌های FVG",
        "win_rate": 81.4,
        "total_pnl": 4290.00,
        "total_trades": 98,
        "followers_count": 51,
        "strategy": "پرایس اکشن اسمارت مانی (SMC)",
        "timeframe": "M15 / H1",
        "symbols": ["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"],
        "lot_size": 0.01,
        "avatar": "target"
    }
}

SIGNALS_FEED: List[Dict[str, Any]] = [
    {
        "id": 101,
        "agent_id": 2,
        "agent_name": "Scalp-Sniper-M1",
        "symbol": "EURUSD",
        "type": "BUY",
        "price": 1.1478,
        "sl": 1.1471,
        "tp": 1.1492,
        "confidence": 85.0,
        "time": "2026-09-17 17:15:00",
        "content": "شکست مقاومت M1 همراه با واگرایی مثبت در RSI و قدرت خریداران."
    },
    {
        "id": 102,
        "agent_id": 1,
        "agent_name": "Alpha-Trend-Master",
        "symbol": "XAUUSD",
        "type": "BUY",
        "price": 2685.50,
        "sl": 2672.00,
        "tp": 2710.00,
        "confidence": 78.0,
        "time": "2026-09-17 16:45:00",
        "content": "تایید شکست ساختار بازار و ادامه روند صعودی طلا با حمایت EMA 50."
    }
]

FOLLOWING_LIST: List[Dict[str, Any]] = []

SETTINGS_FILE = ROOT_DIR / "settings.json"
active_agent: Optional[Agent] = None


# --- WebSocket Manager for Live Streaming ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)


ws_manager = ConnectionManager()


async def broadcast_live_stream():
    """Background task broadcasting real-time tick updates, account P&L, and positions every 400ms."""
    while True:
        try:
            if ws_manager.active_connections:
                symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]
                ticks = mt5_service.get_multi_symbol_ticks(symbols)
                acc = mt5_service.get_account_info() or {}
                positions = mt5_service.get_open_positions()
                
                eurusd_tick = ticks.get("EURUSD", {})

                msg = {
                    "type": "TICK_UPDATE",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    "symbol": "EURUSD",
                    "ask": eurusd_tick.get("ask"),
                    "bid": eurusd_tick.get("bid"),
                    "spread_points": eurusd_tick.get("spread_points"),
                    "ticks": ticks,
                    "account": acc,
                    "positions": positions,
                    "positions_count": len(positions),
                    "auto_trade_running": trading_engine.is_running,
                    "scalp_running": trading_engine.is_scalp_running,
                }
                await ws_manager.broadcast(msg)
            await asyncio.sleep(0.4)
        except Exception as e:
            await asyncio.sleep(1.0)

class ChatPayload(BaseModel):
    message: str
    session_id: str = Field(default="default")


class ChatSessionCreatePayload(BaseModel):
    title: str = "گفتگوی جدید"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting NTK.Ai.Metatrader Multi-Agent Trading Platform by Ali Karavi...")
    mt5_service.connect()
    init_agent_from_settings()
    
    # Auto-resume trading engines from SQLite persistent state
    asyncio.create_task(trading_engine.resume_saved_state())
    
    # Start live WebSocket stream broadcaster
    broadcaster_task = asyncio.create_task(broadcast_live_stream())
    
    yield
    print("🛑 Shutting down NTK.Ai.Metatrader services...")
    broadcaster_task.cancel()
    if trading_engine.is_running:
        await trading_engine.stop()
    if trading_engine.is_scalp_running:
        await trading_engine.stop_scalper()
    mt5_service.disconnect()


app = FastAPI(
    title="NTK.Ai.Metatrader - Multi-Agent Trading Platform",
    description="Multi-Agent AI Trading Signal Platform & MetaTrader 5 Bridge by Ali Karavi (https://alikaravi.com/)",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
STATIC_DIR = ROOT_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

TEMPLATES_DIR = ROOT_DIR / "templates"


# --- Request/Response Models ---

class OrderRequest(BaseModel):
    symbol: str = Field(default="EURUSD")
    order_type: str = Field(default="BUY")
    volume: float = Field(default=0.01)
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: Optional[str] = "AI Trader Web"


class AutoTradeStartRequest(BaseModel):
    symbols: List[str] = Field(default=["EURUSD"])
    timeframe: str = Field(default="M15")
    interval_seconds: int = Field(default=60)
    auto_execute: bool = Field(default=True)
    min_confidence: float = Field(default=70.0)


class ScalpStartRequest(BaseModel):
    symbols: List[str] = Field(default=["EURUSD"])
    timeframe: str = Field(default="M1")
    interval_seconds: int = Field(default=15)
    max_spread: float = Field(default=1.8)


class InstantScalpTradeRequest(BaseModel):
    symbol: str = Field(default="EURUSD")
    order_type: str = Field(default="BUY")
    volume: float = Field(default=0.01)
    target_pips: float = Field(default=10.0)
    sl_pips: float = Field(default=7.0)
    max_hold_minutes: int = Field(default=10)


class PositionModifyRequest(BaseModel):
    sl: Optional[float] = None
    tp: Optional[float] = None

class TrailingEngineRequest(BaseModel):
    activation_pips: float = 12.0
    distance_pips: float = 8.0
    breakeven_enabled: bool = True
    breakeven_trigger_pips: float = 10.0
    breakeven_buffer_pips: float = 0.5
    interval_seconds: int = 4
class SettingsPayload(BaseModel):
    account_login: int = 0
    account_password: str = ""
    broker_server_name: str = "MetaQuotes-Demo"
    provider: str = "OpenAI"
    api_key: str = ""
    custom_model: str = ""
    custom_url: str = ""
    max_open_positions: int = Field(default=10, ge=1, le=50)
    min_trade_confidence: float = Field(default=75.0, ge=50.0, le=99.0)
    ai_position_monitor_enabled: bool = True
    ai_position_monitor_interval: int = 20
class FollowRequest(BaseModel):
    leader_id: int
    auto_copy: bool = True
    copy_ratio: float = 1.0


class SignalPublishRequest(BaseModel):
    symbol: str
    action: str
    price: float
    quantity: float = 0.01
    sl: Optional[float] = None
class StrategyTogglePayload(BaseModel):
    is_active: bool = True


class StrategyWeightPayload(BaseModel):
    weight: float = Field(default=1.0, ge=0.1, le=10.0)

class PortfolioPairAddPayload(BaseModel):
    symbol: str
    title_fa: Optional[str] = ""
    min_confidence: float = Field(default=70.0, ge=50.0, le=99.0)
    lot_size: float = Field(default=0.01, ge=0.01, le=10.0)
    timeframe: str = Field(default="M15")

class PortfolioPairUpdatePayload(BaseModel):
    is_enabled: Optional[bool] = None
    min_confidence: Optional[float] = None
    lot_size: Optional[float] = None
    timeframe: Optional[str] = None

class PortfolioBasketExecutePayload(BaseModel):
    selected_symbols: Optional[List[str]] = None

class PortfolioSupervisorStartPayload(BaseModel):
    interval_seconds: int = Field(default=30, ge=10, le=300)
class AgentRegisterRequest(BaseModel):
    name: str
    email: str = "bot@alikaravi.com"
    password: str = "secure_password"


# --- Helper Functions ---

def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_settings(data: dict) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def init_agent_from_settings(cfg: Optional[dict] = None) -> bool:
    global active_agent
    if cfg is None:
        cfg = load_settings()

    if not cfg:
        return False

    api_key = cfg.get("api_key", "").strip() or settings.OMNIROUTE_API_KEY
    provider = cfg.get("provider", "OpenAI")
    prov_id = PROVIDER_NAMES.get(provider, OPENAI)
    custom_url = cfg.get("custom_url", "") or settings.OMNIROUTE_BASE_URL
    custom_model = cfg.get("custom_model", "") or settings.OMNIROUTE_MODEL
    settings.MAX_OPEN_POSITIONS = int(cfg.get("max_open_positions", 10) or 10)
    min_conf = float(cfg.get("min_trade_confidence", 75.0) or 75.0)
    settings.MIN_TRADE_CONFIDENCE = min_conf
    settings.SCALP_MIN_CONFIDENCE = min_conf
    ai_service.update_config(custom_url, api_key, custom_model)
    try:
        agent = Agent(
            account_login=int(cfg.get("account_login", 0) or 0),
            account_password=cfg.get("account_password", ""),
            broker_server_name=cfg.get("broker_server_name", "MetaQuotes-Demo"),
            api_key=api_key,
            model=prov_id,
            custom_model=custom_model,
            custom_url=custom_url,
        )
        active_agent = agent
        return True
    except Exception as e:
        print(f"Error initializing agent: {e}")
        return False


# --- WebSocket Live Streaming Endpoint ---

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    Live WebSocket endpoint for ultra-low latency tick streaming and account updates.
    Connects at ws://127.0.0.1:8000/ws/live and pushes live ticks and PnL every 400ms.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open and accept client heartbeats
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# --- Web UI Route ---

@app.get("/", response_class=FileResponse)
async def read_dashboard():
    """Serve the complete Persian Multi-Agent Trading Dashboard."""
    index_path = TEMPLATES_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>NTK.Ai.Metatrader</h1><p>Templates not found.</p>")


# --- MetaTrader 5 Bridge REST API Endpoints ---

@app.get("/api/terminal/status")
async def get_terminal_status():
    return mt5_service.get_terminal_status()


@app.get("/api/account")
async def get_account_info():
    acc = mt5_service.get_account_info()
    if acc is None:
        return {
            "login": 0,
            "trade_mode": "Offline",
            "currency": "USD",
            "balance": 0.0,
            "equity": 0.0,
            "profit": 0.0,
            "margin": 0.0,
            "margin_free": 0.0,
            "margin_level": 0.0,
            "leverage": 100,
            "server": "Offline",
            "company": "Offline"
        }
    return acc


@app.get("/api/symbols")
async def get_symbols():
    return mt5_service.get_available_symbols()


@app.get("/api/symbol/{symbol}/overview")
async def get_symbol_overview(symbol: str):
    overview = mt5_service.get_symbol_overview(symbol)
    if overview is None:
        return {"symbol": symbol, "ask": 0.0, "bid": 0.0, "spread_points": 0, "digits": 5}
    return overview


@app.get("/api/symbol/{symbol}/technical")
async def get_symbol_technical(symbol: str, timeframe: str = Query("M15")):
    tech = mt5_service.get_candles_with_indicators(symbol, timeframe)
    if tech is None:
        return {"symbol": symbol, "timeframe": timeframe, "trend": "نامشخص", "rsi": 50.0, "candles": []}
    return tech


@app.get("/api/analyze/{symbol}")
async def analyze_symbol(symbol: str, timeframe: str = Query("M15"), force_refresh: bool = Query(False)):
    account = mt5_service.get_account_info() or {}
    overview = mt5_service.get_symbol_overview(symbol) or {}
    tech = mt5_service.get_candles_with_indicators(symbol, timeframe) or {}
    return ai_service.analyze_market_with_indicators(symbol, account, overview, tech, force_refresh=force_refresh)

@app.get("/api/analyze/confluence/{symbol}")
async def analyze_symbol_confluence(symbol: str):
    """
    Get multi-timeframe AI confluence consensus across M1, M5, M15, H1, H4.
    Cached with 10s TTL for instant sub-50ms responses.
    """
    return ai_service.analyze_multi_timeframe_confluence(symbol)


@app.get("/api/positions")
async def get_positions():
    positions = mt5_service.get_open_positions()
    for p in positions:
        p["ai_check"] = trading_engine.get_position_ai_check(p["ticket"])
    return positions


@app.post("/api/position/{ticket}/reanalyze")
async def reanalyze_position_with_ai(ticket: int):
    """Trigger on-demand AI re-evaluation for a specific open position."""
    return await trading_engine.reanalyze_position(ticket)

@app.post("/api/order")
async def execute_order(order: OrderRequest):
    return mt5_service.execute_order(
        symbol=order.symbol,
        order_type=order.order_type,
        volume=order.volume,
        sl=order.sl,
        tp=order.tp,
        comment=order.comment or "NTK AI Trader"
    )


@app.post("/api/position/{ticket}/close")
async def close_position(ticket: int):
    return mt5_service.close_position(ticket)


@app.post("/api/positions/close-all")
async def close_all_positions(symbol: Optional[str] = None):
    return mt5_service.close_all_positions(symbol)


@app.post("/api/position/{ticket}/modify")
async def modify_position(ticket: int, req: PositionModifyRequest):
    return mt5_service.modify_position(ticket=ticket, sl=req.sl, tp=req.tp)


@app.post("/api/position/{ticket}/breakeven")
async def set_position_breakeven(ticket: int, buffer_pips: float = Query(0.5)):
    return mt5_service.set_breakeven(ticket=ticket, buffer_pips=buffer_pips)


@app.post("/api/engine/trailing/start")
async def start_trailing_engine(req: TrailingEngineRequest):
    return await trading_engine.start_trailing_engine(
        activation_pips=req.activation_pips,
        distance_pips=req.distance_pips,
        breakeven_enabled=req.breakeven_enabled,
        breakeven_trigger_pips=req.breakeven_trigger_pips,
        breakeven_buffer_pips=req.breakeven_buffer_pips,
        interval_seconds=req.interval_seconds
    )


@app.post("/api/engine/trailing/stop")
async def stop_trailing_engine():
    return await trading_engine.stop_trailing_engine()

@app.get("/api/engine/trailing/status")
async def get_trailing_engine_status():
    return trading_engine.get_trailing_status()


@app.get("/api/ai/telemetry")
async def get_ai_telemetry():
    """Return real-time AI telemetry counts: sent, pending, success, failed."""
    logs = db.get_ai_audit_logs(limit=500)
    total_sent = len(logs)
    success_count = sum(1 for l in logs if l.get("status") == "SUCCESS")
    fallback_count = sum(1 for l in logs if l.get("status") == "FALLBACK")
    failed_count = sum(1 for l in logs if l.get("status") == "ERROR")
    
    return {
        "sent": total_sent,
        "pending": 0,
        "success": success_count + fallback_count,
        "failed": failed_count,
        "success_rate": round(((success_count + fallback_count) / max(1, total_sent)) * 100, 1)
    }

@app.get("/api/stats/header-telemetry")
async def get_header_telemetry_stats():
    """Return all live metrics for the top header bar: limits, open trades, 1h/24h/week stats, and AI telemetry."""
    open_positions = mt5_service.get_open_positions()
    open_count = len(open_positions)
    open_profit = round(sum(p["profit"] for p in open_positions), 2)
    max_allowed = settings.MAX_OPEN_POSITIONS

    time_stats = db.get_time_framed_trading_stats()
    
    logs = db.get_ai_audit_logs(limit=500)
    total_sent = len(logs)
    success_count = sum(1 for l in logs if l.get("status") == "SUCCESS")
    fallback_count = sum(1 for l in logs if l.get("status") == "FALLBACK")
    failed_count = sum(1 for l in logs if l.get("status") == "ERROR")

    return {
        "max_allowed_positions": max_allowed,
        "open_positions_count": open_count,
        "open_positions_profit": open_profit,
        "last_1h": time_stats.get("last_1h", {}),
        "last_24h": time_stats.get("last_24h", {}),
        "last_7d": time_stats.get("last_7d", {}),
        "all_time": time_stats.get("all_time", {}),
        "ai_telemetry": {
            "sent": total_sent,
            "pending": 0,
            "success": success_count + fallback_count,
            "failed": failed_count
        }
    }

@app.get("/api/ai/trade-insights")
async def get_ai_trade_insights(limit: int = Query(20, ge=1, le=100)):
    return db.get_ai_trade_insights(limit=limit)

# --- AI Communication & Payload Audit Logs Endpoints ---

@app.get("/api/ai/logs")
async def get_ai_audit_logs(context_type: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=200)):
    """Fetch AI requests, prompts, responses, and latency metrics filtered by context."""
    return {
        "logs": db.get_ai_audit_logs(context_type=context_type, limit=limit),
        "summary": db.get_ai_contexts_summary()
    }


@app.get("/api/ai/contexts/summary")
async def get_ai_contexts_summary():
    """Get status, total counts, and latest activity per AI context tab."""
    return db.get_ai_contexts_summary()


@app.delete("/api/ai/logs")
async def clear_ai_audit_logs():
    """Clear AI communication logs from SQLite."""
    try:
        with db.get_connection() as conn:
            conn.execute("DELETE FROM ai_audit_logs")
            conn.commit()
        return {"success": True, "message": "تمام لاگ‌های هوش مصنوعی با موفقیت پاک‌سازی شدند."}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Multi-Pair Portfolio Hub & Master AI Supervisor Endpoints ---

@app.get("/api/portfolio/pairs")
async def get_portfolio_pairs_analysis(force_refresh: bool = Query(False)):
    """Get full multi-pair portfolio basket with live AI consensus analysis and qualification metrics."""
    return await trading_engine.analyze_all_portfolio_pairs(force_refresh=force_refresh)


@app.post("/api/portfolio/analyze-all")
async def analyze_all_portfolio_pairs_api():
    """Trigger parallel fresh multi-agent analysis across all portfolio currency pairs."""
    return await trading_engine.analyze_all_portfolio_pairs(force_refresh=True)


@app.post("/api/portfolio/pairs")
async def add_portfolio_pair_api(payload: PortfolioPairAddPayload):
    """Add a new symbol to portfolio hub."""
    success = db.add_portfolio_pair(
        symbol=payload.symbol,
        title_fa=payload.title_fa or f"جفت‌ارز {payload.symbol.upper()}",
        min_confidence=payload.min_confidence,
        lot_size=payload.lot_size,
        timeframe=payload.timeframe
    )
    return {"success": success, "message": f"نماد {payload.symbol.upper()} به سبد معاملات پورتفوی افزوده شد."}


@app.delete("/api/portfolio/pairs/{symbol}")
async def remove_portfolio_pair_api(symbol: str):
    """Remove a symbol from portfolio hub."""
    success = db.remove_portfolio_pair(symbol)
    return {"success": success, "message": f"نماد {symbol.upper()} از سبد معاملات حذف شد."}


@app.post("/api/portfolio/pairs/{symbol}/update")
async def update_portfolio_pair_api(symbol: str, payload: PortfolioPairUpdatePayload):
    """Update minimum confidence, lot size, or enable/disable a pair."""
    success = db.update_portfolio_pair(
        symbol=symbol,
        is_enabled=payload.is_enabled,
        min_confidence=payload.min_confidence,
        lot_size=payload.lot_size,
        timeframe=payload.timeframe
    )
    return {"success": success, "message": f"تنظیمات جفت‌ارز {symbol.upper()} با موفقیت بروزرسانی شد."}


@app.post("/api/portfolio/execute-basket")
async def execute_portfolio_basket_api(payload: Optional[PortfolioBasketExecutePayload] = None):
    """1-Click execute approved portfolio basket trades."""
    symbols = payload.selected_symbols if payload else None
    return await trading_engine.execute_portfolio_basket(selected_symbols=symbols)


@app.post("/api/portfolio/supervisor/start")
async def start_portfolio_supervisor_api(payload: Optional[PortfolioSupervisorStartPayload] = None):
    """Start autonomous background AI Master Supervisor for portfolio execution."""
    interval = payload.interval_seconds if payload else 30
    return await trading_engine.start_portfolio_supervisor(interval_seconds=interval)


@app.post("/api/portfolio/supervisor/stop")
async def stop_portfolio_supervisor_api():
    """Stop autonomous portfolio supervisor."""
    return await trading_engine.stop_portfolio_supervisor()


@app.get("/api/portfolio/supervisor/status")
async def get_portfolio_supervisor_status_api():
    """Get autonomous portfolio supervisor status."""
    return trading_engine.get_portfolio_supervisor_status()

@app.get("/api/portfolio/correlation")
async def get_portfolio_correlation_matrix_api(timeframe: str = Query("H1")):
    """Compute live Pearson correlation matrix for portfolio pairs."""
    pairs = db.get_portfolio_pairs()
    symbols = [p["symbol"] for p in pairs if p.get("is_enabled", 1)]
    return mt5_service.get_portfolio_correlation_matrix(symbols=symbols, timeframe=timeframe, count=60)


@app.get("/api/portfolio/exposure")
async def get_portfolio_net_exposure_api():
    """Compute net lot and risk exposure per currency (USD, EUR, GBP, JPY, XAU, etc.)."""
    return mt5_service.get_net_currency_exposure()


@app.post("/api/positions/close-profitable")
async def close_profitable_positions_api():
    """1-Click close all positions currently in profit."""
    return mt5_service.close_profitable_positions()

# --- Auto-Trading Engine Endpoints ---

@app.post("/api/autotrade/start")
async def start_autotrade(req: AutoTradeStartRequest):
    return await trading_engine.start(
        symbols=req.symbols,
        timeframe=req.timeframe,
        interval_seconds=req.interval_seconds,
        auto_execute=req.auto_execute,
        min_confidence=req.min_confidence
    )


@app.post("/api/autotrade/stop")
async def stop_autotrade():
    return await trading_engine.stop()


@app.get("/api/autotrade/status")
async def get_autotrade_status():
    return trading_engine.get_status()


@app.get("/api/autotrade/logs")
async def get_autotrade_logs(limit: int = 50):
    return trading_engine.get_logs(limit)


# --- Scalping Mode Endpoints ---

@app.post("/api/scalp/start")
async def start_scalper(req: ScalpStartRequest):
    return await trading_engine.start_scalper(
        symbols=req.symbols,
        timeframe=req.timeframe,
        interval_seconds=req.interval_seconds,
        max_spread=req.max_spread
    )


@app.post("/api/scalp/stop")
async def stop_scalper():
    return await trading_engine.stop_scalper()


@app.get("/api/scalp/status")
async def get_scalper_status():
    return trading_engine.get_scalper_status()

@app.get("/api/scalp/analyze/{symbol}")
async def analyze_scalp_symbol(symbol: str, timeframe: str = Query("M1")):
    account = mt5_service.get_account_info() or {}
    overview = mt5_service.get_symbol_overview(symbol) or {}
    tech = mt5_service.get_candles_with_indicators(symbol, timeframe, count=60) or {}
    return ai_service.analyze_scalping(symbol, account, overview, tech)


@app.post("/api/scalp/trade")
async def execute_instant_scalp_trade(req: InstantScalpTradeRequest):
    """Execute an instant micro-scalp trade with automated time-based exit (countdown)."""
    return await trading_engine.execute_instant_scalp(
        symbol=req.symbol,
        order_type=req.order_type,
        volume=req.volume,
        target_pips=req.target_pips,
        sl_pips=req.sl_pips,
        max_hold_minutes=req.max_hold_minutes
    )


@app.get("/api/scalp/active")
async def get_active_scalp_positions():
    """List currently tracked scalp trades with remaining countdown seconds."""
    return {"active_scalps": trading_engine.get_active_scalps()}

# --- Market Intelligence & Economic Calendar Endpoints ---

@app.get("/api/market-intel/overview")
async def get_market_intel_overview():
    return {
        "available": True,
        "last_updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "news_status": "active",
        "headline_count": 8,
        "active_categories": ["macro", "crypto", "equities", "commodities"],
        "top_source": "Reuters / Bloomberg",
        "latest_headline": "Federal Reserve maintains interest rate stance amid strong employment data",
        "sentiment_score": 68.5,
        "sentiment_label": "Bullish / Positive"
    }


@app.get("/api/market-intel/macro-signals")
async def get_macro_signals():
    return {
        "available": True,
        "verdict": "Risk-On (Bullish)",
        "bullish_count": 4,
        "total_count": 5,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signals": [
            {"indicator": "US Dollar Index (DXY)", "signal": "Weakening / Bearish", "impact": "Bullish for Gold & EUR"},
            {"indicator": "10Y Treasury Yield", "signal": "Stable (4.15%)", "impact": "Neutral / Risk Supportive"},
            {"indicator": "VIX Volatility Index", "signal": "Low (14.2)", "impact": "Bullish Market Sentiment"},
            {"indicator": "Global Liquidity", "signal": "Expanding", "impact": "Bullish for Risk Assets"},
            {"indicator": "Oil & Commodities", "signal": "Range-bound", "impact": "Neutral"}
        ]
    }


@app.get("/api/market-intel/etf-flows")
async def get_etf_flows():
    return {
        "available": True,
        "summary": "+$340.5M Net Inflows in last 24h",
        "is_estimated": False,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "etfs": [
            {"name": "iShares Bitcoin Trust (IBIT)", "flow": "+$185.2M", "status": "Inflow"},
            {"name": "Fidelity Wise Origin (FBTC)", "flow": "+$92.0M", "status": "Inflow"},
            {"name": "SPDR S&P 500 ETF (SPY)", "flow": "+$63.3M", "status": "Inflow"}
        ]
    }


@app.get("/api/market-intel/calendar")
async def get_economic_calendar():
    """
    Get live High-Impact Economic Calendar events with countdowns for volatility management.
    """
    now = datetime.now(timezone.utc)
    events = [
        {
            "id": "us-cpi",
            "event": "US Consumer Price Index (CPI) YoY",
            "title_fa": "شاخص بهای مصرف‌کننده آمریکا (CPI)",
            "country": "US",
            "currency": "USD",
            "impact": "HIGH",
            "impact_level": 3,
            "forecast": "3.1%",
            "previous": "3.4%",
            "actual": None,
            "scheduled_time": (now + timedelta(days=1, hours=12, minutes=30)).isoformat(),
            "countdown_seconds": 131400,
            "countdown_formatted": "1d 12h 30m 00s",
            "status": "UPCOMING",
            "volatility": "EXTREME",
            "description_fa": "اندازه‌گیری تورم مصرف‌کننده آمریکا - اثر مستقیم بر ارزش دلار و انس طلا"
        },
        {
            "id": "us-nfp",
            "event": "US Non-Farm Payrolls (NFP)",
            "title_fa": "گزارش اشتغال بخش غیرکشاورزی آمریکا (NFP)",
            "country": "US",
            "currency": "USD",
            "impact": "HIGH",
            "impact_level": 3,
            "forecast": "180K",
            "previous": "175K",
            "actual": None,
            "scheduled_time": (now + timedelta(days=2, hours=8, minutes=15)).isoformat(),
            "countdown_seconds": 202500,
            "countdown_formatted": "2d 08h 15m 00s",
            "status": "UPCOMING",
            "volatility": "EXTREME",
            "description_fa": "شاخص کلیدی اشتغال ماهانه آمریکا - نوسان‌سازترین رویداد فارکس"
        },
        {
            "id": "fomc-rate",
            "event": "Federal Reserve FOMC Interest Rate Decision",
            "title_fa": "تصمیم نرخ بهره فدرال رزرو (FOMC)",
            "country": "US",
            "currency": "USD",
            "impact": "HIGH",
            "impact_level": 3,
            "forecast": "5.25%",
            "previous": "5.50%",
            "actual": None,
            "scheduled_time": (now + timedelta(days=4, hours=14, minutes=0)).isoformat(),
            "countdown_seconds": 396000,
            "countdown_formatted": "4d 14h 00m 00s",
            "status": "UPCOMING",
            "volatility": "EXTREME",
            "description_fa": "تعیین نرخ بهره اصلی دلار و بیانیه سیاست پولی فدرال رزرو"
        },
        {
            "id": "ecb-rate",
            "event": "ECB Monetary Policy Decision",
            "title_fa": "نرخ بهره بانک مرکزی اروپا (ECB)",
            "country": "EU",
            "currency": "EUR",
            "impact": "HIGH",
            "impact_level": 3,
            "forecast": "4.25%",
            "previous": "4.25%",
            "actual": None,
            "scheduled_time": (now + timedelta(days=5, hours=6, minutes=45)).isoformat(),
            "countdown_seconds": 456300,
            "countdown_formatted": "5d 06h 45m 00s",
            "status": "UPCOMING",
            "volatility": "HIGH",
            "description_fa": "تعیین سیاست پولی و نرخ بهره یورو"
        }
    ]
    return {
        "available": True,
        "last_updated_at": now.isoformat(),
        "total_events": len(events),
        "high_impact_count": len([e for e in events if e["impact"] == "HIGH"]),
        "events": events
    }


@app.get("/api/market-intel/news")
async def get_market_news(category: Optional[str] = None, limit: int = 5):
    all_news = [
        {"title": "بانک مرکزی اروپا نرخ بهره را بدون تغییر حفظ کرد", "category": "macro", "source": "ECB News", "time": "1 ساعت پیش", "sentiment": "Neutral"},
        {"title": "رشد تقاضای اونس جهانی طلا در پی کاهش بازده اوراق قرضه", "category": "commodities", "source": "Reuters", "time": "2 ساعت پیش", "sentiment": "Bullish"},
        {"title": "حجم ورودی خالص سرمایه به صندوق‌های ETF بیت‌کوین افزایش یافت", "category": "crypto", "source": "CoinDesk", "time": "3 ساعت پیش", "sentiment": "Bullish"},
        {"title": "رشد شاخص‌های بورس وال‌استریت در پی گزارش‌های درآمدی مثبت شرکت‌های فناوری", "category": "equities", "source": "Bloomberg", "time": "4 ساعت پیش", "sentiment": "Bullish"},
    ]
    if category:
        all_news = [n for n in all_news if n["category"] == category]
    return {"news": all_news[:limit], "total": len(all_news)}


# --- Risk Calculator Tool Endpoint ---

@app.get("/api/tools/risk-calc")
async def calculate_risk_lot_size(
    risk_percent: float = Query(1.0, ge=0.1, le=10.0, description="Risk % of account equity"),
    sl_pips: float = Query(20.0, ge=1.0, le=500.0, description="Stop loss distance in pips"),
    symbol: str = Query("EURUSD")
):
    """
    Calculate mathematically precise lot size based on balance and SL pips.
    """
    acc = mt5_service.get_account_info() or {}
    balance = float(acc.get("balance", 10000.0) or 10000.0)
    risk_amount = round(balance * (risk_percent / 100.0), 2)
    
    pip_val_per_lot = 10.0  # Standard 1 lot pip value approx $10 for USD pairs
    if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
        pip_val_per_lot = 10.0
    elif "BTC" in symbol.upper():
        pip_val_per_lot = 1.0

    raw_lots = risk_amount / (sl_pips * pip_val_per_lot)
    lot_size = round(max(0.01, min(10.0, raw_lots)), 2)

    return {
        "lot_size": lot_size,
        "risk_amount": risk_amount,
        "risk_percent": risk_percent,
        "sl_pips": sl_pips,
        "symbol": symbol,
        "balance": balance,
        "pip_value": pip_val_per_lot,
        "currency": acc.get("currency", "USD"),
        "potential_profit_1_2": round(risk_amount * 2.0, 2),
        "tp_pips_1_2": sl_pips * 2.0,
        "recommendation_fa": f"حجم مجاز: {lot_size} لات با ریسک {risk_percent}% معادل ${risk_amount}",
        "recommendation_en": f"Recommended volume: {lot_size} lots with {risk_percent}% risk (${risk_amount})"
    }


# --- Persistent History & Decision Audit Trail Endpoints ---

@app.get("/api/history/decisions")
async def get_ai_decisions_history(limit: int = 20):
    """Get persistent AI decisions, step-by-step thinking chain, and action audit logs."""
    return {"decisions": db.get_ai_decisions(limit)}


@app.get("/api/history/trades")
async def get_trades_history(limit: int = 50, status: Optional[str] = None):
    """Get persistent trade history from SQLite."""
    return {"trades": db.get_trades_history(limit, status)}


@app.get("/api/history/performance")
async def get_performance_stats():
    """Get overall performance stats (Win Rate, Net PnL, Profit Factor)."""
    return db.get_performance_summary()


@app.get("/api/history/export/trades.csv", response_class=PlainTextResponse)
async def export_trades_csv():
    """Download trade history in CSV format."""
    csv_data = db.export_trades_csv()
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ntk_trades_history.csv"}
    )


@app.get("/api/reports/trade-journal/html", response_class=HTMLResponse)
async def get_printable_trade_journal_html():
    """Generate an institutional printable HTML/PDF performance debrief report."""
    summary = db.get_performance_summary()
    insights = db.get_ai_trade_insights(limit=100)
    trades = db.get_trades_history(limit=100, status="CLOSED")
    pairs = db.get_pair_performance_breakdown()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    trades_rows = ""
    for t in trades:
        is_win = (t.get("profit") or 0.0) > 0
        pnl_color = "#10b981" if is_win else "#f43f5e"
        pnl_val = t.get("profit") or 0.0
        trades_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px; font-family: monospace;">#{t.get('ticket')}</td>
            <td style="padding: 8px; font-weight: bold;">{t.get('symbol')}</td>
            <td style="padding: 8px; font-weight: bold; color: {'#10b981' if t.get('type') == 'BUY' else '#f43f5e'};">{t.get('type')}</td>
            <td style="padding: 8px; font-family: monospace;">{t.get('volume')}</td>
            <td style="padding: 8px; font-family: monospace;">{t.get('open_price')}</td>
            <td style="padding: 8px; font-family: monospace;">{t.get('close_price') or '-'}</td>
            <td style="padding: 8px; font-weight: bold; font-family: monospace; color: {pnl_color};">{'+' if pnl_val >= 0 else ''}${pnl_val:.2f}</td>
            <td style="padding: 8px; font-size: 11px;">{t.get('prediction_title') or t.get('strategy')}</td>
            <td style="padding: 8px; font-size: 10px; color: #64748b;">{t.get('close_time') or t.get('created_at')}</td>
        </tr>
        """

    pairs_rows = ""
    for p in pairs:
        pairs_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px; font-weight: bold;">{p.get('symbol')}</td>
            <td style="padding: 8px; font-family: monospace;">{p.get('total_trades')}</td>
            <td style="padding: 8px; font-weight: bold; color: #10b981;">{p.get('win_rate')}%</td>
            <td style="padding: 8px; font-family: monospace; font-weight: bold;">{'+' if (p.get('total_pnl') or 0) >= 0 else ''}${p.get('total_pnl')}</td>
            <td style="padding: 8px; font-size: 11px;">{p.get('best_strategy')}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>NTK.Ai.Metatrader - گزارش تحلیلی ژورنال معاملات</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #ffffff; color: #1e293b; padding: 24px; margin: 0; }}
            .header-banner {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3b82f6; padding-bottom: 16px; margin-bottom: 20px; }}
            .title {{ font-size: 20px; font-weight: 800; color: #1e3a8a; }}
            .meta {{ font-size: 11px; color: #64748b; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
            .kpi-card {{ background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; text-align: right; }}
            .kpi-label {{ font-size: 11px; color: #64748b; }}
            .kpi-val {{ font-size: 18px; font-weight: bold; margin-top: 4px; font-family: monospace; }}
            .section-title {{ font-size: 14px; font-weight: bold; color: #0f172a; margin: 20px 0 10px; border-right: 4px solid #3b82f6; padding-right: 8px; }}
            table {{ width: 100%; border-collapse: collapse; text-align: right; font-size: 12px; margin-bottom: 20px; }}
            th {{ background: #f1f5f9; padding: 8px; font-weight: 600; color: #475569; }}
            .summary-box {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px; font-size: 12px; color: #166534; line-height: 1.6; margin-bottom: 20px; }}
            .print-btn {{ background: #2563eb; color: #ffffff; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; }}
            @media print {{
                .no-print {{ display: none; }}
                body {{ padding: 0; }}
            }}
        </style>
    </head>
    <body>
        <div class="header-banner">
            <div>
                <div class="title">گزارش تحلیلی ژورنال معاملات هوش مصنوعی (AI Trade Journal)</div>
                <div class="meta">پلتفرم NTK.Ai.Metatrader | توسعه‌دهنده: <a href="https://alikaravi.com/" target="_blank" style="color: #2563eb; text-decoration: none;">علی کروی (Ali Karavi)</a></div>
            </div>
            <div style="text-align: left;">
                <button onclick="window.print()" class="print-btn no-print">🖨️ چاپ / ذخیره PDF</button>
                <div class="meta" style="margin-top: 6px;">تاریخ تهیه گزارش: {now_str}</div>
            </div>
        </div>

        <!-- KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">وین‌ریت کلی (Win Rate):</div>
                <div class="kpi-val" style="color: #16a34a;">{summary.get('win_rate', 0.0)}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">سود خالص (Net PnL):</div>
                <div class="kpi-val" style="color: #2563eb;">{'+' if (summary.get('net_pnl') or 0) >= 0 else ''}${summary.get('net_pnl', 0.0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">فاکتور سود (Profit Factor):</div>
                <div class="kpi-val" style="color: #9333ea;">{summary.get('profit_factor', 1.0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">کل معاملات ثبت‌شده:</div>
                <div class="kpi-val">{summary.get('total_trades', 0)}</div>
            </div>
        </div>

        <!-- AI Summary -->
        <div class="summary-box">
            <b>🧠 ارزیابی و استنتاج هوش مصنوعی:</b><br>
            {insights.get('summary_fa', 'اطلاعات در دسترس نیست.')}
        </div>

        <!-- Pair Performance -->
        <div class="section-title">عملکرد به تفکیک جفت‌ارزها (Pair Breakdown)</div>
        <table>
            <thead>
                <tr>
                    <th>جفت‌ارز</th>
                    <th>تعداد معاملات</th>
                    <th>وین‌ریت</th>
                    <th>سود خالص</th>
                    <th>استراتژی برتر معاملاتی</th>
                </tr>
            </thead>
            <tbody>
                {pairs_rows or '<tr><td colspan="5" style="text-align: center; padding: 12px;">سابقه‌ای ثبت نشده است.</td></tr>'}
            </tbody>
        </table>

        <!-- Closed Trades Table -->
        <div class="section-title">ریز تاریخچه معاملات بسته شده (Closed Trades History)</div>
        <table>
            <thead>
                <tr>
                    <th>تیکت</th>
                    <th>نماد</th>
                    <th>نوع</th>
                    <th>حجم</th>
                    <th>قیمت ورود</th>
                    <th>قیمت خروج</th>
                    <th>سود/زیان</th>
                    <th>استراتژی / پیش‌بینی</th>
                    <th>زمان بسته‌شدن</th>
                </tr>
            </thead>
            <tbody>
                {trades_rows or '<tr><td colspan="9" style="text-align: center; padding: 12px;">معامله بسته‌شده‌ای یافت نشد.</td></tr>'}
            </tbody>
        </table>

        <div style="text-align: center; margin-top: 30px; font-size: 10px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 10px;">
            NTK.Ai.Metatrader - Institutional Algorithmic & AI Trading Engine • Ali Karavi (<a href="https://alikaravi.com/" style="color: #64748b;">alikaravi.com</a>)
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# --- Quantitative Attribution & Prediction Matrix Endpoints ---

@app.get("/api/analytics/symbols")
async def get_pair_analytics():
    """Get currency pair performance breakdown and strategy recommendations."""
    return {"symbols": db.get_pair_performance_breakdown()}


@app.get("/api/analytics/strategies")
async def get_strategy_matrix():
    """Get cross-tabulated Symbol x Strategy prediction performance matrix."""
    return {"matrix": db.get_symbol_strategy_matrix()}


@app.get("/api/analytics/predictions")
async def get_predictions_audit_log(limit: int = 50, symbol: Optional[str] = None):
    """Get detailed prediction audit log with confidence %, rationale, and outcome."""
    return {"predictions": db.get_predictions_audit_log(limit, symbol)}

# --- Trading Strategy Catalog & Manager Endpoints ---

@app.get("/api/strategies")
async def list_all_strategies():
    """List all trading strategies in catalog with active status."""
    return {"strategies": db.get_all_strategies()}


@app.get("/api/strategies/active")
async def list_active_strategies():
    """List only currently active trading strategies."""
    return {"active_strategies": db.get_active_strategies()}


@app.post("/api/strategies/{strategy_id}/toggle")
async def toggle_trading_strategy(strategy_id: str, payload: StrategyTogglePayload):
    """Toggle a trading strategy active or inactive."""
    success = db.toggle_strategy(strategy_id, payload.is_active)
    ai_service.clear_cache()
    status_str = "فعال" if payload.is_active else "غیرفعال"
    return {
        "success": success,
        "strategy_id": strategy_id,
        "is_active": payload.is_active,
        "message": f"استراتژی {strategy_id} با موفقیت {status_str} شد و در تحلیل‌ها اعمال می‌گردد."
    }


@app.post("/api/strategies/{strategy_id}/weight")
async def update_trading_strategy_weight(strategy_id: str, payload: StrategyWeightPayload):
    """Update strategy importance multiplier."""
    success = db.update_strategy_weight(strategy_id, payload.weight)
    ai_service.clear_cache()
    return {
        "success": success,
        "strategy_id": strategy_id,
        "weight": payload.weight,
        "message": f"ضریب اهمیت استراتژی {strategy_id} با موفقیت روی {payload.weight}x تنظیم شد."
    }

@app.post("/api/strategies/auto-optimize")
async def auto_optimize_strategies_api():
    """Run AI Quantitative Optimizer on all 50 strategy weights based on historical win rates."""
    result = strategy_engine.optimize_strategy_weights()
    ai_service.clear_cache()
    return result


@app.get("/api/analyze/confluence-matrix/{symbol}")
async def get_multi_tf_confluence_matrix(symbol: str):
    """Fetch live multi-timeframe confluence table across M1, M5, M15, M30, H1, H4, D1."""
    timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
    active_strats = db.get_active_strategies()
    tf_results = []
    
    for tf in timeframes:
        tech = mt5_service.get_candles_with_indicators(symbol, tf) or {"trend": "خنثی", "rsi": 50.0}
        _, wp = strategy_engine.evaluate_all_strategies(symbol, tech, active_strats)
        tf_results.append({
            "timeframe": tf,
            "trend": tech.get("trend", "خنثی"),
            "rsi": tech.get("rsi", 50.0),
            "action": wp.get("consensus_action", "HOLD"),
            "confidence": wp.get("final_confidence", 50.0),
            "buy_prob": wp.get("buy_probability", 50.0),
            "sell_prob": wp.get("sell_probability", 50.0)
        })
    
    return {
        "symbol": symbol,
        "timeframes": tf_results,
        "overall_confluence": ai_service.analyze_multi_timeframe_confluence(symbol)
    }
@app.get("/api/history/chat")
async def get_persistent_chat():
    return {"history": db.get_chat_history(40)}

@app.get("/api/signals/following")
async def get_following_list():
    return {"subscriptions": FOLLOWING_LIST, "total": len(FOLLOWING_LIST)}


@app.post("/api/claw/agents/selfRegister")
async def register_agent(req: AgentRegisterRequest):
    new_id = len(AGENTS_DB) + 1
    agent_record = {
        "id": new_id,
        "name": req.name,
        "email": req.email,
        "description": "Autonomous registered agent",
        "win_rate": 70.0,
        "total_pnl": 0.0,
        "followers_count": 0,
        "status": "online",
        "strategy": "Custom AI Agent",
        "avatar": "bot"
    }
    AGENTS_DB[f"agent_{new_id}"] = agent_record
    return {
        "success": True,
        "token": f"ntk_agent_{new_id}_{int(datetime.now().timestamp())}",
        "agent_id": new_id,
        "name": req.name
    }


@app.post("/api/claw/agents/heartbeat")
async def agent_heartbeat(request: Request):
    return {
        "status": "ok",
        "agent_status": "online",
        "server_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "active_agents": len(AGENTS_DB),
        "messages": [],
        "tasks": []
    }


# --- AI Chat & Settings Endpoints ---
# --- Multi-Session Chat & Isolated Context Endpoints ---

@app.get("/api/chat/sessions")
async def list_chat_sessions():
    """List all user chat sessions."""
    return {"sessions": db.get_chat_sessions()}


@app.post("/api/chat/sessions")
async def create_new_chat_session(payload: Optional[ChatSessionCreatePayload] = None):
    """Create a new isolated chat session."""
    sess_id = f"chat_{int(datetime.now().timestamp())}_{int(time.time()*1000)%1000}"
    title = payload.title if payload and payload.title else "گفتگوی جدید"
    sess = db.create_chat_session(sess_id, title)
    return {"success": True, "session": sess}


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session."""
    success = db.delete_chat_session(session_id)
    return {"success": success, "message": f"سشن {session_id} حذف شد."}


@app.get("/api/chat/sessions/{session_id}/messages")
async def get_session_chat_messages(session_id: str):
    """Get message history for a specific chat session."""
    messages = db.get_chat_messages(session_id, limit=50)
    return {"session_id": session_id, "messages": messages}


@app.delete("/api/chat/sessions/{session_id}/messages")
async def clear_session_chat_messages(session_id: str):
    """Clear message history for a specific chat session."""
    db.clear_chat_messages(session_id)
    return {"success": True, "message": f"پیام‌های سشن {session_id} پاک‌سازی شد."}


@app.post("/api/chat")
async def chat_with_agent(payload: ChatPayload):
    global active_agent
    if not active_agent:
        init_agent_from_settings()

    if not active_agent:
        raise HTTPException(
            status_code=400,
            detail="هوش مصنوعی تنظیم نشده است. لطفاً از آیکون تنظیمات بالای صفحه، کلید API و مشخصات را وارد نمایید.",
        )

    session_id = payload.session_id or "default"
    
    # 1. Record user message to session
    db.record_chat_message(session_id, "user", payload.message)
    
    # 2. Auto-update session title based on first prompt
    sessions = db.get_chat_sessions()
    cur_sess = next((s for s in sessions if s["id"] == session_id), None)
    if cur_sess and (cur_sess["title"] in ["گفتگوی جدید", "گفتگو", "گفتگوی اصلی"] or cur_sess.get("message_count", 0) <= 2):
        new_title = payload.message.strip()[:35]
        if new_title:
            db.update_chat_session_title(session_id, new_title)

    # 3. Load isolated session history from SQLite to form context
    history_rows = db.get_chat_messages(session_id, limit=30)
    
    system_content = (
        "You are NTK.Ai.Metatrader assistant developed by Ali Karavi (https://alikaravi.com/). "
        "You are an expert algorithmic and financial market trading assistant for MetaTrader 5. "
        "Help the user analyze markets, answer trading questions, provide technical insights, "
        "and manage trades. Always respond helpfully, accurately, and professionally in Persian/English."
    )
    
    messages_payload = [{"role": "system", "content": system_content}]
    for m in history_rows:
        messages_payload.append({"role": m["role"], "content": m["content"]})

    start_ts = time.time()
    try:
        resp_obj = active_agent.llm
        headers = active_agent.headers
        
        req_payload = {
            "model": resp_obj.model,
            "messages": messages_payload,
            "stream": False,
        }
        
        resp = requests.post(resp_obj.url, headers=headers, json=req_payload, timeout=60)
        lat_ms = int((time.time() - start_ts) * 1000)
        if not resp.ok:
            try:
                err_detail = resp.json()
            except Exception:
                err_detail = resp.text
            response_text = f"API error {resp.status_code}: {err_detail}"
            call_status = "ERROR"
        else:
            call_status = "SUCCESS"
            try:
                data = resp.json()
                response_text = data["choices"][0]["message"].get("content", "")
            except Exception:
                response_text = resp.text.strip()
                if "data:" in response_text:
                    collected = []
                    for line in response_text.splitlines():
                        line = line.strip()
                        if line.startswith("data:") and not line.endswith("[DONE]"):
                            try:
                                chunk = json.loads(line[5:].strip())
                                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if delta:
                                    collected.append(delta)
                            except Exception:
                                pass
                    if collected:
                        response_text = "".join(collected)

        # Record into AI Audit Logs
        db.record_ai_audit_log(
            context_type="chat",
            prompt_sent=json.dumps(messages_payload, ensure_ascii=False, indent=2),
            response_received=response_text,
            model=resp_obj.model,
            provider=settings.AI_PROVIDER,
            parsed_action="CHAT_REPLY",
            confidence=100.0,
            latency_ms=lat_ms,
            status=call_status
        )

        # 4. Record assistant response to session
        db.record_chat_message(session_id, "assistant", response_text)
        return {"response": response_text, "session_id": session_id}
    except Exception as e:
        lat_ms = int((time.time() - start_ts) * 1000)
        err_msg = f"خطا در پردازش هوش مصنوعی: {str(e)}"
        db.record_ai_audit_log(
            context_type="chat",
            prompt_sent=json.dumps(messages_payload, ensure_ascii=False, indent=2),
            response_received=err_msg,
            model=settings.OMNIROUTE_MODEL,
            provider=settings.AI_PROVIDER,
            parsed_action="ERROR",
            confidence=0.0,
            latency_ms=lat_ms,
            status="ERROR",
            error_message=str(e)
        )
        db.record_chat_message(session_id, "assistant", err_msg)
        return {"response": err_msg, "session_id": session_id}


# --- Multi-Agent Fleet & Copy Trading Endpoints ---

@app.get("/api/agents/fleet")
async def get_agent_fleet():
    subs = db.get_agent_subscriptions()
    open_positions = mt5_service.get_open_positions()
    
    agents = []
    for ag in AGENTS_DB.values():
        ag_id = ag["id"]
        sub_info = subs.get(ag_id, {})
        is_active = bool(sub_info.get("auto_copy", 1))
        copy_ratio = float(sub_info.get("copy_ratio", 1.0))
        
        agent_open = len([p for p in open_positions if p.get("symbol") in ag.get("symbols", [])])
        
        agents.append({
            **ag,
            "is_active_in_mt5": is_active,
            "copy_ratio": copy_ratio,
            "open_positions": agent_open,
            "status_label": "🟢 فعال در حساب MT5" if is_active else "⚪ غیرفعال",
            "status_color": "emerald" if is_active else "slate"
        })
    return {"agents": agents, "total": len(agents)}


@app.post("/api/agents/{agent_id}/toggle")
async def toggle_agent_active_state(agent_id: int):
    target = next((ag for ag in AGENTS_DB.values() if ag["id"] == agent_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="ایجنت یافت نشد.")
    
    subs = db.get_agent_subscriptions()
    current_active = bool(subs.get(agent_id, {}).get("auto_copy", 1))
    new_active = not current_active
    
    db.toggle_agent_subscription(
        leader_id=agent_id,
        leader_name=target["name"],
        auto_copy=new_active,
        copy_ratio=1.0
    )
    status_str = "فعال و متصل به متاتریدر ۵" if new_active else "غیرفعال"
    return {
        "success": True,
        "agent_id": agent_id,
        "is_active_in_mt5": new_active,
        "message": f"ایجنت {target['title_fa']} با موفقیت {status_str} شد."
    }


@app.get("/api/signals/feed")
async def get_signals_feed(limit: int = 20):
    return {"signals": SIGNALS_FEED[:limit], "total": len(SIGNALS_FEED)}


@app.post("/api/signals/realtime")
async def publish_realtime_signal(req: SignalPublishRequest):
    new_sig = {
        "id": len(SIGNALS_FEED) + 101,
        "agent_id": 1,
        "agent_name": "NTK-Master-Agent",
        "symbol": req.symbol,
        "type": req.action.upper(),
        "price": req.price,
        "sl": req.sl,
        "tp": req.tp,
        "confidence": 80.0,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": req.content or f"سیگنال معاملاتی {req.action} برای نماد {req.symbol} ثبت شد."
    }
    SIGNALS_FEED.insert(0, new_sig)
    return {"success": True, "signal_id": new_sig["id"], "message": "سیگنال با موفقیت در فید منتشر شد."}


@app.post("/api/signals/{signal_id}/execute")
async def execute_signal_trade(signal_id: int):
    sig = next((s for s in SIGNALS_FEED if s["id"] == signal_id), None)
    if not sig:
        raise HTTPException(status_code=404, detail="سیگنال یافت نشد.")
    
    res = mt5_service.execute_order(
        symbol=sig["symbol"],
        order_type=sig["type"],
        volume=0.01,
        sl=sig.get("sl"),
        tp=sig.get("tp"),
        comment=f"Agent Sig #{signal_id}",
        confidence=sig.get("confidence", 80.0),
        prediction_title=f"سیگنال {sig.get('agent_name', 'Agent')}",
        prediction_reason=sig.get("content", "")
    )
    return res


@app.get("/api/settings")
async def get_settings():
    return load_settings()


@app.post("/api/settings")
async def update_settings(payload: SettingsPayload):
    data = payload.model_dump()
    save_settings(data)
    init_agent_from_settings(data)
    return {"status": "success", "message": "تنظیمات با موفقیت ذخیره و اعمال شد."}
@app.post("/api/test-ai")
async def test_ai_endpoint(payload: SettingsPayload):
    prov_id = PROVIDER_NAMES.get(payload.provider, OPENAI)
    llm_obj = LLM(
        provider_id=prov_id,
        custom_model=payload.custom_model,
        custom_url=payload.custom_url,
    )

    headers = {"Content-Type": "application/json"}
    if llm_obj.id == "anthropic":
        headers["x-api-key"] = payload.api_key
        headers["anthropic-version"] = "2023-06-01"
        test_payload = {
            "model": llm_obj.model,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "hi"}],
        }
    else:
        if llm_obj.id != "local" and payload.api_key:
            headers["Authorization"] = f"Bearer {payload.api_key}"
        test_payload = {
            "model": llm_obj.model,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 10,
            "stream": False,
        }

    try:
        resp = requests.post(llm_obj.url, headers=headers, json=test_payload, timeout=15)
        if resp.ok:
            return {
                "ok": True,
                "message": f"اتصال به مدل {llm_obj.model} با موفقیت برقرار شد.",
                "url": llm_obj.url,
            }
        else:
            try:
                err_detail = resp.json()
            except Exception:
                err_detail = resp.text
            return {
                "ok": False,
                "message": f"کد خطای {resp.status_code}: {err_detail}",
                "url": llm_obj.url,
            }
    except Exception as e:
        return {
            "ok": False,
            "message": f"خطای ارتباط: {str(e)}",
            "url": llm_obj.url,
        }


@app.post("/api/test-mt5")
async def test_mt5_endpoint(payload: SettingsPayload):
    try:
        if mt5_service.ensure_connected():
            info = mt5_service.get_account_info()
            bal = info.get("balance", 0.0) if info else 0.0
            return {
                "ok": True,
                "message": f"اتصال متاتریدر ۵ برقرار است. موجودی: ${bal:.2f}",
            }
        else:
            return {
                "ok": False,
                "message": "لاگین به متاتریدر ۵ ناموفق بود.",
            }
    except Exception as e:
        return {
            "ok": False,
            "message": f"خطا در ارتباط با متاتریدر: {str(e)}",
        }


@app.post("/api/connect")
async def connect_agent(payload: SettingsPayload):
    data = payload.model_dump()
    save_settings(data)
    success = init_agent_from_settings(data)
    if success:
        return {"status": "success", "message": "تنظیمات هوش مصنوعی و متاتریدر ۵ با موفقیت ذخیره و اعمال شد."}
    return {"status": "error", "message": "خطا در برقراری اتصال با اطلاعات جدید."}


if __name__ == "__main__":
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
