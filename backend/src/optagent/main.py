"""
OptAgent - FastAPI application entry point.

Initializes all subsystems: config, persistence, KB, skills, workflow, agent.
"""

import asyncio
import json
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import AppConfig
from .persistence.store import SessionStore
from .server.session_manager import SessionManager
from .server.ws import WSConnection
from .server import routes as R
from .skills.registry import SkillRegistry
from .workflow.loader import WorkflowLoader
from .workflow.builder import WorkflowBuilder
from .workflow.node_runner import NodeRunner
from .agent.factory import create_optagent_agent, _resolve_model
from .agent.tools import init_tools, query_knowledge_base, step_complete
from .event.transformer import EventTransformer
from .kb.retriever import KBRetriever
from .kb.ingestion import KBIngestion
from .server.routes.kb import track_search as track_kb_search
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import SystemMessage

logger = logging.getLogger("optagent")

# Global state (injected into routes)
config: AppConfig = None
store: SessionStore = None
session_manager: SessionManager = None
skill_registry: SkillRegistry = None
workflow_loader: WorkflowLoader = None
agent = None
retriever: KBRetriever = None
chat_model = None
ingestion: KBIngestion = None

_active_ws: Dict[str, WSConnection] = {}
_session_messages: Dict[str, list] = {}


async def kb_ws_broadcast(event: Dict[str, Any]):
    for ws in _active_ws.values():
        await ws.send(event)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global config, store, session_manager, skill_registry, chat_model
    global workflow_loader, agent, retriever, ingestion, chat_model

    config = AppConfig.load()

    # Init persistence
    store = SessionStore(config.persistence.sqlite_path)
    session_manager = SessionManager(store, config)

    # Init KB
    retriever = KBRetriever(
        persist_dir=config.knowledge_base.chroma_persist_dir,
        model_name=config.embedding.model,
    )
    ingestion = KBIngestion(
        retriever=retriever,
        chunk_size=config.knowledge_base.chunk_size,
        chunk_overlap=config.knowledge_base.chunk_overlap,
    )

    # Init tools
    init_tools(retriever)

    # Init skills
    skill_registry = SkillRegistry()
    for src in config.skills.sources:
        skill_registry.register(src)

    # Init workflows
    workflow_loader = WorkflowLoader(config.workflows.directory)

    # Init agent
    tools = [query_knowledge_base, step_complete]
    agent = create_optagent_agent(config, tools=tools)
    chat_model = _resolve_model(config)

    # Init routes
    R.workflows.init(workflow_loader)
    R.sessions.init(session_manager)
    R.skills.init(skill_registry)
    R.kb.init(retriever, ingestion, kb_ws_broadcast)
    R.data.init(store)

    logger.info("OptAgent started")
    yield

    # Shutdown
    await session_manager.cleanup()
    logger.info("OptAgent stopped")


app = FastAPI(lifespan=lifespan, title="OptAgent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(R.workflows.router)
app.include_router(R.sessions.router)
app.include_router(R.skills.router)
app.include_router(R.kb.router)
app.include_router(R.data.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/sessions/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    ws = WSConnection(websocket)
    _active_ws[session_id] = ws

    heartbeat_task = asyncio.create_task(ws.heartbeat())

    try:
        meta = session_manager.get_session(session_id)
        if meta and meta.status in ("interrupted", "completed"):
            await ws.send({
                "type": "graph:start",
                "session_id": session_id,
                "workflow_name": meta.workflow_name,
                "status": meta.status,
            })

        while ws.alive:
            msg = await ws.receive()
            if msg is None:
                break

            msg_type = msg.get("type")

            if msg_type == "user:terminate":
                session_manager.terminate(session_id)
                await ws.send({
                    "type": "graph:interrupted",
                    "session_id": session_id,
                    "reason": msg.get("reason", "user_cancelled"),
                })

            elif msg_type == "user:next_step":
                await ws.send({"type": "node:skipped", "node": "user_skipped"})

            elif msg_type == "user:message":
                # Process user message through the agent and stream response
                await _chat_with_agent(session_id, msg.get("content", ""), ws)

            elif msg_type == "user:resume_from":
                await _run_workflow(session_id, ws)

    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        _active_ws.pop(session_id, None)


async def _run_workflow(session_id: str, ws: WSConnection):
    """Execute workflow: load YAML, build graph, run nodes via NodeRunner."""
    meta = session_manager.get_session(session_id)
    if not meta:
        await ws.send({"type": "graph:error", "error": "Session not found"})
        return

    cancel_event = asyncio.Event()

    defn = workflow_loader.load(meta.workflow_name)
    builder = WorkflowBuilder(defn)

    node_runner = NodeRunner(agent, ws.send, cancel_event)

    async def make_handler(node):
        async def handler(state):
            return await node_runner.run(state, node)
        return handler

    handlers = {}
    for node in defn.nodes:
        handlers[node.id] = await make_handler(node)

    graph = builder.build(handlers)

    await ws.send({
        "type": "graph:start",
        "session_id": session_id,
        "workflow_name": meta.workflow_name,
        "nodes": [n.id for n in defn.nodes],
    })

    try:
        initial_state = {
            "workflow_name": meta.workflow_name,
            "messages": [],
            "current_node": "",
            "completed_nodes": [],
            "node_statuses": {},
            "node_results": {},
            "node_durations": {},
            "errors": [],
            "kb_context": [],
        }
        state = await graph.ainvoke(initial_state)
        await ws.send({"type": "graph:end", "session_id": session_id})
    except asyncio.CancelledError:
        await ws.send({"type": "graph:interrupted", "session_id": session_id})
    except Exception as e:
        logger.exception("Workflow execution failed")
        await ws.send({"type": "graph:error", "error": str(e)})


def _build_skills_system_prompt() -> list[SystemMessage]:
    """Build system prompt from all registered skills.
    
    Always rebuilt fresh so hot-plugged skills take effect immediately.
    """
    if not skill_registry:
        return []

    skills = skill_registry.get_all()
    if not skills:
        return []

    lines = [
        "你是一个工艺参数优化专家助手。你可以使用以下专业技能来指导用户完成工艺优化：",
        ""
    ]

    for skill in skills:
        lines.append(f"## 技能: {skill.name}")
        lines.append(f"描述: {skill.description}")
        skill_path = Path(skill.path)
        try:
            content = skill_path.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            body = parts[2].strip() if len(parts) >= 3 else content.strip()
            lines.append(body)
        except Exception:
            pass
        lines.append("")

    lines.append(
        "根据用户的问题选择最合适的技能来指导回答，遵循所选技能的步骤逐步引导用户。"
        "如果用户的问题不属于任何技能范围，用你的通用知识回答即可。"
    )

    return [SystemMessage(content="\n".join(lines))]


def _match_skills(user_message: str) -> list[str]:
    """Match skills via name keywords + Chinese bigram overlap."""
    if not skill_registry:
        return []

    matched: list[str] = []
    msg_lower = user_message.lower()

    # Chinese character bigrams (e.g. "优化目标" -> {"优化", "化目", "目标"})
    msg_chars = re.findall(r'[\u4e00-\u9fff]', msg_lower)
    msg_bigrams = set(msg_chars[i] + msg_chars[i+1] for i in range(len(msg_chars) - 1))

    for skill in skill_registry.get_all():
        # 1. Try English name keywords (e.g. "design-doe" -> ["design", "doe"])
        name_keywords = skill.name.replace("-", " ").lower().split()
        if any(kw in msg_lower for kw in name_keywords):
            matched.append(skill.name)
            continue

        # 2. Try Chinese bigram overlap
        desc_chars = re.findall(r'[\u4e00-\u9fff]', skill.description)
        desc_bigrams = set(desc_chars[i] + desc_chars[i+1] for i in range(len(desc_chars) - 1))
        if desc_bigrams & msg_bigrams:
            matched.append(skill.name)

    return matched


def _fix_markdown_tables(text: str) -> str:
    """Fix LLM-generated tables that lack line breaks between rows.

    Detects when a line contains a flat table with | | between merged rows:
      | H1 | H2 | H3 | | :--- | :--- | :--- | | R1 | R2 | R3 |
    and inserts proper newlines to create a valid markdown table.
    """
    lines = text.split('\n')
    result = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and '| |' in stripped and ':---' in stripped:
            cells = [c.strip() for c in stripped.split('|')]
            non_empty = [c for c in cells if c]

            col_count = None
            for idx, c in enumerate(non_empty):
                if c.startswith(':') or c.startswith('-') or c.startswith('---'):
                    col_count = idx
                    break
            if col_count is None:
                result.append(line)
                continue

            rows = []
            for i in range(0, len(non_empty), col_count):
                row_cells = non_empty[i:i+col_count]
                if len(row_cells) == col_count:
                    rows.append('| ' + ' | '.join(row_cells) + ' |')

            result.extend(rows if rows else [line])
        else:
            result.append(line)

    return '\n'.join(result)


async def _chat_with_agent(session_id: str, user_message: str, ws: Any):
    """Process a user message through deepagents agent with SkillsMiddleware + KB tools."""
    if not user_message or agent is None:
        return

    # Store user message in conversation history
    if session_id not in _session_messages:
        _session_messages[session_id] = []
    _session_messages[session_id].append(HumanMessage(content=user_message))
    await ws.send({"type": "user:message", "content": user_message})

    await ws.send({"type": "agent:thinking"})

    full_content = ""
    try:
        async for event in agent.astream_events(
            {"messages": _session_messages[session_id]},
            version="v2",
        ):
            event_name = event.get("event", "")
            data = event.get("data", {}) or {}
            name = event.get("name", "")

            if event_name == "on_chat_model_stream":
                chunk = data.get("chunk", {})
                content = ""
                if hasattr(chunk, "content"):
                    content = chunk.content or ""
                elif isinstance(chunk, dict):
                    content = chunk.get("content", "") or ""
                if content:
                    full_content += content
                    await ws.send({"type": "agent:token", "content": content})

            elif event_name == "on_tool_start":
                input_data = data.get("input", {})
                await ws.send({"type": "agent:tool_call", "tool": name, "args": input_data})
                if name == "query_knowledge_base":
                    await ws.send({
                        "type": "kb:query",
                        "query": input_data.get("query", ""),
                        "top_k": input_data.get("top_k", 5),
                    })

            elif event_name == "on_tool_end":
                output = data.get("output", "")
                await ws.send({"type": "agent:tool_result", "tool": name, "output": str(output)[:500]})
                if name == "query_knowledge_base" and output:
                    try:
                        chunks_list = json.loads(str(output)) if isinstance(output, str) else (output or [])
                        if isinstance(chunks_list, list):
                            await ws.send({"type": "kb:result", "chunks": chunks_list})
                    except Exception:
                        pass

            elif event_name == "on_chain_start":
                if name == "SkillsMiddleware":
                    skill_name = data.get("skill_name", "") or name
                    await ws.send({"type": "skill:matched", "skill": skill_name})

        if full_content:
            _session_messages[session_id].append(AIMessage(content=full_content))
            full_content = _fix_markdown_tables(full_content)
            await ws.send({"type": "agent:message", "content": full_content})
    except Exception:
        logger.exception("Agent streaming failed")
        await ws.send({"type": "graph:error", "error": "Agent processing failed"})


async def execute_session(session_id: str):
    from fastapi import HTTPException
    meta = session_manager.get_session(session_id)
    if not meta:
        raise HTTPException(404, "Session not found")
    return {"ok": True, "message": "Connect via WebSocket for execution stream"}
