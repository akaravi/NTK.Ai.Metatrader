from datetime import datetime
import json
from pathlib import Path
from typing import Optional

import requests

from .tools import dispatch, mt5
from .llm import DEEPSEEK, LLM, LOCAL, OPENAI

BASE_DIR = Path(__file__).resolve().parent

CONTEXT_FILES = [
    "context/python.md",
    "context/trade.md",
    "workflows/response.md",
]


class Agent:
    """Stateful MetaTrader AI agent that keeps multi-turn chat history."""

    def __init__(
        self,
        account_login: int,
        account_password: str,
        broker_server_name: str,
        api_key: str,
        model: int | LLM = DEEPSEEK,
        custom_model: str = "",
        custom_url: str = "",
    ):
        if isinstance(model, LLM):
            self.llm = model
        else:
            self.llm = LLM(model, custom_model=custom_model, custom_url=custom_url)

        if (not api_key or len(api_key) < 3) and self.llm.id != "local":
            raise ValueError("No API key set.")

        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if self.llm.id == "anthropic":
            self.headers["x-api-key"] = api_key
            self.headers["anthropic-version"] = "2023-06-01"
        elif self.llm.id != "local":
            self.headers["Authorization"] = f"Bearer {api_key}"
        self.metatrader_client = mt5.MT5(
            account_login,
            account_password,
            broker_server_name,
        )
        dispatch.set_metatrader(self.metatrader_client)

        self.mt5_connected = False
        try:
            if account_login:
                self.mt5_connected = bool(self.metatrader_client.login())
            else:
                self.mt5_connected = bool(self.metatrader_client.open())
        except Exception:
            self.mt5_connected = False
        self.messages = self.initialize_messages()

    @staticmethod
    def _read_markdown(relative_path: str) -> str:
        file_path = BASE_DIR / relative_path
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_prompt(self) -> str:
        """Return the system prompt from package context files."""
        return self._read_markdown("context/prompt.md")

    def load_markdown_files(self, file_paths: list[str]) -> str:
        """Read markdown files from package data and combine their content."""
        combined = ""
        for rel_path in file_paths:
            combined += f"\n\n--- {rel_path} ---\n{self._read_markdown(rel_path)}"
        return combined

    def initialize_messages(self) -> list[dict]:
        """Build initial system context for a multi-turn conversation."""
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_content = (
            f"Today's current date and time is {current_time_str}.\n"
            "You are NTK.Ai.Metatrader assistant developed by Ali Karavi (https://alikaravi.com/). "
            "You are directly connected to the user's live MetaTrader 5 (MT5) terminal. "
            "When the user asks for account balance, open positions, active orders, today's trades/deals history (e.g. 'لیست معاملات امروز من را بده'), or symbol prices, "
            "YOU MUST ALWAYS call the corresponding MT5 function tools (e.g., get_history_positions, get_positions, get_account_info, get_orders, get_recent_bars) "
            "to fetch the live data from MetaTrader 5 and present the exact real data in a neat table or list with ticket numbers, profit/loss, and details. "
            "NEVER give generic instructions on how to click in MetaTrader when the user asks for their data. Always fetch and return the actual data. "
            "Always respond helpfully, accurately, and professionally in the user's language (Persian/English)."
        )
        return [{"role": "system", "content": system_content}]
    def run(self, prompt: str) -> str:
        """Process one user turn and return the assistant response."""
        if not prompt:
            return ""

        self.messages.append({"role": "user", "content": prompt})
        
        # Only include tool definitions if MT5 is connected
        tools = dispatch.get_tool_list() if self.mt5_connected else []

        try:
            # Handle Anthropic API format
            if self.llm.id == "anthropic":
                return self._run_anthropic()

            # OpenAI / DeepSeek / Custom Router Format
            while True:
                payload: dict = {
                    "model": self.llm.model,
                    "messages": self.messages,
                    "stream": False,
                }
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

                response = requests.post(
                    self.llm.url, headers=self.headers, json=payload, timeout=60
                )

                # Fallback if custom router does not support tools parameter or returns empty
                if (not response.ok or not response.text.strip()) and tools:
                    tools = []  # disable tools for this turn
                    fallback_payload = {
                        "model": self.llm.model,
                        "messages": self.messages,
                        "stream": False,
                    }
                    response = requests.post(
                        self.llm.url, headers=self.headers, json=fallback_payload, timeout=60
                    )

                if not response.ok:
                    try:
                        detail = response.json()
                    except Exception:
                        detail = response.text
                    return f"API error {response.status_code}: {detail}"

                # Parse JSON or SSE or plain text safely
                text_content = response.text.strip()
                if not text_content:
                    return "Received empty response from AI router."

                data = {}
                try:
                    data = response.json()
                except Exception:
                    # Check if response is Server-Sent Events (SSE lines)
                    if "data:" in text_content:
                        collected = []
                        for line in text_content.splitlines():
                            line = line.strip()
                            if line.startswith("data:") and not line.endswith("[DONE]"):
                                chunk_str = line[5:].strip()
                                try:
                                    chunk = json.loads(chunk_str)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if delta:
                                        collected.append(delta)
                                except Exception:
                                    pass
                        if collected:
                            assistant_content = "".join(collected)
                            self.messages.append({"role": "assistant", "content": assistant_content})
                            return assistant_content
                    # Raw text fallback
                    self.messages.append({"role": "assistant", "content": text_content})
                    return text_content

                if "choices" not in data or not data["choices"]:
                    if "message" in data:
                        assistant_content = data["message"]
                        self.messages.append({"role": "assistant", "content": assistant_content})
                        return assistant_content
                    return f"API response error: {data}"

                message = data["choices"][0].get("message", {})

                if not message.get("tool_calls"):
                    assistant_content = message.get("content") or ""
                    self.messages.append(
                        {"role": "assistant", "content": assistant_content}
                    )
                    return assistant_content

                assistant_msg: dict = {
                    "role": "assistant",
                    "tool_calls": message["tool_calls"],
                }
                if message.get("content") is not None:
                    assistant_msg["content"] = message["content"]
                self.messages.append(assistant_msg)

                for tool_call in message["tool_calls"]:
                    name = tool_call["function"]["name"]
                    raw_args = tool_call["function"].get("arguments") or "{}"

                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {}

                    result = dispatch.execute_tool(name, args)

                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": str(result),
                        }
                    )
        except Exception as e:
            return f"An error occurred during processing: {e}"

    def _run_anthropic(self) -> str:
        system_content = (
            self.messages[0]["content"]
            if self.messages and self.messages[0]["role"] == "system"
            else ""
        )
        non_system_msgs = [m for m in self.messages if m["role"] != "system"]

        payload = {
            "model": self.llm.model,
            "max_tokens": 4096,
            "system": system_content,
            "messages": non_system_msgs,
        }

        response = requests.post(
            self.llm.url, headers=self.headers, json=payload, timeout=60
        )
        if not response.ok:
            return f"API error {response.status_code}: {response.text}"

        data = response.json()
        content_blocks = data.get("content", [])
        text_resp = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        self.messages.append({"role": "assistant", "content": text_resp})
        return text_resp

    def chat(self) -> None:
        """Run the interactive terminal chat loop."""
        while True:
            prompt = input("\033[93m>>> \033[0m").strip()

            if not prompt:
                continue

            if prompt.lower() in ("exit", "quit", "q"):
                break

            print(self.run(prompt))


def run(
    account_login: int,
    account_password: str,
    broker_server_name: str,
    api_key: str,
    prompt: str,
    model: int = DEEPSEEK,
    custom_model: str = "",
    custom_url: str = "",
) -> str:
    """One-shot helper: instantiate an Agent, run a single prompt, and return."""
    agent = Agent(
        account_login=account_login,
        account_password=account_password,
        broker_server_name=broker_server_name,
        api_key=api_key,
        model=model,
        custom_model=custom_model,
        custom_url=custom_url,
    )
    return agent.run(prompt)
