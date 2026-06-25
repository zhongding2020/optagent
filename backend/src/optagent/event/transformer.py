 from typing import Any, AsyncIterator, Dict, Optional
 from .types import WSEvent
 
 
 class EventTransformer:
     """Converts LangGraph astream_events into optagent WS events."""
 
     SKILL_NODE_NAMES = {"SkillsMiddleware", "FilesystemMiddleware"}
 
     def __init__(self, skill_match: Optional[Dict[str, str]] = None):
         self.skill_match = skill_match or {}
 
     async def transform(
         self, event_stream: AsyncIterator[Dict[str, Any]]
     ) -> AsyncIterator[WSEvent]:
         async for event in event_stream:
             event_name = event.get("event", "")
             data = event.get("data", {}) or {}
             name = event.get("name", "")
 
             if event_name == "on_chat_model_start":
                 yield WSEvent("agent:thinking")
 
             elif event_name == "on_chat_model_stream":
                 chunk = data.get("chunk", {})
                 content = ""
                 if hasattr(chunk, "content"):
                     content = chunk.content or ""
                 elif isinstance(chunk, dict):
                     content = chunk.get("content", "") or ""
                 if content:
                     yield WSEvent("agent:token", content=content)
 
             elif event_name == "on_tool_start":
                 yield WSEvent(
                     "agent:tool_call",
                     tool=name,
                     args=data.get("input", {}),
                 )
 
             elif event_name == "on_tool_end":
                 output = data.get("output", "")
                 yield WSEvent(
                     "agent:tool_result",
                     tool=name,
                     output=str(output)[:500],
                 )
 
             elif event_name == "on_chain_start" and name in self.SKILL_NODE_NAMES:
                 yield WSEvent("skill:matched", skill=name)
