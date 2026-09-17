import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import secrets
from tools.mt5 import MT5

SYMBOL = "ETHUSD"
LOT = 0.01


def main():
    client = MT5(
        secrets.ACCOUNT_NUMBER,
        secrets.ACCOUNT_PASSWORD,
        secrets.BROKER_SERVER_NAME,
    )

    if not client.login():
        print("\033[91mFailed to login to MetaTrader 5.\033[0m")
        return

    print("\033[92mLogged in successfully.\033[0m")

    # place a market buy order
    ok = client.order_send(
        symbol=SYMBOL,
        order_type="buy",
        lot=LOT,
    )
    if not ok:
        print("\033[91mFailed to place market buy order.\033[0m")
        return
    print("\033[92mMarket buy order placed successfully.\033[0m")

    # close the position
    positions = client.get_positions(SYMBOL)
    if not positions:
        print("\033[91mNo open positions found after placing order.\033[0m")
        return

    ticket = positions[0]["ticket"]
    print(f"Position ticket: {ticket}")

    ok = client.position_close(ticket)
    if not ok:
        print(f"\033[91mFailed to close position {ticket}.\033[0m")
        return
    print(f"\033[92mPosition {ticket} closed successfully.\033[0m")


if __name__ == "__main__":
    main()
