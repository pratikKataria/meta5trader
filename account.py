# ==========================
# account.py — Account info display
# ==========================

from mt5linux import MetaTrader5
mt5 = MetaTrader5(host='localhost', port=18812)

def print_account_info() -> None:
    """Fetch and display the current account details."""
    info = mt5.account_info()

    print("Account:", info.login)
    print("Balance:", info.balance)
    print("Equity:", info.equity)
    print("Server:", info.server)
    print()
