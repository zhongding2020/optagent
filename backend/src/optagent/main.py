"""
OptAgent - FastAPI application entry point.

Initializes all subsystems: config, persistence, KB, skills, workflow, agent.
"""

import asyncio, time
from datetime import datetime
import json
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import AppConfig
from .persistence.store import SessionStore
from .backends import register as register_backend
from .server.session_manager import SessionManager
from .server.ws import WSConnection
from .server import routes as R
from .skills.registry import SkillRegistry
from .workflow.loader import WorkflowLoader
from .agent.factory import create_optagent_agent, _resolve_model
from .agent.tools import init_tools, query_knowledge_base, step_complete, get_uploaded_data
from .agent.analysis_tools import (
    correlation_analysis,
    factor_importance,
    design_experiment,
    response_surface,
    pareto_analysis,
    anova_one_way,
)
from .models.session import NodeStatus
from .kb.retriever import KBRetriever
from .kb.ingestion import KBIngestion
from .server.routes.kb import track_search as track_kb_search
from langchain_core.messages import HumanMessage, AIMessage, message_to_dict, messages_from_dict
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
_session_token_counts: Dict[str, dict] = {}
_workflow_states: Dict[str, dict] = {}


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
    register_backend("sqlite", type(store))

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
    tools = [query_knowledge_base, step_complete, get_uploaded_data,
             correlation_analysis, factor_importance,
             design_experiment, response_surface,
             pareto_analysis, anova_one_way]
    agent = create_optagent_agent(config, tools=tools)
    chat_model = _resolve_model(config)

    # Init routes
    R.workflows.init(workflow_loader)
    R.sessions.init(session_manager, store)
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

    # Restore conversation messages from persistent store
    msg_json = store.load_session_messages(session_id)
    if msg_json:
        _session_messages[session_id] = messages_from_dict(json.loads(msg_json))

    heartbeat_task = asyncio.create_task(ws.heartbeat())
    wf_state = _get_workflow_state(session_id)
    cancel_event = asyncio.Event()

    try:
        while ws.alive:
            msg = await ws.receive()
            if msg is None:
                break

            msg_type = msg.get("type")

            if msg_type == "user:terminate":
                wf_state["cancelled"] = True
                cancel_event.set()
                session_manager.terminate(session_id)
                await ws.send({
                    "type": "graph:interrupted",
                    "session_id": session_id,
                    "reason": msg.get("reason", "user_cancelled"),
                })

            elif msg_type == "user:next_step":
                await ws.send({"type": "node:skipped", "node": "user_skipped"})

            elif msg_type == "user:message":
                content = msg.get("content", "")
                # Start workflow on first user message
                if not wf_state.get("started") and not wf_state.get("no_workflow"):
                    await _start_workflow(session_id, ws, wf_state)
                # Process message through agent and stream response
                result = await _chat_with_agent(session_id, content, ws, cancel_event)
                # Persist conversation messages to store and trim if needed
                _persist_session_messages(session_id)
                # If step_complete was called, advance to next workflow node
                if result.get("step_completed") and not wf_state.get("no_workflow"):
                    await _advance_workflow(session_id, ws, wf_state, result)

            elif msg_type == "user:resume_from":
                await ws.send({
                    "type": "graph:error",
                    "error": "Workflow execution is now integrated into chat flow",
                })

    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        cancel_event.set()
        _active_ws.pop(session_id, None)
        _workflow_states.pop(session_id, None, None)


async def _run_workflow(session_id: str, ws: WSConnection):
    """Deprecated: workflow execution is now handled inline in the WebSocket handler."""
    logger.warning("_run_workflow() is deprecated")


def _get_workflow_state(session_id: str) -> dict:
    """Get or initialize workflow state for a session."""
    if session_id in _workflow_states:
        return _workflow_states[session_id]

    meta = session_manager.get_session(session_id)
    if meta and meta.workflow_name:
        try:
            defn = workflow_loader.load(meta.workflow_name)
            wf_state = {
                "started": False,
                "cancelled": False,
                "current_node_idx": 0,
                "defn": defn,
                "node_statuses": {},
                "node_results": {},
                "node_durations": {},
                "completed_nodes": [],
            }
            _workflow_states[session_id] = wf_state
            return wf_state
        except Exception:
            logger.exception(f"Failed to load workflow for session {session_id}")

    wf_state = {"started": True, "cancelled": False, "no_workflow": True}
    _workflow_states[session_id] = wf_state
    return wf_state


async def _start_workflow(session_id: str, ws: Any, wf_state: dict):
    """Send graph:start and first node:enter events."""
    defn = wf_state["defn"]
    wf_state["started"] = True
    wf_state["current_node_idx"] = 0

    # Add workflow step instruction to conversation context
    if session_id not in _session_messages:
        _session_messages[session_id] = []
    _session_messages[session_id].append(HumanMessage(
        content=f"[工作流] 你正在执行工艺参数优化工作流。当前步骤：{defn.nodes[0].name}（{defn.nodes[0].id}）。"
                f"重要规则：请不要生成或执行任何代码（Python/R等），通过对话引导用户完成本步骤。"
                f"请根据专业技能引导用户完成本步骤目标。完成后，使用 step_complete 工具进入下一步。"
    ))

    # Persist node status to store
    meta = session_manager.get_session(session_id)
    if meta:
        meta.current_node = defn.nodes[0].id
        meta.node_statuses[defn.nodes[0].id] = NodeStatus(status="running", started_at=datetime.utcnow())
        meta.status = "running"
        store.update(meta)

    await ws.send({
        "type": "graph:start",
        "session_id": session_id,
        "workflow_name": defn.name,
        "nodes": [n.id for n in defn.nodes],
    })

    first_node = defn.nodes[0]
    wf_state["node_statuses"][first_node.id] = "running"
    await ws.send({
        "type": "node:enter",
        "node": first_node.id,
        "name": first_node.name,
    })


async def _advance_workflow(session_id: str, ws: Any, wf_state: dict, result: dict):
    """Mark current node complete and enter next node or finish workflow."""
    defn = wf_state["defn"]
    current_idx = wf_state["current_node_idx"]
    current_node = defn.nodes[current_idx]

    wf_state["node_statuses"][current_node.id] = "completed"
    wf_state["completed_nodes"].append(current_node.id)
    wf_state["node_results"][current_node.id] = {"summary": result.get("summary", "")}

    # Persist to store
    meta = session_manager.get_session(session_id)
    if meta:
        meta.node_statuses[current_node.id] = NodeStatus(
            status="completed", duration_ms=None,
            completed_at=datetime.utcnow(),
        )
        meta.node_results[current_node.id] = {"summary": result.get("summary", "")}
        store.update(meta)

    await ws.send({
        "type": "node:exit",
        "node": current_node.id,
        "summary": result.get("summary", ""),
    })

    next_idx = current_idx + 1
    if next_idx < len(defn.nodes):
        next_node = defn.nodes[next_idx]
        wf_state["current_node_idx"] = next_idx
        wf_state["node_statuses"][next_node.id] = "running"
        # Persist next node status
        if meta:
            meta.current_node = next_node.id
            meta.node_statuses[next_node.id] = NodeStatus(status="running", started_at=datetime.utcnow())
            store.update(meta)
        # Add next step instruction
        _session_messages[session_id].append(HumanMessage(
            content=f"[工作流] 步骤“{current_node.name}”已完成。现在进入下一步：{next_node.name}（{next_node.id}）。"
                    f"重要规则：请不要生成或执行任何代码（Python/R等），通过对话引导用户完成本步骤。"
                    f"请根据新步骤的专业技能引导用户完成目标。完成后使用 step_complete 工具。"
        ))
        await ws.send({
            "type": "node:enter",
            "node": next_node.id,
            "name": next_node.name,
        })
    else:
        meta = session_manager.get_session(session_id)
        if meta:
            meta.status = "completed"
            meta.node_results = wf_state.get("node_results", {})
            store.update(meta)
        await ws.send({
            "type": "graph:end",
            "session_id": session_id,
        })

MAX_CONTEXT_MESSAGES = 30

def _persist_session_messages(session_id: str):
    """Save conversation messages to store and trim if needed."""
    messages = _session_messages.get(session_id, [])
    if not messages:
        return

    # Trim if over threshold
    if len(messages) > MAX_CONTEXT_MESSAGES + 10:
        keep_count = max(MAX_CONTEXT_MESSAGES, 5)
        trimmed = messages[-keep_count:]
        _session_messages[session_id] = [HumanMessage(content="[前几轮对话已折叠，继续当前对话]")] + trimmed

    # Save to store
    try:
        msg_json = json.dumps([message_to_dict(m) for m in _session_messages[session_id]])
        store.save_session_messages(session_id, msg_json)
    except Exception:
        logger.exception("Failed to persist session messages")


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


async def _chat_with_agent(session_id: str, user_message: str, ws: Any, cancel_event = None):
    """Process a user message through deepagents agent.
    
    Returns a dict with workflow signals:
        step_completed (bool): whether the agent called step_complete
        summary (str): result summary from step_complete if called
    """
    if not user_message or agent is None:
        return {"step_completed": False, "summary": ""}

    # Store user message in conversation history
    if session_id not in _session_messages:
        _session_messages[session_id] = []
    _session_messages[session_id].append(HumanMessage(content=user_message))
    await ws.send({"type": "user:message", "content": user_message})

    await ws.send({"type": "agent:thinking"})

    full_content = ""
    output_tokens = 0
    step_completed = False
    step_summary = ""
    try:
        async for event in agent.astream_events(
            {"messages": _session_messages[session_id]},
            version="v2",
        ):
            if cancel_event and cancel_event.is_set():
                break
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
                    output_tokens += 1
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
                elif name == "step_complete":
                    step_completed = True
                    step_summary = (
                        input_data.get("result_summary", "")
                        if isinstance(input_data, dict) else ""
                    )

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

        # Track token usage and send stats
        input_tokens = len(user_message) // 4 + 1
        if session_id not in _session_token_counts:
            _session_token_counts[session_id] = {"input": 0, "output": 0}
        _session_token_counts[session_id]["input"] += input_tokens
        _session_token_counts[session_id]["output"] += output_tokens
        await ws.send({
            "type": "agent:stats",
            "session_id": session_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "session_input_total": _session_token_counts[session_id]["input"],
            "session_output_total": _session_token_counts[session_id]["output"],
        })

    except Exception:
        logger.exception("Agent streaming failed")
        await ws.send({"type": "graph:error", "error": "Agent processing failed"})
    return {"step_completed": step_completed, "summary": step_summary}


async def execute_session(session_id: str):
    from fastapi import HTTPException
    meta = session_manager.get_session(session_id)
    if not meta:
        raise HTTPException(404, "Session not found")
    return {"ok": True, "message": "Connect via WebSocket for execution stream"}
