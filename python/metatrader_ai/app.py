"""NTK.Ai.Metatrader desktop GUI (customtkinter).

Developed by Ali Karavi (https://alikaravi.com/)
Inspired by metatrader-ai (jblanked) and AI-Trader (HKUDS).
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import requests

from .agent import Agent
from .llm import ANTHROPIC, DEEPSEEK, LOCAL, OPENAI, PROVIDER_NAMES, LLM
from .tools import mt5

# Color palette
COLOR_BG = "#1E1E1E"
COLOR_CARD_BG = "#26262B"
COLOR_USER_BUBBLE = "#0A84FF"
COLOR_AI_BUBBLE = "#37373C"
COLOR_USER_TEXT = "#FFFFFF"
COLOR_AI_TEXT = "#DCDCDC"
COLOR_TAB_ACTIVE = "#323237"
COLOR_TAB_INACTIVE = "#232328"
COLOR_TAB_TEXT = "#C8C8C8"
COLOR_INPUT_BG = "#2D2D32"
COLOR_SEND_BTN = "#0A84FF"
COLOR_SEND_TEXT = "#FFFFFF"
COLOR_ACCENT = "#0A84FF"
COLOR_SUCCESS = "#30D158"
COLOR_ERROR = "#FF453A"
COLOR_WARNING = "#FF9F0A"
COLOR_BORDER = "#3C3C41"
COLOR_INFO_KEY = "#A0A0A0"
COLOR_INFO_VAL = "#DCDCDC"
COLOR_HEADER_BG = "#28282D"

FONT_FAMILY = "Consolas"
FONT_SIZES = {
    "tab": 12,
    "msg": 11,
    "input": 11,
    "send": 11,
    "info_key": 10,
    "info_val": 10,
    "header": 12,
    "scroll": 9,
    "subheading": 11,
}

SETTINGS_FILE = Path("settings.json")


def load_saved_settings() -> dict:
    """Load settings from local settings.json if it exists."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_settings_to_file(data: dict) -> None:
    """Save configuration to settings.json."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")


class ScrollableChatFrame(ctk.CTkFrame):
    """Single textbox chat view — wrapping and scrolling handled natively."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._txt = ctk.CTkTextbox(
            self,
            wrap="word",
            fg_color="transparent",
            text_color=COLOR_AI_TEXT,
            font=(FONT_FAMILY, FONT_SIZES["msg"]),
            border_width=0,
            activate_scrollbars=True,
        )
        self._txt.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._txt.insert("0.0", "")
        self._txt.configure(state="disabled")

        # User prefix tag
        self._txt._textbox.tag_config(
            "user_prefix",
            foreground=COLOR_ACCENT,
            font=(FONT_FAMILY, FONT_SIZES["msg"], "bold"),
        )
        self._txt._textbox.tag_config(
            "sys_prefix",
            foreground=COLOR_WARNING,
            font=(FONT_FAMILY, FONT_SIZES["msg"], "bold"),
        )

    def add_message(self, role: str, text: str, timestamp: str = "") -> None:
        self._txt.configure(state="normal")

        prefix = f"[{timestamp}] " if timestamp else ""
        if role == "user":
            prefix += "You: "
            tag = "user_prefix"
        elif role == "system":
            prefix += "System: "
            tag = "sys_prefix"
        else:
            prefix += "AI: "
            tag = ""

        self._txt.insert("end", prefix, tag)
        self._txt.insert("end", text + "\n\n")
        self._txt.configure(state="disabled")
        self._txt.yview_moveto(1.0)

    def clear(self) -> None:
        self._txt.configure(state="normal")
        self._txt.delete("0.0", "end")
        self._txt.configure(state="disabled")


class ScrollableInfoFrame(ctk.CTkScrollableFrame):
    """Scrollable terminal/symbol/account info."""

    def __init__(self, master, mt5_client=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._mt5 = mt5_client
        self._info_rows: list[ctk.CTkFrame] = []

    def set_client(self, client) -> None:
        self._mt5 = client

    def clear(self) -> None:
        for w in self._info_rows:
            w.destroy()
        self._info_rows.clear()

    def refresh(self) -> None:
        """Rebuild info rows from MetaTrader state."""
        self.clear()

        if self._mt5 is None:
            self._show_error("No MetaTrader client configured.\nPlease configure in the Settings tab.")
            return

        if not getattr(self._mt5, "is_connected", False):
            self._show_error("MetaTrader not connected.\nPlease check connection in Settings tab.")
            return

        rows: list[tuple[str, str, bool]] = []

        # Terminal Info
        ti = self._mt5.terminal_info
        rows.append(("── Terminal Info ──", "", True))
        if ti:
            rows.append(("Name", str(getattr(ti, "name", "")), False))
            rows.append(("Data Path", str(getattr(ti, "data_path", "")), False))
            rows.append(("Build", str(getattr(ti, "build", "")), False))
            rows.append(("Max Bars", str(getattr(ti, "maxbars", "")), False))
            rows.append(("Connected", "Yes" if getattr(ti, "connected", False) else "No", False))
            rows.append(("Trade Allowed", "Yes" if getattr(ti, "trade_allowed", False) else "No", False))
            rows.append(("DLLs Allowed", "Yes" if getattr(ti, "dlls_allowed", False) else "No", False))

        # Symbol Info
        symbol_name = self._pick_symbol()
        si = self._mt5.get_symbol_info(symbol_name) if symbol_name else {}
        rows.append(("", "", False))
        rows.append(("── Symbol Info ──", "", True))
        if si:
            rows.append(("Symbol", symbol_name, False))
            rows.append(("Bid", str(si.get("bid", "")), False))
            rows.append(("Ask", str(si.get("ask", "")), False))
            rows.append(("Spread", str(si.get("spread", "")), False))
            rows.append(("Digits", str(si.get("digits", "")), False))
            rows.append(("Point", str(si.get("point", "")), False))
            rows.append(("Tick Value", str(si.get("tick_value", "")), False))
            rows.append(("Volume Max", str(si.get("max_lot_size", "")), False))

        # Account Info
        ai = self._mt5.account_info
        rows.append(("", "", False))
        rows.append(("── Account Info ──", "", True))
        if ai:
            rows.append(("Login", str(getattr(ai, "login", "")), False))
            rows.append(("Name", str(getattr(ai, "name", "")), False))
            rows.append(("Company", str(getattr(ai, "company", "")), False))
            rows.append(("Currency", str(getattr(ai, "currency", "")), False))
            rows.append(("Balance", f"{getattr(ai, 'balance', 0):.2f}", False))
            rows.append(("Equity", f"{getattr(ai, 'equity', 0):.2f}", False))
            rows.append(("Margin", f"{getattr(ai, 'margin', 0):.2f}", False))
            rows.append(("Free Margin", f"{getattr(ai, 'margin_free', 0):.2f}", False))
            rows.append(("Margin Level", f"{getattr(ai, 'margin_level', 0):.2f}", False))
            rows.append(("Profit", f"{getattr(ai, 'profit', 0):.2f}", False))
            rows.append(("Leverage", str(getattr(ai, "leverage", "")), False))

        self._build_rows(rows)

    def _pick_symbol(self) -> str:
        """Return a symbol from open positions, or a safe default."""
        try:
            positions = self._mt5.get_positions()
            if positions:
                return positions[0].get("symbol", "EURUSD")
        except Exception:
            pass
        return "EURUSD"

    def _show_error(self, msg: str) -> None:
        lbl = ctk.CTkLabel(
            self,
            text=msg,
            text_color="#FF6B6B",
            font=(FONT_FAMILY, FONT_SIZES["info_val"]),
            justify="center",
        )
        lbl.pack(pady=40)
        self._info_rows.append(lbl)

    def _build_rows(self, rows: list[tuple[str, str, bool]]) -> None:
        for key, val, is_header in rows:
            row_frame = ctk.CTkFrame(self, fg_color="transparent")
            row_frame.pack(fill="x", padx=8, pady=(0, 1))
            row_frame.grid_columnconfigure(1, weight=1)

            if is_header:
                lbl = ctk.CTkLabel(
                    row_frame,
                    text=key,
                    text_color=COLOR_ACCENT,
                    font=(FONT_FAMILY, FONT_SIZES["header"], "bold"),
                    anchor="w",
                    fg_color=COLOR_HEADER_BG,
                    corner_radius=4,
                    padx=8,
                    pady=4,
                )
                lbl.pack(fill="x")
            elif key == "" and val == "":
                lbl = ctk.CTkLabel(row_frame, text="", height=4)
                lbl.pack(fill="x")
            else:
                key_lbl = ctk.CTkLabel(
                    row_frame,
                    text=key,
                    text_color=COLOR_INFO_KEY,
                    font=(FONT_FAMILY, FONT_SIZES["info_key"]),
                    anchor="w",
                )
                key_lbl.grid(row=0, column=0, sticky="w", padx=(8, 4))

                val_lbl = ctk.CTkLabel(
                    row_frame,
                    text=val,
                    text_color=COLOR_INFO_VAL,
                    font=(FONT_FAMILY, FONT_SIZES["info_val"]),
                    anchor="e",
                )
                val_lbl.grid(row=0, column=1, sticky="e", padx=(4, 8))

            self._info_rows.append(row_frame)


class ScrollableSettingsFrame(ctk.CTkScrollableFrame):
    """Configuration and connection settings UI."""

    def __init__(self, master, app: "App", **kwargs):
        super().__init__(master, **kwargs)
        self._app = app
        self.grid_columnconfigure(0, weight=1)

        saved = load_saved_settings()

        # Header Title
        title_lbl = ctk.CTkLabel(
            self,
            text="⚙️ Settings & Connection / تنظیمات و اتصال",
            font=(FONT_FAMILY, 14, "bold"),
            text_color=COLOR_ACCENT,
            anchor="w",
        )
        title_lbl.pack(fill="x", padx=12, pady=(10, 2))

        sub_lbl = ctk.CTkLabel(
            self,
            text="NTK.Ai.Metatrader - Developed by Ali Karavi (https://alikaravi.com/)",
            font=(FONT_FAMILY, 10),
            text_color="#888888",
            anchor="w",
        )
        sub_lbl.pack(fill="x", padx=12, pady=(0, 12))

        # Section 1: MetaTrader 5
        self._build_section_header("📊 MetaTrader 5 Connection / تنظیمات متاتریدر ۵")

        self._ent_login = self._create_input_field(
            "Account Login / شماره حساب:",
            placeholder="e.g. 12345678",
            default_val=str(saved.get("account_login", "")),
        )

        self._ent_password = self._create_input_field(
            "Account Password / رمز عبور:",
            placeholder="Account trading or investor password",
            default_val=saved.get("account_password", ""),
            is_password=True,
        )

        self._ent_server = self._create_input_field(
            "Broker Server / سرور بروکر:",
            placeholder="e.g. MetaQuotes-Demo, ICMarketsSC-Demo",
            default_val=saved.get("broker_server_name", "MetaQuotes-Demo"),
        )

        # Section 2: AI & LLM Provider
        self._build_section_header("🤖 AI & LLM Model / تنظیمات هوش مصنوعی")

        lbl_provider = ctk.CTkLabel(
            self,
            text="LLM Provider / ارائه‌دهنده مدل:",
            font=(FONT_FAMILY, FONT_SIZES["info_key"]),
            text_color=COLOR_INFO_KEY,
            anchor="w",
        )
        lbl_provider.pack(fill="x", padx=12, pady=(4, 2))

        provider_options = ["DeepSeek", "OpenAI", "Anthropic", "Local"]
        default_prov = saved.get("provider", "DeepSeek")
        if default_prov not in provider_options:
            default_prov = "DeepSeek"

        self._opt_provider = ctk.CTkOptionMenu(
            self,
            values=provider_options,
            font=(FONT_FAMILY, 11),
            fg_color=COLOR_INPUT_BG,
            button_color=COLOR_ACCENT,
            button_hover_color="#0066CC",
            dropdown_fg_color=COLOR_CARD_BG,
            command=self._on_provider_change,
        )
        self._opt_provider.set(default_prov)
        self._opt_provider.pack(fill="x", padx=12, pady=(0, 8))

        self._ent_api_key = self._create_input_field(
            "API Key / کلید API:",
            placeholder="sk-...",
            default_val=saved.get("api_key", ""),
            is_password=True,
        )

        self._ent_custom_model = self._create_input_field(
            "Model Name / نام مدل (اختیاری):",
            placeholder="e.g. deepseek-chat, gpt-4o-mini",
            default_val=saved.get("custom_model", ""),
        )

        self._ent_custom_url = self._create_input_field(
            "Custom API URL / آدرس سرور دلخواه (اختیاری):",
            placeholder="e.g. http://127.0.0.1:11434/v1/chat/completions",
            default_val=saved.get("custom_url", ""),
        )

        # Status Label
        self._lbl_status = ctk.CTkLabel(
            self,
            text="● Disconnected / متصل نیست",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=COLOR_ERROR,
            anchor="center",
        )
        self._lbl_status.pack(fill="x", padx=12, pady=(12, 6))

        # Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(4, 15))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self._btn_connect = ctk.CTkButton(
            btn_frame,
            text="💾 Save & Connect / ذخیره و اتصال",
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=COLOR_SEND_BTN,
            hover_color="#0066CC",
            text_color=COLOR_SEND_TEXT,
            height=36,
            corner_radius=6,
            command=self._on_save_and_connect,
        )
        self._btn_connect.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self._btn_test = ctk.CTkButton(
            btn_frame,
            text="🔍 Test / بررسی اتصال",
            font=(FONT_FAMILY, 11),
            fg_color=COLOR_CARD_BG,
            hover_color=COLOR_TAB_ACTIVE,
            text_color=COLOR_AI_TEXT,
            height=36,
            corner_radius=6,
            command=self._on_test_connection,
        )
        self._btn_test.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        if self._app._agent is not None:
            self.update_status("● Connected / متصل شد", COLOR_SUCCESS)

    def _build_section_header(self, text: str) -> None:
        lbl = ctk.CTkLabel(
            self,
            text=text,
            font=(FONT_FAMILY, FONT_SIZES["subheading"], "bold"),
            text_color=COLOR_ACCENT,
            fg_color=COLOR_HEADER_BG,
            corner_radius=4,
            anchor="w",
            padx=8,
            pady=4,
        )
        lbl.pack(fill="x", padx=12, pady=(10, 4))

    def _create_input_field(
        self,
        label: str,
        placeholder: str = "",
        default_val: str = "",
        is_password: bool = False,
    ) -> ctk.CTkEntry:
        lbl = ctk.CTkLabel(
            self,
            text=label,
            font=(FONT_FAMILY, FONT_SIZES["info_key"]),
            text_color=COLOR_INFO_KEY,
            anchor="w",
        )
        lbl.pack(fill="x", padx=12, pady=(4, 2))

        entry_frame = ctk.CTkFrame(self, fg_color="transparent")
        entry_frame.pack(fill="x", padx=12, pady=(0, 6))
        entry_frame.grid_columnconfigure(0, weight=1)

        ent = ctk.CTkEntry(
            entry_frame,
            font=(FONT_FAMILY, FONT_SIZES["input"]),
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_AI_TEXT,
            border_color=COLOR_BORDER,
            placeholder_text=placeholder,
            show="*" if is_password else "",
            height=32,
        )
        if default_val:
            ent.insert(0, default_val)
        ent.grid(row=0, column=0, sticky="ew")

        if is_password:
            def toggle_eye():
                if ent.cget("show") == "*":
                    ent.configure(show="")
                    btn_eye.configure(text="🔒")
                else:
                    ent.configure(show="*")
                    btn_eye.configure(text="👁")

            btn_eye = ctk.CTkButton(
                entry_frame,
                text="👁",
                width=32,
                height=32,
                fg_color=COLOR_CARD_BG,
                hover_color=COLOR_TAB_ACTIVE,
                command=toggle_eye,
            )
            btn_eye.grid(row=0, column=1, padx=(4, 0))

        return ent

    def _on_provider_change(self, choice: str) -> None:
        if choice == "Local":
            if not self._ent_custom_url.get():
                self._ent_custom_url.insert(0, "http://127.0.0.1:11434/v1/chat/completions")

    def update_status(self, text: str, color: str) -> None:
        self._lbl_status.configure(text=text, text_color=color)

    def get_settings_dict(self) -> dict:
        login_str = self._ent_login.get().strip()
        login_val = int(login_str) if login_str.isdigit() else 0

        return {
            "account_login": login_val,
            "account_password": self._ent_password.get().strip(),
            "broker_server_name": self._ent_server.get().strip(),
            "provider": self._opt_provider.get(),
            "api_key": self._ent_api_key.get().strip(),
            "custom_model": self._ent_custom_model.get().strip(),
            "custom_url": self._ent_custom_url.get().strip(),
        }

    def _on_save_and_connect(self) -> None:
        cfg = self.get_settings_dict()

        if not cfg["account_login"]:
            self.update_status("❌ Error: Invalid Account Login ID", COLOR_ERROR)
            return

        if not cfg["broker_server_name"]:
            self.update_status("❌ Error: Broker server required", COLOR_ERROR)
            return

        save_settings_to_file(cfg)
        self.update_status("⏳ Connecting to MetaTrader & AI...", COLOR_WARNING)
        self._btn_connect.configure(state="disabled")

        threading.Thread(target=self._connect_thread, args=(cfg,), daemon=True).start()

    def _connect_thread(self, cfg: dict) -> None:
        try:
            prov_id = PROVIDER_NAMES.get(cfg["provider"], DEEPSEEK)
            agent = Agent(
                account_login=cfg["account_login"],
                account_password=cfg["account_password"],
                broker_server_name=cfg["broker_server_name"],
                api_key=cfg["api_key"],
                model=prov_id,
                custom_model=cfg["custom_model"],
                custom_url=cfg["custom_url"],
            )

            self.after(0, self._on_connect_success, agent, cfg)
        except Exception as e:
            self.after(0, self._on_connect_error, str(e))

    def _on_connect_success(self, agent: Agent, cfg: dict) -> None:
        self._btn_connect.configure(state="normal")
        self._app.set_agent(agent)
        self.update_status(f"● Connected: #{cfg['account_login']} ({cfg['provider']})", COLOR_SUCCESS)
        self._app.add_message(
            "system",
            f"Connected successfully to MetaTrader 5 (Account #{cfg['account_login']} on {cfg['broker_server_name']}) using {cfg['provider']}!"
        )
        self._app._switch_to_chat()

    def _on_connect_error(self, err_msg: str) -> None:
        self._btn_connect.configure(state="normal")
        self.update_status(f"❌ Connection Failed: {err_msg[:45]}...", COLOR_ERROR)
        self._app.add_message("system", f"Connection failed: {err_msg}")

    def _on_test_connection(self) -> None:
        cfg = self.get_settings_dict()
        self.update_status("⏳ Testing MT5 & AI Router...", COLOR_WARNING)

        def test_task():
            prov_id = PROVIDER_NAMES.get(cfg["provider"], OPENAI)
            llm_obj = LLM(
                provider_id=prov_id,
                custom_model=cfg["custom_model"],
                custom_url=cfg["custom_url"],
            )
            headers = {"Content-Type": "application/json"}
            if llm_obj.id != "local" and cfg["api_key"]:
                headers["Authorization"] = f"Bearer {cfg['api_key']}"
            test_payload = {
                "model": llm_obj.model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 10,
            }

            ai_ok = False
            ai_msg = ""
            try:
                resp = requests.post(llm_obj.url, headers=headers, json=test_payload, timeout=12)
                if resp.ok:
                    ai_ok = True
                    ai_msg = f"AI OK ({llm_obj.model})"
                else:
                    ai_msg = f"AI HTTP {resp.status_code}"
            except Exception as e:
                ai_msg = f"AI Error: {str(e)[:30]}"

            mt5_ok = False
            mt5_msg = ""
            try:
                client = mt5.MT5(
                    cfg["account_login"],
                    cfg["account_password"],
                    cfg["broker_server_name"],
                )
                if client.login():
                    info = client.account_info
                    bal = getattr(info, "balance", 0.0) if info else 0.0
                    mt5_ok = True
                    mt5_msg = f"MT5 OK (${bal:.2f})"
                else:
                    mt5_msg = "MT5 Login Fail"
            except Exception as e:
                mt5_msg = f"MT5: {str(e)[:25]}"

            if ai_ok and mt5_ok:
                self.after(0, lambda: self.update_status(f"✅ {mt5_msg} | {ai_msg}", COLOR_SUCCESS))
            elif ai_ok:
                self.after(0, lambda: self.update_status(f"⚠️ {ai_msg} | {mt5_msg}", COLOR_WARNING))
            else:
                self.after(0, lambda: self.update_status(f"❌ {ai_msg} | {mt5_msg}", COLOR_ERROR))

        threading.Thread(target=test_task, daemon=True).start()


class App(ctk.CTk):
    """Main window — Chat, Info, and Settings tabs."""

    def __init__(
        self,
        agent: Optional[Agent] = None,
        title: str = "NTK.Ai.Metatrader - Ali Karavi",
        width: int = 560,
        height: int = 740,
    ):
        super().__init__()
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(420, 520)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=COLOR_BG)

        self._agent = agent
        self._message_history: list[dict[str, str]] = []
        self._request_pending = False
        self._pending_msg: str = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Tab bar frame
        self._tab_frame = ctk.CTkFrame(self, fg_color="transparent", height=34)
        self._tab_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self._tab_frame.grid_columnconfigure((0, 1, 2), weight=0)
        self._tab_frame.grid_columnconfigure(3, weight=1)

        tab_w, tab_h = 100, 32

        self._btn_chat = ctk.CTkButton(
            self._tab_frame,
            text="Chat / گفتگو",
            width=tab_w,
            height=tab_h,
            font=(FONT_FAMILY, FONT_SIZES["tab"]),
            fg_color=COLOR_TAB_ACTIVE,
            hover_color=COLOR_TAB_ACTIVE,
            text_color=COLOR_TAB_TEXT,
            corner_radius=0,
            command=self._switch_to_chat,
        )
        self._btn_chat.grid(row=0, column=0, padx=(0, 1))

        self._btn_info = ctk.CTkButton(
            self._tab_frame,
            text="Info / اطلاعات",
            width=tab_w,
            height=tab_h,
            font=(FONT_FAMILY, FONT_SIZES["tab"]),
            fg_color=COLOR_TAB_INACTIVE,
            hover_color=COLOR_TAB_INACTIVE,
            text_color=COLOR_TAB_TEXT,
            corner_radius=0,
            command=self._switch_to_info,
        )
        self._btn_info.grid(row=0, column=1, padx=(0, 1))

        self._btn_settings = ctk.CTkButton(
            self._tab_frame,
            text="Settings / تنظیمات",
            width=120,
            height=tab_h,
            font=(FONT_FAMILY, FONT_SIZES["tab"]),
            fg_color=COLOR_TAB_INACTIVE,
            hover_color=COLOR_TAB_INACTIVE,
            text_color=COLOR_TAB_TEXT,
            corner_radius=0,
            command=self._switch_to_settings,
        )
        self._btn_settings.grid(row=0, column=2, padx=(0, 0))

        # Main content area
        self._content = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self._content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        # 1. Chat Tab Frame
        self._chat_frame = ctk.CTkFrame(self._content, fg_color=COLOR_BG)
        self._chat_frame.grid_columnconfigure(0, weight=1)
        self._chat_frame.grid_rowconfigure(0, weight=1)

        self._chat_scroll = ScrollableChatFrame(self._chat_frame, fg_color=COLOR_BG)
        self._chat_scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self._input_frame = ctk.CTkFrame(
            self._chat_frame, fg_color=COLOR_INPUT_BG, height=44
        )
        self._input_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        self._input_frame.grid_columnconfigure(0, weight=1)

        self._txt_input = ctk.CTkEntry(
            self._input_frame,
            font=(FONT_FAMILY, FONT_SIZES["input"]),
            fg_color=COLOR_BG,
            text_color=COLOR_AI_TEXT,
            border_color=COLOR_BORDER,
            placeholder_text="Type a question or trading prompt…",
            placeholder_text_color="#666666",
        )
        self._txt_input.grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=6)
        self._txt_input.bind("<Return>", lambda e: self._send_message())

        self._btn_send = ctk.CTkButton(
            self._input_frame,
            text="Send",
            width=70,
            font=(FONT_FAMILY, FONT_SIZES["send"]),
            fg_color=COLOR_SEND_BTN,
            hover_color="#0066CC",
            text_color=COLOR_SEND_TEXT,
            corner_radius=6,
            command=self._send_message,
        )
        self._btn_send.grid(row=0, column=1, padx=(4, 8), pady=6)

        # 2. Info Tab Frame
        self._info_frame = ctk.CTkFrame(self._content, fg_color=COLOR_BG)
        self._info_frame.grid_columnconfigure(0, weight=1)
        self._info_frame.grid_rowconfigure(0, weight=1)

        mt5_client = (
            getattr(self._agent, "metatrader_client", None) if self._agent else None
        )
        self._info_scroll = ScrollableInfoFrame(
            self._info_frame,
            mt5_client=mt5_client,
            fg_color=COLOR_BG,
            scrollbar_button_color=COLOR_TAB_INACTIVE,
            scrollbar_button_hover_color=COLOR_TAB_ACTIVE,
        )
        self._info_scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # 3. Settings Tab Frame
        self._settings_frame = ctk.CTkFrame(self._content, fg_color=COLOR_BG)
        self._settings_frame.grid_columnconfigure(0, weight=1)
        self._settings_frame.grid_rowconfigure(0, weight=1)

        self._settings_scroll = ScrollableSettingsFrame(
            self._settings_frame,
            app=self,
            fg_color=COLOR_BG,
            scrollbar_button_color=COLOR_TAB_INACTIVE,
            scrollbar_button_hover_color=COLOR_TAB_ACTIVE,
        )
        self._settings_scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self._current_tab: str = "chat"

        # Welcome message
        self.add_message(
            "assistant",
            "Hello! I'm NTK.Ai.Metatrader assistant (by Ali Karavi - https://alikaravi.com/).\n"
            "You can manage positions, check market data, and execute trades.\n"
            "If you haven't connected your account yet, open the Settings tab to configure your credentials.",
        )

        # If no agent provided, show Settings tab first
        if self._agent is None:
            self._switch_to_settings()
        else:
            self._switch_to_chat()

    def set_agent(self, agent: Agent) -> None:
        self._agent = agent
        if hasattr(agent, "metatrader_client"):
            self._info_scroll.set_client(agent.metatrader_client)

    # Tab switching
    def _switch_to_chat(self) -> None:
        self._show_tab("chat")
        self._btn_chat.configure(fg_color=COLOR_TAB_ACTIVE)
        self._btn_info.configure(fg_color=COLOR_TAB_INACTIVE)
        self._btn_settings.configure(fg_color=COLOR_TAB_INACTIVE)

    def _switch_to_info(self) -> None:
        self._show_tab("info")
        self._btn_chat.configure(fg_color=COLOR_TAB_INACTIVE)
        self._btn_info.configure(fg_color=COLOR_TAB_ACTIVE)
        self._btn_settings.configure(fg_color=COLOR_TAB_INACTIVE)
        self._info_scroll.refresh()

    def _switch_to_settings(self) -> None:
        self._show_tab("settings")
        self._btn_chat.configure(fg_color=COLOR_TAB_INACTIVE)
        self._btn_info.configure(fg_color=COLOR_TAB_INACTIVE)
        self._btn_settings.configure(fg_color=COLOR_TAB_ACTIVE)

    def _show_tab(self, tab: str) -> None:
        self._chat_frame.grid_forget()
        self._info_frame.grid_forget()
        self._settings_frame.grid_forget()

        if tab == "chat":
            self._chat_frame.grid(row=0, column=0, sticky="nsew")
        elif tab == "info":
            self._info_frame.grid(row=0, column=0, sticky="nsew")
        elif tab == "settings":
            self._settings_frame.grid(row=0, column=0, sticky="nsew")

        self._current_tab = tab

    # Chat logic
    def add_message(self, role: str, content: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._message_history.append({"role": role, "content": content, "time": ts})
        self._chat_scroll.add_message(role, content, timestamp=ts)

    def _send_message(self) -> None:
        if self._request_pending:
            return

        text = self._txt_input.get().strip()
        if not text:
            return

        self._txt_input.delete(0, "end")
        self.add_message("user", text)

        if self._agent is not None:
            self._request_pending = True
            self._pending_msg = text
            self.add_message("assistant", "Thinking…")
            self._btn_send.configure(state="disabled")

            thread = threading.Thread(target=self._run_agent, daemon=True)
            thread.start()
        else:
            self.add_message(
                "system",
                "⚠️ No active agent connection. Please go to the Settings tab, enter your credentials, and click 'Save & Connect'."
            )

    def _run_agent(self) -> None:
        try:
            response = self._agent.run(self._pending_msg)
        except Exception as e:
            response = f"Error: {e}"
        self.after(0, self._complete_pending, response)

    def _complete_pending(self, response: str) -> None:
        if not self._request_pending:
            return
        self._request_pending = False

        # Pop placeholder
        if self._message_history and self._message_history[-1]["content"] == "Thinking…":
            self._message_history.pop()

        # Append response
        self._message_history.append(
            {
                "role": "assistant",
                "content": response,
                "time": datetime.now().strftime("%H:%M:%S"),
            }
        )

        # Redraw all
        self._chat_scroll.clear()
        for msg in self._message_history:
            self._chat_scroll.add_message(
                msg["role"], msg["content"], timestamp=msg.get("time", "")
            )

        self._btn_send.configure(state="normal")

    def on_close(self) -> None:
        self.destroy()


def launch(
    agent: Optional[Agent] = None,
    title: str = "NTK.Ai.Metatrader - Ali Karavi",
    width: int = 560,
    height: int = 740,
    *,
    api_key: Optional[str] = None,
    account_login: Optional[int] = None,
    account_password: Optional[str] = None,
    broker_server_name: Optional[str] = None,
    model: int = DEEPSEEK,
    custom_model: str = "",
    custom_url: str = "",
) -> None:
    """Launch the desktop GUI.

    Pass a pre-built agent, or provide credentials, or use the in-app Settings page.
    """
    if agent is None and api_key and account_login and account_password and broker_server_name:
        try:
            agent = Agent(
                api_key=api_key,
                account_login=account_login,
                account_password=account_password,
                broker_server_name=broker_server_name,
                model=model,
                custom_model=custom_model,
                custom_url=custom_url,
            )
        except Exception as e:
            print(f"Could not initialize agent from arguments: {e}")

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")
    app = App(agent=agent, title=title, width=width, height=height)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    launch()
