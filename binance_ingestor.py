import asyncio
import json
import threading
from typing import Iterable, List

import websockets

from data_store import DataStore


class BinanceIngestor:
    """
    Very small Binance trade stream ingestor.

    Runs in a background thread with its own asyncio loop, writing ticks into
    the shared DataStore. Symbols are Binance spot symbols like 'btcusdt'.
    """

    def __init__(self, store: DataStore, symbols: Iterable[str]):
        self.store = store
        self.symbols = [s.lower() for s in symbols]
        # Use optional annotation compatible with older Python versions
        self._thread: "threading.Thread | None"
        self._thread = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run_loop(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        streams = "/".join(f"{s}@trade" for s in self.symbols)
        url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    async for msg in ws:
                        if self._stop_event.is_set():
                            break
                        self._handle_message(msg)
            except Exception:
                # Backoff a little before reconnect
                await asyncio.sleep(2)

    def _handle_message(self, raw: str) -> None:
        try:
            data = json.loads(raw)
            payload = data.get("data", {})
            symbol = payload.get("s")
            price = float(payload.get("p"))
            qty = float(payload.get("q"))
            ts = float(payload.get("T"))  # trade time ms
        except Exception:
            return

        if not symbol:
            return

        self.store.insert_tick(ts_ms=ts, symbol=symbol, price=price, qty=qty)


