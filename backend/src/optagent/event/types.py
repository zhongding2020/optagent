from typing import Any, Dict, Literal, Optional

WSEventType = Literal[
    "graph:start", "graph:end", "graph:error", "graph:interrupted",
    "node:enter", "node:exit", "node:progress", "node:error",
    "node:retry", "node:skipped",
    "agent:message", "agent:token", "agent:tool_call",
    "agent:tool_result", "agent:thinking",
    "skill:matched", "skill:loaded",
    "kb:query", "kb:result", "kb:index_update", "kb:index_progress",
]


class WSEvent:
    def __init__(self, type: WSEventType, **data: Any):
        self.payload: Dict[str, Any] = {"type": type, **data}
