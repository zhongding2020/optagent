# OptAgent Design Spec

An agent-based framework for process parameter optimization, built on deepagents (Python) + LangGraph, with a React SPA frontend and FastAPI backend.

## Overview

OptAgent is a framework that combines AI agent capabilities with structured process optimization workflows. It leverages deepagents' skill system to provide domain-specific guidance, LangGraph for stateful workflow execution, and a web UI for real-time visualization and interaction.

**Target users:** Process engineers and domain specialists who need guidance through parameter optimization workflows (DOE, factor analysis, etc.)

**Core principles:**
- **Skill-driven** — domain knowledge encoded as Markdown SKILL.md files, hot-pluggable
- **Agent-guided** — LLM agent leads the user through each optimization step
- **Knowledge-augmented** — agent proactively queries knowledge bases to ground its reasoning in domain documents
- **Visual-first** — real-time graph visualization, interactive charts, live streaming
- **Extensible** — add new skills or knowledge sources, and define entirely new workflows, without changing framework code

## Architecture

```
+--------------------------------------------+
|  Web UI (React SPA)                        |
|  Dashboard / WorkflowDetail / Analysis     |
+---------------------------+----------------+
                            | WS + REST
+---------------------------v----------------+
|  FastAPI Server                             |
|  Routes: sessions, workflows, skills, kb   |
|  WebSocket (1 per session page)            |
|  EventTransformer (LG events -> WS events) |
|  Session: asyncio task + cancel tokens     |
+-------+-------------------+----------------+
        |                   |
+-------v--------+  +-------v--------+
| Agent Runtime  |  | Knowledge Base |
| deepagents +   |  | Chroma         |
| LangGraph      |  | PDF/Markdown   |
| SkillsMiddleware|  | Async upload   |
| + KB Tool      |  | progress via WS|
| + step_complete|  |                |
+-------+--------+  +----------------+
        |
+-------v--------+
| Persistence    |
| SQLite         |
| (metadata)     |
| + LangGraph    |
|   checkpoint   |
+----------------+
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|----------|
| Agent Runtime | deepagents (Python) | LangGraph-based, built-in SkillsMiddleware |
| Graph | @langchain/langgraph (Python) | Stateful DAG, streaming, checkpointing |
| API Server | FastAPI | Native WebSocket, async, Python |
| KB Vector Store | Chroma | Lightweight, local-first, no external infra |
| KB Document Loader (v1) | LangChain loaders for local PDF + Markdown | Simple setup, no auth required |
| KB Document Loader (future) | Confluence, SharePoint, etc. | Requires OAuth, post-v1 |
| LLM | Configurable (OpenAI, Anthropic, Ollama, etc.) | deepagents supports any tool-calling model |
| Embedding | Configurable via LangChain embeddings API | Coupled to vector store choice |
| Frontend | React + Vite (SPA) | Fast dev, rich chart ecosystem |
| Real-time | WebSocket (JSON Lines) | Bidirectional, terminate support |
| Charts | ECharts | Heatmaps, Pareto, scatter for DOE |
| Skills Format | Markdown + YAML frontmatter | deepagents native, hot-pluggable |
| Workflow Definition | YAML | Declarative, no code changes needed for new workflows |
| Session Persistence | SQLite + LangGraph checkpoint | Lightweight, no external service needed |
| KB Ingestion | Background asyncio task + WS progress | Non-blocking, real-time feedback |

## Project Structure

```
optagent/
+-- backend/
|   +-- src/optagent/
|   |   +-- main.py                     # FastAPI entry
|   |   +-- config.py                   # Configuration loader
|   |   +-- agent/
|   |   |   +-- factory.py              # create_agent() wrapper
|   |   |   +-- tools.py                # Tool defs (kb_query, step_complete)
|   |   +-- event/
|   |   |   +-- transformer.py          # EventTransformer (LG -> WS)
|   |   |   +-- types.py                # WS event type definitions
|   |   +-- skills/
|   |   |   +-- registry.py             # SkillRegistry - hot-plug
|   |   |   +-- types.py
|   |   +-- workflow/
|   |   |   +-- builder.py              # WorkflowBuilder (YAML -> StateGraph)
|   |   |   +-- loader.py               # YAML validation + loading
|   |   |   +-- types.py                # WorkflowDefinition types
|   |   |   +-- node_runner.py          # Residence loop implementation
|   |   +-- server/
|   |   |   +-- routes/
|   |   |   |   +-- sessions.py
|   |   |   |   +-- workflows.py
|   |   |   |   +-- skills.py
|   |   |   |   +-- data.py
|   |   |   |   +-- kb.py
|   |   |   +-- ws.py                   # WS connection manager
|   |   |   +-- session_manager.py      # asyncio task lifecycle
|   |   +-- models/
|   |   |   +-- session.py
|   |   +-- backends/
|   |   |   +-- filesystem.py
|   |   |   +-- knowledge_base.py
|   |   +-- kb/
|   |   |   +-- ingestion.py
|   |   |   +-- retriever.py
|   |   +-- persistence/
|   |       +-- store.py                # SQLite session CRUD
|   +-- workflows/
|   |   +-- process-optimization.yaml
|   +-- skills/
|   |   +-- define-objective/SKILL.md
|   |   +-- identify-params/SKILL.md
|   |   +-- design-doe/SKILL.md
|   |   +-- collect-data/SKILL.md
|   |   +-- analyze-results/SKILL.md
|   |   +-- generate-report/SKILL.md
|   |   +-- knowledge-retrieval/SKILL.md
|   +-- kb_docs/
|   +-- data/
|   |   +-- sessions.db                 # SQLite (created at runtime)
|   |   +-- chroma/                     # Chroma persistence dir
|   |   +-- checkpoints/                # LangGraph checkpoint dir
|   +-- config.yaml
|   +-- tests/
|   +-- pyproject.toml
|
+-- frontend/
|   +-- src/
|   |   +-- App.tsx
|   |   +-- pages/
|   |   |   +-- Dashboard.tsx
|   |   |   +-- WorkflowDetail.tsx
|   |   |   +-- Analysis.tsx
|   |   |   +-- Chat.tsx
|   |   |   +-- KnowledgeBase.tsx
|   |   +-- components/
|   |   |   +-- charts/
|   |   |   |   +-- FactorRankBar.tsx
|   |   |   |   +-- CorrelationHeatmap.tsx
|   |   |   |   +-- ParetoChart.tsx
|   |   |   |   +-- DesignMatrixTable.tsx
|   |   |   |   +-- ScatterTrend.tsx
|   |   |   +-- WorkflowGraph.tsx
|   |   |   +-- SkillStatus.tsx
|   |   |   +-- AgentChat.tsx
|   |   |   +-- TerminateButton.tsx
|   |   |   +-- NextStepButton.tsx
|   |   |   +-- KbSearchResult.tsx
|   |   |   +-- KbDocumentList.tsx
|   |   |   +-- KbUploadProgress.tsx
|   |   +-- hooks/
|   |   |   +-- useWebSocket.ts
|   |   |   +-- useApi.ts
|   |   +-- types/
|   |       +-- events.ts
|   +-- package.json
|   +-- vite.config.ts
|
+-- CONTEXT.md
+-- README.md
```

## Workflow System

### Design Decision (ADR 0001)

Graphs are not hardcoded. Each workflow is defined as a YAML file. WorkflowBuilder
reads the YAML and dynamically generates a LangGraph StateGraph at load time.
Adding a new workflow type requires zero Python code changes.

### Workflow YAML Format

```yaml
name: process-optimization
description: 工艺参数优化标准工作流
version: 1.0

nodes:
  - id: define_objective
    name: 梳理优化目标
    skill_match: ["define-objective", "objective"]
    error_strategy:
      max_retries: 3
      on_failure: terminate

  - id: identify_params
    name: 识别关键工艺参数
    skill_match: ["identify-params", "parameter"]
    error_strategy:
      max_retries: 3
      on_failure: terminate

  - id: design_doe
    name: 试验设计(DOE)
    skill_match: ["design-doe", "doe", "experiment-design"]
    error_strategy:
      max_retries: 3
      on_failure: terminate

  - id: collect_data
    name: 收集试验结果
    skill_match: ["collect-data", "experiment"]
    error_strategy:
      max_retries: 2
      on_failure: skip

  - id: analyze_results
    name: 数据分析与因子提取
    skill_match: ["analyze-results", "analysis", "factor"]
    error_strategy:
      max_retries: 2
      on_failure: terminate

  - id: generate_report
    name: 生成验证报告
    skill_match: ["generate-report", "report"]
    error_strategy:
      max_retries: 1
      on_failure: skip

edges:
  - from: define_objective
    to: identify_params
  - from: identify_params
    to: design_doe
  - from: design_doe
    to: collect_data
  - from: collect_data
    to: analyze_results
  - from: analyze_results
    to: generate_report
```

### Workflow State Schema

```python
class WorkflowState(TypedDict):
    """Generic workflow state. All domain data lives in node_results."""
    workflow_name: str
    messages: list[BaseMessage]
    current_node: str
    completed_nodes: list[str]
    node_statuses: dict[str, NodeStatus]
    node_results: dict[str, Any]          # Domain data per node (generic)
    node_durations: dict[str, float]
    errors: list[NodeError]
    kb_context: list[KBDocument]          # Append-only, groups by node
```

Domain data is stored per node in `node_results[node_id]`:
- `node_results["define_objective"]["objective"]` - optimization objective
- `node_results["identify_params"]["parameters"]` - key parameters list
- `node_results["design_doe"]["design"]` - DOE design matrix
- etc.

This keeps the state schema workflow-agnostic. Different workflow types store
different fields without changing Python code.

### Node Execution: Residence Loop (ADR 0002)

Each node uses the residence loop pattern:

```python
class NodeRunner:
    def __init__(self, agent, ws, event_transformer):
        self.agent = agent
        self.ws = ws
        self.transformer = event_transformer

    async def run(self, state: WorkflowState, node_def: NodeDef) -> WorkflowState:
        while not self._goal_reached(state, node_def.id):
            # 1. Call agent with current messages
            result = await self.agent.ainvoke({"messages": state["messages"]})
            state["messages"] = result["messages"]

            # 2. Check for step_complete tool call
            if self._has_step_complete(state):
                state["node_results"][node_def.id] = self._extract_summary(state)
                break

            # 3. Check for user interruption
            user_msg = await self.ws.wait_for_message()
            if user_msg["type"] == "user:terminate":
                return self._interrupted_state(state)
            state["messages"].append(HumanMessage(user_msg["content"]))

        state["node_statuses"][node_def.id] = "completed"
        return state
```

Key properties:
- Single shared agent instance per session
- Checkpoint at node boundaries only (not per turn)
- step_complete tool signals goal reached
- User can also click "下一步" button on frontend as manual signal
- User interruption saves partial checkpoint

## EventTransformer

Converts LangGraph `astream_events` events into optagent WS events:

```python
class EventTransformer:
    async def transform(self, event_stream):
        async for event in event_stream:
            match event["event"]:
                case "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    yield {"type": "agent:token", "content": chunk.content}
                case "on_chat_model_start":
                    yield {"type": "agent:thinking"}
                case "on_tool_start":
                    tool = event["name"]
                    yield {"type": "agent:tool_call",
                           "tool": tool, "args": event["data"].get("input")}
                case "on_chain_start" if event["name"] == "SkillsMiddleware":
                    yield {"type": "skill:matched",
                           "skill": event["data"].get("skill_name")}
                case "on_tool_end":
                    pass
```

Cleanly separates LangGraph details from the WS protocol. Independently testable.

## Skill System

Skills follow the deepagents / Anthropic Agent Skills specification:
- Each skill is a directory containing SKILL.md
- SKILL.md has YAML frontmatter (name, description) + Markdown body
- SkillsMiddleware scans skill directories, loads metadata, injects into system prompt
- Agent uses progressive disclosure: sees name+description, reads full file via read_file on demand

## Knowledge Base System

### Architecture

```
KB Ingestion: PDF/Markdown -> LangChain Loader -> Splitter
               -> Embedding -> Chroma
               (async background task, progress via WS)

KB Retrieval: query_knowledge_base(query, top_k=5, filter)
               -> Chroma -> Return chunks via WS event

Tool: registered as deepagents tool alongside step_complete
```

### KB Upload Flow

```
User uploads PDF via frontend
  -> POST /api/kb/upload -> returns {"job_id": "xxx"}
  -> Background task runs ingestion pipeline:
     WS: {"type": "kb:index_progress", "job_id": "xxx", "phase": "loading",    "progress": 0.2}
     WS: {"type": "kb:index_progress", "job_id": "xxx", "phase": "splitting",  "progress": 0.5}
     WS: {"type": "kb:index_progress", "job_id": "xxx", "phase": "embedding",  "progress": 0.8}
     WS: {"type": "kb:index_progress", "job_id": "xxx", "phase": "done",       "progress": 1.0, "documents": 3}
```

### KB Events (pushed alongside agent:token, unordered between panels)

```
agent 推理:
  -> WS: agent:thinking
  -> WS: agent:token "让我查一下知识库"
  -> agent calls query_knowledge_base(...)
     -> WS: kb:query {query: "...", top_k: 5}
     -> WS: kb:result {chunks: [...]} (数百毫秒后)
  -> WS: agent:token "根据知识库..."
  -> WS: agent:token "中关于焊接工艺..."

前端分别渲染:
  - agent:token  -> chat bubble (追加流式文字)
  - kb:result    -> KB sidebar (刷新搜索结果)
```

## Hot-Plug Mechanism

SkillRegistry wraps deepagents' SkillsMiddleware sources:
- register(path) - adds a directory to middleware sources
- unregister(name) - removes a skill by name
- reload() - force-refresh all skills from configured sources
- Adding/removing SKILL.md on filesystem is reflected on next agent invocation

## Persistence

### SQLite (session metadata)

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checkpoint_id TEXT,
    node_statuses TEXT,   -- JSON
    current_node TEXT
);
```

### LangGraph Checkpoints (execution state)

LangGraph's built-in filesystem checkpoint backend stores full execution state
(messages, node statuses, node results) in `data/checkpoints/{session_id}/`.

This enables resume: user closes browser, reopens, selects the session, and the
workflow continues from the last checkpoint.

## WebSocket Protocol

### Connection Model

- Each session page opens a dedicated WS: `/ws/sessions/{session_id}`
- KB management page has its own WS: `/ws/kb`
- Heartbeat every 30 seconds (server-side ping)
- Auto-reconnect on disconnect (client retries every 1s)
- On reconnect: server pushes `graph:start` with current state to sync the UI

### Event Transformer (LangGraph -> WS)

See EventTransformer section above for the event mapping.

### Events Table

| Event Type | Direction | Description |
|------------|-----------|-------------|
| graph:start | S>C | Graph execution started, node list |
| graph:end | S>C | Graph completed, total duration |
| graph:error | S>C | Fatal error |
| graph:interrupted | S>C | User terminated, state snapshot |
| node:enter | S>C | Node started |
| node:exit | S>C | Node completed, duration and result |
| node:progress | S>C | Overall progress update |
| node:error | S>C | Node error (recoverable flag) |
| node:retry | S>C | Node retrying (attempt number) |
| node:skipped | S>C | Node skipped by error strategy |
| agent:message | S>C | Agent chat message |
| agent:token | S>C | Streaming token |
| agent:tool_call | S>C | Tool call initiated |
| agent:tool_result | S>C | Tool call completed |
| agent:thinking | S>C | Thinking indicator |
| skill:matched | S>C | Skill matched for current step |
| skill:loaded | S>C | Full SKILL.md content loaded |
| kb:query | S>C | KB search initiated |
| kb:result | S>C | KB search results |
| kb:index_update | S>C | KB index updated |
| kb:index_progress | S>C | KB upload progress |
| user:message | C>S | User input |
| user:terminate | C>S | Termination request |
| user:next_step | C>S | Manual "next step" signal |
| user:resume_from | C>S | Resume from interrupted node |

## REST API

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/workflows | List available workflow definitions |
| GET | /api/workflows/:name | Get workflow definition detail |
| POST | /api/sessions | Create session (select workflow) |
| GET | /api/sessions | List sessions |
| GET | /api/sessions/:id | Session detail |
| DELETE | /api/sessions/:id | Delete session |
| POST | /api/sessions/:id/execute | Start execution |
| POST | /api/sessions/:id/terminate | Terminate |
| GET | /api/sessions/:id/state | State snapshot |
| POST | /api/sessions/:id/resume | Resume |
| GET | /api/sessions/:id/data | Analysis data |
| GET | /api/skills | List skills |
| POST | /api/skills/register | Register skill |
| DELETE | /api/skills/:name | Unregister |
| POST | /api/skills/reload | Hot-reload |
| GET | /api/kb/documents | List indexed documents |
| POST | /api/kb/upload | Upload document (returns job_id) |
| DELETE | /api/kb/documents/:id | Remove document |
| POST | /api/kb/reindex | Re-index all sources |
| GET | /api/kb/search | Manual KB search |

## Termination Mechanism

Layered approach:

1. Primary: LangGraph interruption
   - User clicks terminate -> WS sends user:terminate
   - Server sets asyncio.Event
   - Residence loop checks event at each iteration boundary
   -> NodeInterrupt -> Checkpoint -> WS pushes graph:interrupted

2. Fallback: asyncio task cancellation (timeout guard)
   - If interruption doesn't trigger within timeout -> task.cancel()
   -> Catch CancelledError -> Save partial checkpoint

After interruption: view saved state, resume from interrupted node, or start over.

## Security (v1)

- No authentication. Server binds to `0.0.0.0` by default.
- LLM API keys read from environment variables, never logged.
- CORS configured for the frontend origin.
- README explicitly warns: "Use only on trusted networks. No auth implemented."

## Configuration

```yaml
# config.yaml
llm:
  provider: openai
  model: gpt-4o
  api_key_env: OPENAI_API_KEY

embedding:
  provider: openai
  model: text-embedding-3-small
  api_key_env: OPENAI_API_KEY

knowledge_base:
  chroma_persist_dir: ./data/chroma
  chunk_size: 1000
  chunk_overlap: 200
  default_top_k: 5

server:
  host: 0.0.0.0
  port: 8020

persistence:
  sqlite_path: ./data/sessions.db
  checkpoint_dir: ./data/checkpoints

skills:
  sources:
    - ./skills

workflows:
  directory: ./workflows
  default: process-optimization
```

## Frontend Pages

| Page | Route | Content |
|------|-------|---------|
| Dashboard | / | Workflow list, active/past sessions |
| WorkflowDetail | /sessions/:id | WorkflowGraph, AgentChat, KB sidebar, NodeDetail panel, NextStepButton, TerminateButton |
| KnowledgeBase | /kb | Document list, upload form, upload progress, search preview |
| Analysis | /sessions/:id/analysis | FactorRankBar, ParetoChart, CorrelationHeatmap, DesignMatrixTable, ScatterTrend |
| Chat | /sessions/:id/chat | Full-screen agent conversation |

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Process model | Single process | Simpler deployment |
| Graph definition | YAML (dynamic) | True extensibility, no code changes |
| Node execution | Residence loop | Checkpoint only at node boundaries |
| State schema | Generic (messages + node_results) | Workflow-agnostic, no Python changes needed |
| Agent instance | Single shared per session | No per-node startup overhead |
| State bridge | Message bridge (manual in node) | Simple, explicit, no nested graph complexity |
| Event conversion | EventTransformer class | Testable, isolated from LangGraph version |
| KB upload | Async with WS progress | Non-blocking, real-time feedback |
| WS connection | One per page + auto-reconnect + 30s heartbeat | Simple, resilient |
| Event ordering | Unordered by type (separate panels) | Tokens and KB results render independently |
| Persistence | SQLite + LangGraph checkpoint files | Lightweight, no external service |
| Security | No auth, 0.0.0.0, CORS configured | v1 simplicity, documented risk |
| Step completion | step_complete tool + manual "next step" button | Dual-path: agent-driven + user-driven |
| LLM model | Configurable via config.yaml | Support any tool-calling model provider |
| kb_context | Append-only across nodes | Frontend groups by node name for display |
| Error recovery | Per-node (configured in YAML) | Different nodes have different error tolerance |
