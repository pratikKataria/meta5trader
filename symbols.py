# ==========================
# symbols.py — Symbol management
# ==========================

from connection import mt5   # ← shared mt5linux instance
import config


def enable_symbols() -> None:
    """Enable all configured symbols in the Market Watch."""
    for symbol in config.SYMBOLS:
        if not mt5.symbol_select(symbol, True):
            print("Failed to enable", symbol)
        else:
            print(symbol, "enabled")
    print()