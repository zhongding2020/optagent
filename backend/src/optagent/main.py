"""
OptAgent - FastAPI application entry point.

Initializes all subsystems: config, persistence, KB, skills, workflow, agent.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
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
from .agent.tools import init_tools
from .event.transformer import EventTransformer
from .kb.retriever import KBRetriever
from .kb.ingestion import KBIngestion

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
        embedding_model=config.embedding.model,
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
    agent = create_optagent_agent(config)
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


@app.post("/api/sessions/{session_id}/execute")
async def _chat_with_agent(session_id: str, user_message: str, ws: Any):
    """Process a user message through the LLM and stream the response."""
    if not user_message or chat_model is None:
        return

    if session_id not in _session_messages:
        _session_messages[session_id] = []

    # Add and echo user message
    _session_messages[session_id].append(HumanMessage(content=user_message))
    await ws.send({"type": "user:message", "content": user_message})

    await ws.send({"type": "agent:thinking"})

    try:
        full_content = ""
        async for chunk in chat_model.astream(_session_messages[session_id]):
            if hasattr(chunk, "content") and chunk.content:
                full_content += chunk.content
                await ws.send({"type": "agent:token", "content": chunk.content})

        if full_content:
            _session_messages[session_id].append(AIMessage(content=full_content))
            await ws.send({"type": "agent:message", "content": full_content})
    except Exception:
        import traceback
        traceback.print_exc()
        await ws.send({"type": "graph:error", "error": "Agent processing failed"})


async def execute_session(session_id: str):
    from fastapi import HTTPException
    meta = session_manager.get_session(session_id)
    if not meta:
        raise HTTPException(404, "Session not found")
    return {"ok": True, "message": "Connect via WebSocket for execution stream"}
