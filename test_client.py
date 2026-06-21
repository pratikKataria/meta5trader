# ==========================
# test_client.py — Quick test for the WebSocket tick server
# ==========================

import asyncio
import json

import websockets

WS_URL = "ws://localhost:8765"


async def listen():
    print(f"Connecting to {WS_URL} ...\n")

    async with websockets.connect(WS_URL) as ws:
        print("Connected. Receiving ticks (Ctrl+C to stop):\n")

        async for message in ws:
            ticks = json.loads(message)

            for tick in ticks:
                print(
                    f"[{tick['time']}]  {tick['symbol']}"
                    f"  Bid: {tick['bid']}  Ask: {tick['ask']}"
                )

            print("-" * 56)


if __name__ == "__main__":
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        print("\nDisconnected.")
