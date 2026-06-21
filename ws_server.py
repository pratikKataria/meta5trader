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


CLIENTS: dict[any, set[str]] = {}


def validate_symbols(requested: set[str]) -> tuple[set[str], set[str]]:
    """
    Check each requested symbol against MT5.
    Returns (valid, invalid) sets.
    """
    valid   = set()
    invalid = set()

    for symbol in requested:
        info = mt5.symbol_info(symbol)
        if info is not None:
            mt5.symbol_select(symbol, True)  # enable in Market Watch
            valid.add(symbol)
        else:
            invalid.add(symbol)

    return valid, invalid


def parse_symbols(websocket) -> set[str]:
    """Extract symbols from ?symbols= query param and validate against MT5."""
    try:
        path      = websocket.request.path
        query     = parse_qs(urlparse(path).query)
        raw       = query.get("symbols", [""])[0]
        requested = {s.strip().upper() for s in raw.split(",") if s.strip()}

        if not requested:
            return set()

        valid, invalid = validate_symbols(requested)

        if invalid:
            print(f"  [!] Invalid/unknown MT5 symbols ignored: {invalid}")

        return valid

    except Exception as e:
        print(f"  [!] parse_symbols error: {e}")
        return set()


async def broadcast_ticks() -> None:
    """Push ticks to every connected client, filtered to their watchlist."""
    while True:
        if CLIENTS:
            all_needed = set().union(*CLIENTS.values())

            # Fetch once per unique symbol across all clients
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
    """Register client, validate their symbols against MT5, stream until disconnect."""
    symbols = parse_symbols(websocket)
    addr    = websocket.remote_address

    if not symbols:
        # Send error and close if no valid symbols provided
        await websocket.send(json.dumps({
            "error": "No valid symbols. Provide ?symbols=EURUSD,XAUUSD etc."
        }))
        await websocket.close()
        print(f"[!] Rejected client {addr} — no valid symbols")
        return

    CLIENTS[websocket] = symbols
    print(f"[+] Client connected: {addr}  |  Symbols: {symbols}  |  Total: {len(CLIENTS)}")

    try:
        await websocket.wait_closed()
    finally:
        CLIENTS.pop(websocket, None)
        print(f"[-] Client disconnected: {addr}  |  Total: {len(CLIENTS)}")