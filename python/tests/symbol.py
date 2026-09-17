import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import secrets
from tools.mt5 import MT5

SYMBOL = "ETHUSD"

# timeframe constant -> label
TIMEFRAMES = {
    1: "M1",
    5: "M5",
    15: "M15",
    30: "M30",
    16385: "H1",
    16388: "H4",
    16408: "D1",
}

BARS_PER_TIMEFRAME = 3


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

    # symbol info
    print(f"\n--- Symbol info: {SYMBOL} ---")
    info = client.get_symbol_info(SYMBOL)
    if not info:
        print(f"\033[91mCould not retrieve symbol info for {SYMBOL}.\033[0m")
        return
    for key, value in info.items():
        print(f"  {key}: {value}")

    # recent bars across multiple timeframes
    for tf_const, tf_label in TIMEFRAMES.items():
        print(f"\n--- {tf_label} bars (last {BARS_PER_TIMEFRAME}) ---")
        bars = client.get_recent_bars(SYMBOL, tf_const, BARS_PER_TIMEFRAME)
        if not bars:
            print(f"  \033[93mNo bars returned for {tf_label}.\033[0m")
            continue
        for bar in bars:
            print(
                f"  time={bar['time']}  O={bar['open']}  H={bar['high']}  "
                f"L={bar['low']}  C={bar['close']}  vol={bar['tick_volume']}"
            )

    # iOpen / iHigh / iLow / iClose / iDate for the last closed bar (shift=1)
    # tested on H1 and D1
    for tf_const, tf_label in {16385: "H1", 16408: "D1"}.items():
        print(f"\n--- iXxx helpers at shift=1 ({tf_label}) ---")
        date = client.iDate(SYMBOL, tf_const, 1)
        open_ = client.iOpen(SYMBOL, tf_const, 1)
        high = client.iHigh(SYMBOL, tf_const, 1)
        low = client.iLow(SYMBOL, tf_const, 1)
        close = client.iClose(SYMBOL, tf_const, 1)
        print(f"  time={date}  open={open_}  high={high}  low={low}  close={close}")
        if not date:
            print(f"  \033[91mFailed to read {tf_label} bar data.\033[0m")
        else:
            print(f"  \033[92m{tf_label} bar data read successfully.\033[0m")


if __name__ == "__main__":
    main()
