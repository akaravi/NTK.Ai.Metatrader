from . import mt5, build

# set by agent.py on startup
metatrader = None  # type: ignore  # mt5.MT5
TOOL_MAP = {}


def _build_tool_map() -> dict:
    """Create a callable map from the initialized MT5 client."""
    if metatrader is None:
        raise RuntimeError(
            "\033[91mMetaTrader client is not initialized. Call set_metatrader() first.\033[0m"
        )

    return {
        # MT5 tools
        "close": metatrader.close,
        "get_account_info": metatrader.get_account_info,
        "get_history_position": metatrader.get_history_position,
        "get_history_positions": metatrader.get_history_positions,
        "get_order": metatrader.get_order,
        "get_orders": metatrader.get_orders,
        "get_pip_value": metatrader.get_pip_value,
        "get_position": metatrader.get_position,
        "get_positions": metatrader.get_positions,
        "get_recent_bars": metatrader.get_recent_bars,
        "get_risk": metatrader.get_risk,
        "get_symbol_info": metatrader.get_symbol_info,
        "iClose": metatrader.iClose,
        "iDate": metatrader.iDate,
        "iHigh": metatrader.iHigh,
        "iLow": metatrader.iLow,
        "iOpen": metatrader.iOpen,
        "is_order_opened": metatrader.is_order_opened,
        "is_position_opened": metatrader.is_position_opened,
        "login": metatrader.login,
        "open": metatrader.open,
        "order_delete": metatrader.order_delete,
        "order_send": metatrader.order_send,
        "order_send_pips": metatrader.order_send_pips,
        "order_modify": metatrader.order_modify,
        "position_close": metatrader.position_close,
        "position_modify": metatrader.position_modify,
        # build tool
        "build_mql5": build.build_mql5,
    }


def set_metatrader(client):
    """Set the MT5 client and rebuild the dispatch table."""
    globals()["metatrader"] = client

    TOOL_MAP.clear()
    TOOL_MAP.update(_build_tool_map())


def _ensure_tool_map() -> None:
    """Lazy-initialize TOOL_MAP if metatrader was assigned directly."""
    if not TOOL_MAP:
        TOOL_MAP.update(_build_tool_map())


def execute_tool(name: str, args: dict):
    """Executes a tool by name with the given arguments."""
    _ensure_tool_map()
    if name not in TOOL_MAP:
        raise ValueError(f"\033[91mUnknown tool: {name}\033[0m")
    print(f"\033[90m[AGENT] Executing tool: {name} with args: {args}\033[0m")
    result = TOOL_MAP[name](**args)
    print(f"\033[90m[AGENT] Tool {name} returned: {result}\033[0m")
    return result


def get_tool_list(is_openai: bool = True) -> list:
    """Returns an OpenAI-formatted list of tools."""
    return (
        [
            # MT5 tools
            mt5.TOOL_CLOSE.json_openai,
            mt5.TOOL_GET_ACCOUNT_INFO.json_openai,
            mt5.TOOL_GET_HISTORY_POSITION.json_openai,
            mt5.TOOL_GET_HISTORY_POSITIONS.json_openai,
            mt5.TOOL_GET_ORDER.json_openai,
            mt5.TOOL_GET_ORDERS.json_openai,
            mt5.TOOL_GET_PIP_VALUE.json_openai,
            mt5.TOOL_GET_POSITION.json_openai,
            mt5.TOOL_GET_POSITIONS.json_openai,
            mt5.TOOL_GET_RECENT_BARS.json_openai,
            mt5.TOOL_GET_RISK.json_openai,
            mt5.TOOL_GET_SYMBOL_INFO.json_openai,
            mt5.TOOL_ICLOSE.json_openai,
            mt5.TOOL_IDATE.json_openai,
            mt5.TOOL_IHIGH.json_openai,
            mt5.TOOL_ILOW.json_openai,
            mt5.TOOL_IOPEN.json_openai,
            mt5.TOOL_IS_ORDER_OPENED.json_openai,
            mt5.TOOL_IS_POSITION_OPENED.json_openai,
            mt5.TOOL_LOGIN.json_openai,
            mt5.TOOL_OPEN.json_openai,
            mt5.TOOL_ORDER_DELETE.json_openai,
            mt5.TOOL_ORDER_SEND.json_openai,
            mt5.TOOL_ORDER_SEND_PIPS.json_openai,
            mt5.TOOL_ORDER_MODIFY.json_openai,
            mt5.TOOL_POSITION_CLOSE.json_openai,
            mt5.TOOL_POSITION_MODIFY.json_openai,
            # build tool
            build.TOOL_BUILD_MQL5.json_openai,
        ]
        if is_openai
        else [
            # MT5 tools
            mt5.TOOL_CLOSE.json_anthropic,
            mt5.TOOL_GET_ACCOUNT_INFO.json_anthropic,
            mt5.TOOL_GET_HISTORY_POSITION.json_anthropic,
            mt5.TOOL_GET_HISTORY_POSITIONS.json_anthropic,
            mt5.TOOL_GET_ORDER.json_anthropic,
            mt5.TOOL_GET_ORDERS.json_anthropic,
            mt5.TOOL_GET_PIP_VALUE.json_anthropic,
            mt5.TOOL_GET_POSITION.json_anthropic,
            mt5.TOOL_GET_POSITIONS.json_anthropic,
            mt5.TOOL_GET_RECENT_BARS.json_anthropic,
            mt5.TOOL_GET_RISK.json_anthropic,
            mt5.TOOL_GET_SYMBOL_INFO.json_anthropic,
            mt5.TOOL_ICLOSE.json_anthropic,
            mt5.TOOL_IDATE.json_anthropic,
            mt5.TOOL_IHIGH.json_anthropic,
            mt5.TOOL_ILOW.json_anthropic,
            mt5.TOOL_IOPEN.json_anthropic,
            mt5.TOOL_IS_ORDER_OPENED.json_anthropic,
            mt5.TOOL_IS_POSITION_OPENED.json_anthropic,
            mt5.TOOL_LOGIN.json_anthropic,
            mt5.TOOL_OPEN.json_anthropic,
            mt5.TOOL_ORDER_DELETE.json_anthropic,
            mt5.TOOL_ORDER_SEND.json_anthropic,
            mt5.TOOL_ORDER_SEND_PIPS.json_anthropic,
            mt5.TOOL_ORDER_MODIFY.json_anthropic,
            mt5.TOOL_POSITION_CLOSE.json_anthropic,
            mt5.TOOL_POSITION_MODIFY.json_anthropic,
            # build tool
            build.TOOL_BUILD_MQL5.json_anthropic,
        ]
    )
