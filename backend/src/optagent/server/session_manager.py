import asyncio
from typing import Any, Callable, Dict, Optional
from ..persistence.store import SessionStore
from ..models.session import SessionMetadata, SessionCreate
from ..config import AppConfig


class SessionManager:
    def __init__(self, store: SessionStore, config: AppConfig):
        self.store = store
        self.config = config
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._cancel_events: Dict[str, asyncio.Event] = {}

    def create_session(self, req: SessionCreate) -> SessionMetadata:
        session = self.store.create(req)
        return session

    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        return self.store.get(session_id)

    def list_sessions(self) -> list[SessionMetadata]:
        return self.store.list()

    def delete_session(self, session_id: str):
        if session_id in self._running_tasks:
            self.terminate(session_id)
        self.store.delete(session_id)

    def start_execution(
        self,
        session_id: str,
        runner: Callable,  # coroutine function
    ):
        cancel_event = asyncio.Event()
        self._cancel_events[session_id] = cancel_event

        meta = self.store.get(session_id)
        if meta:
            meta.status = "running"
            self.store.update(meta)

        task = asyncio.create_task(runner(session_id, cancel_event))
        self._running_tasks[session_id] = task

    def terminate(self, session_id: str):
        if session_id in self._cancel_events:
            self._cancel_events[session_id].set()
        if session_id in self._running_tasks:
            self._running_tasks[session_id].cancel()

    def is_running(self, session_id: str) -> bool:
        return session_id in self._running_tasks and not self._running_tasks[session_id].done()

    async def cleanup(self):
        for session_id, task in self._running_tasks.items():
            if not task.done():
                task.cancel()
        self._running_tasks.clear()
        self._cancel_events.clear()
