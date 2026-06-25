import asyncio
import json
from typing import Any, Callable, Dict, Optional
from fastapi import WebSocket


class WSConnection:
    """Manages a single WebSocket connection with heartbeat."""

    def __init__(self, websocket: WebSocket, heartbeat_interval: int = 30):
        self.websocket = websocket
        self.heartbeat_interval = heartbeat_interval
        self._running = True

    async def send(self, data: Dict[str, Any]):
        try:
            await self.websocket.send_json(data)
        except Exception:
            self._running = False

    async def receive(self) -> Optional[Dict[str, Any]]:
        try:
            raw = await self.websocket.receive_text()
            return json.loads(raw)
        except Exception:
            self._running = False
            return None

    async def heartbeat(self):
        while self._running:
            await asyncio.sleep(self.heartbeat_interval)
            try:
                await self.websocket.send_json({"type": "ping"})
            except Exception:
                self._running = False

    @property
    def alive(self) -> bool:
        return self._running
