# ==========================
# connection.py — MT5 init, login, shutdown
# ==========================

from mt5linux import MetaTrader5
mt5 = MetaTrader5(host='localhost', port=18812)

import config


def initialize() -> None:
    """Initialize the MT5 terminal. Exits the program on failure."""
    # No path needed on Linux — MT5 is already running in Docker via Wine
    if not mt5.initialize():
        print("Initialize failed:", mt5.last_error())
        quit()


def login() -> None:
    """Log into the MT5 account. Shuts down and exits on failure."""
    authorized = mt5.login(
        config.ACCOUNT,
        password=config.PASSWORD,
        server=config.SERVER,
    )
    if not authorized:
        print("Login failed:", mt5.last_error())
        mt5.shutdown()
        quit()

    print("\nConnected to MT5\n")


def shutdown() -> None:
    """Gracefully shut down the MT5 connection."""
    mt5.shutdown()