import argparse
import os

from .agent import Agent
from .llm import DEEPSEEK, OPENAI

PROVIDER_MAP = {
    "openai": OPENAI,
    "deepseek": DEEPSEEK,
}


def _env_first(*names: str):
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MetaTrader AI command line client")
    parser.add_argument(
        "--api-key", default=_env_first("DEEPSEEK_API_KEY", "OPENAI_API_KEY")
    )
    parser.add_argument(
        "--account-login",
        type=int,
        default=_env_first("ACCOUNT_LOGIN", "ACCOUNT_NUMBER"),
    )
    parser.add_argument(
        "--account-pass",
        default=_env_first("ACCOUNT_PASS", "ACCOUNT_PASSWORD"),
    )
    parser.add_argument(
        "--broker-name",
        default=_env_first("BROKER_NAME", "BROKER_SERVER_NAME"),
    )
    parser.add_argument(
        "--provider",
        default="deepseek",
        choices=["openai", "deepseek"],
        help="LLM provider to use (openai or deepseek).",
    )
    parser.add_argument(
        "--prompt",
        help="Optional single prompt. If omitted, interactive mode starts.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    missing = []
    if not args.api_key:
        missing.append("api_key")
    if args.account_login is None:
        missing.append("account_login")
    if not args.account_pass:
        missing.append("account_pass")
    if not args.broker_name:
        missing.append("broker_name")

    if missing:
        parser.error(
            "Missing credentials. Provide flags or environment variables for: "
            + ", ".join(missing)
        )

    agent = Agent(
        api_key=args.api_key,
        account_login=int(args.account_login),
        account_password=args.account_pass,
        broker_server_name=args.broker_name,
        model=PROVIDER_MAP[args.provider],
    )

    if args.prompt:
        print(agent.run(args.prompt))
        return 0

    agent.chat()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
