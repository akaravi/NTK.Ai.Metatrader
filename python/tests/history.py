import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import secrets
from tools.mt5 import MT5

SYMBOL = "ETHUSD"


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

    # get all historical positions for the current year
    positions = client.get_history_positions()
    if not positions:
        print("\033[93mNo historical positions found for the current year.\033[0m")
        return

    print(f"\033[92mFound {len(positions)} historical deal(s).\033[0m")
    for pos in positions[:5]:  # print first 5 for brevity
        print(
            f"  ticket={pos['ticket']}  symbol={pos['symbol']}  "
            f"type={pos['type']}  volume={pos['volume']}  "
            f"price={pos['price']}  profit={pos['profit']}  time={pos['time']}"
        )

    # get all deals for the first closed position
    ticket = positions[0]["ticket"]
    print(f"\nFetching all deals for ticket {ticket}...")
    deals = client.get_history_position(ticket)
    if not deals:
        print(f"\033[91mNo deals found for ticket {ticket}.\033[0m")
        return

    print(f"\033[92mFound {len(deals)} deal(s) for ticket {ticket}.\033[0m")
    for deal in deals:
        print(f"  deal={deal}")

    # filter history by symbol
    print(f"\nFetching historical positions filtered by symbol {SYMBOL}...")
    symbol_positions = client.get_history_positions(symbol=SYMBOL)
    if not symbol_positions:
        print(f"\033[93mNo historical positions found for {SYMBOL}.\033[0m")
    else:
        print(
            f"\033[92mFound {len(symbol_positions)} historical deal(s) for {SYMBOL}.\033[0m"
        )


if __name__ == "__main__":
    main()
