# ==========================
# market_data.py — Historical candles and live ticks
# ==========================

import asyncio
import time
from datetime import datetime

from connection import mt5   # ← shared mt5linux instance
import config


def print_historical_candles() -> None:
    """Print the last N M1 candles for the configured historical symbol."""
    print(f"Last {config.HISTORICAL_CANDLES} candles (M1)\n")

    rates = mt5.copy_rates_from_pos(
        config.HISTORICAL_SYMBOL,
        mt5.TIMEFRAME_M1,
        0,
        config.HISTORICAL_CANDLES,
    )

    for r in rates:
        print(datetime.fromtimestamp(r["time"]), r["open"], r["close"])

    print()


def stream_live_ticks() -> None:
    """Stream live ticks to console — blocking loop (used standalone)."""
    print("Streaming live ticks...\n")

    while True:
        for symbol in config.SYMBOLS:
            tick = mt5.symbol_info_tick(symbol)
            if tick is not None:
                print(datetime.now(), symbol, "Bid:", tick.bid, "Ask:", tick.ask)

        print("-" * 48)
        time.sleep(config.TICK_INTERVAL_SECONDS)


async def stream_live_ticks_async() -> None:
    """Stream live ticks to console — async version."""
    print("Streaming live ticks...\n")

    while True:
        for symbol in config.SYMBOLS:
            tick = mt5.symbol_info_tick(symbol)
            if tick is not None:
                print(datetime.now(), symbol, "Bid:", tick.bid, "Ask:", tick.ask)

        print("-" * 48)
        await asyncio.sleep(config.TICK_INTERVAL_SECONDS)