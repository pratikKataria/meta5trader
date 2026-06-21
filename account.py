# ==========================
# account.py — Account info display
# ==========================

import MetaTrader5 as mt5


def print_account_info() -> None:
    """Fetch and display the current account details."""
    info = mt5.account_info()

    print("Account:", info.login)
    print("Balance:", info.balance)
    print("Equity:", info.equity)
    print("Server:", info.server)
    print()
