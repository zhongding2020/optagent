import asyncio
import time
from typing import Any, Callable, Dict

from langchain_core.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph

from .types import NodeDef


class NodeRunner:
    """Residence loop that runs a single workflow node via the agent graph."""

    def __init__(
        self,
        agent: CompiledStateGraph,
        ws_send: Callable[[Dict[str, Any]], Any],
        cancel_event: asyncio.Event,
    ):
        self.agent = agent
        self.ws_send = ws_send
        self.cancel_event = cancel_event

    def _tool_called(self, messages: list, tool_name: str) -> bool:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
                for tc in msg.tool_calls or []:
                    if tc.get("name") == tool_name:
                        return True
        return False

    def _get_step_summary(self, messages: list) -> str:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
                for tc in msg.tool_calls or []:
                    if tc.get("name") == "step_complete":
                        args = tc.get("args", {})
                        return args.get("result_summary", "")
        return ""

    async def run(
        self,
        state: Dict[str, Any],
        node_def: NodeDef,
    ) -> Dict[str, Any]:
        node_id = node_def.id
        state["current_node"] = node_id
        state["node_statuses"][node_id] = "running"
        start = time.monotonic()

        await self.ws_send({"type": "node:enter", "node": node_id})

        retries = 0
        max_retries = node_def.error_strategy.max_retries

        while not self._tool_called(state["messages"], "step_complete"):
            if self.cancel_event.is_set():
                state["node_statuses"][node_id] = "interrupted"
                await self.ws_send({"type": "graph:interrupted", "node": node_id})
                return state

            try:
                result = await self.agent.ainvoke({"messages": state["messages"]})
                state["messages"] = result.get("messages", state["messages"])

                if self._tool_called(state["messages"], "step_complete"):
                    state["node_results"][node_id] = {
                        "summary": self._get_step_summary(state["messages"])
                    }
                    break

            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    if node_def.error_strategy.on_failure == "skip":
                        state["node_statuses"][node_id] = "skipped"
                        await self.ws_send({
                            "type": "node:skipped", "node": node_id,
                            "error": str(e),
                        })
                        return state

                    state["node_statuses"][node_id] = "error"
                    state["errors"].append({"node": node_id, "error": str(e)})
                    await self.ws_send({
                        "type": "node:error", "node": node_id,
                        "error": str(e), "recoverable": False,
                    })
                    return state

                await self.ws_send({
                    "type": "node:retry", "node": node_id,
                    "attempt": retries, "max": max_retries,
                })
                continue

        elapsed = time.monotonic() - start
        state["node_durations"][node_id] = elapsed * 1000
        state["node_statuses"][node_id] = "completed"
        state["completed_nodes"].append(node_id)

        await self.ws_send({
            "type": "node:exit", "node": node_id,
            "duration_ms": elapsed * 1000,
        })
        return state
