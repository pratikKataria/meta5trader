# ==========================
# connection.py — MT5 init, login, shutdown
# ==========================

import time
from mt5linux import MetaTrader5
import config

mt5 = None

def initialize() -> None:
    global mt5
    print("Connecting to MT5 RPyC server...")

    for attempt in range(10):
        try:
            mt5 = MetaTrader5(host='localhost', port=18812)
            if mt5.initialize():
                print("MT5 initialized successfully.")
                return
            else:
                print(f"Attempt {attempt+1}: initialize() failed: {mt5.last_error()}")
        except Exception as e:
            print(f"Attempt {attempt+1}: Connection error: {e}")

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


def shutdown() -> None:
    if mt5:
        mt5.shutdown()