# ==========================
# main.py — Entry point
# ==========================

import asyncio

import websockets

import config
import connection
import account
import symbols
import market_data
import ws_server


async def main() -> None:
    # ── MT5 setup ──
    connection.initialize()
    connection.login()

    account.print_account_info()
    symbols.enable_symbols()
    market_data.print_historical_candles()

    print(f"WebSocket server on ws://localhost:{config.WS_PORT}\n")

    # ── Run WebSocket server only ──
    async with websockets.serve(ws_server.handler, "localhost", config.WS_PORT):
        await ws_server.broadcast_ticks()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        connection.shutdown()