# ==========================
# ws_server.py — Per-client symbol filtering via URL query params
# ==========================

import asyncio
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import MetaTrader5 as mt5
import websockets

import config


# Map of websocket -> set of symbols for that client
CLIENTS: dict[any, set[str]] = {}


def get_ticks_for(symbols: set[str]) -> list[dict]:
    """Fetch latest tick only for the given symbols."""
    ticks = []

    for symbol in symbols:
        tick = mt5.symbol_info_tick(symbol)

        if tick is not None:
            ticks.append({
                "symbol": symbol,
                "bid":    tick.bid,
                "ask":    tick.ask,
                "time":   datetime.now().isoformat(),
            })

    return ticks


def parse_symbols(websocket) -> set[str]:
    """Extract and validate ?symbols= from the connection URL."""
    try:
        path  = websocket.request.path          # e.g. /?symbols=EURUSD,XAUUSD
        query = parse_qs(urlparse(path).query)  # {'symbols': ['EURUSD,XAUUSD']}
        raw   = query.get("symbols", [""])[0]

        requested = {s.strip().upper() for s in raw.split(",") if s.strip()}

        # Only allow symbols that are in config + exist in MT5
        valid = {s for s in requested if s in config.SYMBOLS}

        # Warn about unknown symbols
        unknown = requested - valid
        if unknown:
            print(f"  [!] Unknown symbols ignored: {unknown}")

        return valid if valid else set(config.SYMBOLS)  # fallback: all symbols

    except Exception:
        return set(config.SYMBOLS)


async def broadcast_ticks() -> None:
    """Push ticks to every connected client, filtered to their watchlist."""
    while True:
        if CLIENTS:
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


async def handler(websocket) -> None:
    """Register client with their requested symbols, stream until disconnect."""
    symbols = parse_symbols(websocket)
    CLIENTS[websocket] = symbols

    addr = websocket.remote_address
    print(f"[+] Client connected: {addr}  |  Symbols: {symbols}  |  Total clients: {len(CLIENTS)}")

    # Enable any newly requested symbols in MT5
    for symbol in symbols:
        mt5.symbol_select(symbol, True)

    try:
        await websocket.wait_closed()
    finally:
        CLIENTS.pop(websocket, None)
        print(f"[-] Client disconnected: {addr}  |  Total clients: {len(CLIENTS)}")