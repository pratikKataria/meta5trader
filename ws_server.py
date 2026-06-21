# ==========================
# ws_server.py — Per-client symbol filtering via URL query params
# ==========================

import asyncio
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import websockets

import connection
import config


CLIENTS: dict[any, set[str]] = {}


async def broadcast_ticks() -> None:
    """Push ticks to every connected client, filtered to their watchlist."""
    while True:
        if CLIENTS:
            mt5 = connection.get_mt5()

            # Collect all unique symbols needed across all clients
            all_needed = set().union(*CLIENTS.values())

            # Fetch once per unique symbol
            tick_map: dict[str, dict] = {}
            for symbol in all_needed:
                tick = mt5.symbol_info_tick(symbol)
                if tick is not None:
                    tick_map[symbol] = {
                        "symbol": symbol,
                        "bid":    tick.bid,
                        "ask":    tick.ask,
                        "time":   datetime.now().isoformat(),
                    }

            # Send each client only their symbols
            disconnected = set()
            for client, symbols in CLIENTS.items():
                payload = [tick_map[s] for s in symbols if s in tick_map]
                if not payload:
                    continue
                try:
                    await client.send(json.dumps(payload))
                except websockets.ConnectionClosed:
                    disconnected.add(client)

            for client in disconnected:
                CLIENTS.pop(client, None)

        await asyncio.sleep(config.TICK_INTERVAL_SECONDS)


def parse_symbols(websocket) -> set[str]:
    """Extract and validate ?symbols= from the connection URL."""
    try:
        path      = websocket.request.path
        query     = parse_qs(urlparse(path).query)
        raw       = query.get("symbols", [""])[0]
        requested = {s.strip().upper() for s in raw.split(",") if s.strip()}
        valid     = {s for s in requested if s in config.SYMBOLS}
        unknown   = requested - valid

        if unknown:
            print(f"  [!] Unknown symbols ignored: {unknown}")

        return valid if valid else set(config.SYMBOLS)
    except Exception:
        return set(config.SYMBOLS)


async def handler(websocket) -> None:
    """Register client with their requested symbols, stream until disconnect."""
    mt5     = connection.get_mt5()
    symbols = parse_symbols(websocket)
    CLIENTS[websocket] = symbols

    addr = websocket.remote_address
    print(f"[+] Client connected: {addr}  |  Symbols: {symbols}  |  Total: {len(CLIENTS)}")

    # Enable any newly requested symbols in MT5
    for symbol in symbols:
        mt5.symbol_select(symbol, True)

    try:
        await websocket.wait_closed()
    finally:
        CLIENTS.pop(websocket, None)
        print(f"[-] Client disconnected: {addr}  |  Total: {len(CLIENTS)}")