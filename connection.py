# ==========================
# connection.py — MT5 init, login, shutdown
# ==========================

import time
from mt5linux import MetaTrader5

import config

# Shared mt5 instance — initialized lazily in initialize()
mt5: MetaTrader5 = None


def initialize() -> None:
    global mt5
    print("Connecting to MT5 RPyC server...")

    for attempt in range(10):
        try:
            client = MetaTrader5(host='localhost', port=18812)
            if client.initialize():
                mt5 = client
                print("MT5 initialized successfully.")
                return
            else:
                print(f"Attempt {attempt + 1}: initialize() failed: {client.last_error()}")
        except Exception as e:
            print(f"Attempt {attempt + 1}: Connection error: {e}")

        time.sleep(10)

    print("Could not initialize MT5 after 10 attempts. Exiting.")
    quit()


def login() -> None:
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


def get_mt5() -> MetaTrader5:
    """Always use this getter to access the mt5 instance."""
    if mt5 is None:
        raise RuntimeError("MT5 not initialized. Call connection.initialize() first.")
    return mt5


def shutdown() -> None:
    if mt5:
        mt5.shutdown()