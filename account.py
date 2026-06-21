# ==========================
# account.py — Account info display
# ==========================

import connection


def print_account_info() -> None:
    """Fetch and display the current account details."""
    mt5  = connection.get_mt5()
    info = mt5.account_info()

    print("Account:", info.login)
    print("Balance:", info.balance)
    print("Equity:",  info.equity)
    print("Server:",  info.server)
    print()