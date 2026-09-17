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

    # place a pending buy limit order
    info = client.get_symbol_info(SYMBOL)
    ask = info.get("ask", 0)
    if not ask:
        print(f"\033[91mCould not retrieve price for {SYMBOL}.\033[0m")
        return

    limit_price = round(ask * 0.90, 2)  # 10 % below ask — stays pending
    print(f"Current ASK: {ask}  ->  placing BUY LIMIT at: {limit_price}")

    ok = client.order_send(
        symbol=SYMBOL,
        order_type="buy limit",
        lot=LOT,
        order_price=limit_price,
    )
    if not ok:
        print("\033[91mFailed to place pending buy limit order.\033[0m")
        return
    print("\033[92mPending buy limit order placed successfully.\033[0m")

    # delete the pending order
    orders = client.get_orders(SYMBOL)
    if not orders:
        print("\033[91mNo pending orders found after placing order.\033[0m")
        return

    ticket = orders[0]["ticket"]
    print(f"Pending order ticket: {ticket}")

    ok = client.order_delete(ticket)
    if not ok:
        print(f"\033[91mFailed to delete order {ticket}.\033[0m")
        return
    print(f"\033[92mPending order {ticket} deleted successfully.\033[0m")


if __name__ == "__main__":
    main()
