# ==========================
# symbols.py — Symbol management
# ==========================

import connection
import config


def enable_symbols() -> None:
    """Enable all configured symbols in the Market Watch."""
    mt5 = connection.get_mt5()

    for symbol in config.SYMBOLS:
        if not mt5.symbol_select(symbol, True):
            print("Failed to enable", symbol)
        else:
            print(symbol, "enabled")
    print()