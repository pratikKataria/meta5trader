# ==========================
# ws_server.py — Per-client symbol filtering via URL query params
# ==========================

import asyncio
import json
import time
from urllib.parse import urlparse, parse_qs

import MetaTrader5 as mt5
import websockets

import config


CLIENTS: dict[any, set[str]] = {}
_id_counter = 0


def next_id() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter


def validate_symbols(requested: set[str]) -> tuple[set[str], set[str]]:
    valid   = set()
    invalid = set()
    for symbol in requested:
        info = mt5.symbol_info(symbol)
        if info is not None:
            mt5.symbol_select(symbol, True)
            valid.add(symbol)
        else:
            invalid.add(symbol)
    return valid, invalid


def parse_symbols(websocket) -> set[str]:
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


def build_tick(symbol: str) -> dict | None:
    """
    Build a tick payload that mirrors the Flutter TickData class.
    Returns None if MT5 data is unavailable.
    """
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)

    if tick is None or info is None:
        return None

    last_price   = tick.last if tick.last != 0.0 else tick.bid
    close        = info.session_close if info.session_close != 0.0 else last_price
    change       = round(last_price - close, info.digits)
    change_pct   = round((change / close * 100) if close != 0.0 else 0.0, 4)

    return {
        "id":              next_id(),
        "instrumentToken": info.custom_int if hasattr(info, "custom_int") else abs(hash(symbol)) & 0x7FFFFFFF,
        "tradingSymbol":   symbol,
        "exchange":        info.path.split("\\")[0] if info.path else "MT5",
        "lastPrice":       last_price,
        "change":          change,
        "changePercent":   change_pct,
        "open":            info.session_open,
        "high":            info.session_price_limit_max if info.session_price_limit_max != 0.0 else tick.ask,
        "low":             info.session_price_limit_min if info.session_price_limit_min != 0.0 else tick.bid,
        "close":           close,
        "volume":          float(tick.volume_real if tick.volume_real != 0.0 else tick.volume),
        "buyQuantity":     float(info.volume_min),   # replace with order book data if available
        "sellQuantity":    float(info.volume_step),  # replace with order book data if available
        "timestamp":       int(tick.time),           # Unix epoch seconds (int), matches Dart int
    }


async def broadcast_ticks() -> None:
    """Push ticks to every connected client, filtered to their watchlist."""
    while True:
        if CLIENTS:
            all_needed = set().union(*CLIENTS.values())

            tick_map: dict[str, dict] = {}
            for symbol in all_needed:
                payload = build_tick(symbol)
                if payload is not None:
                    tick_map[symbol] = payload

            disconnected = set()
            for client, symbols in CLIENTS.items():
                client_payload = [tick_map[s] for s in symbols if s in tick_map]
                if not client_payload:
                    continue
                try:
                    await client.send(json.dumps(client_payload))
                except websockets.ConnectionClosed:
                    disconnected.add(client)

            for client in disconnected:
                CLIENTS.pop(client, None)

        await asyncio.sleep(config.TICK_INTERVAL_SECONDS)


async def handler(websocket) -> None:
    symbols = parse_symbols(websocket)
    addr    = websocket.remote_address

    if not symbols:
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