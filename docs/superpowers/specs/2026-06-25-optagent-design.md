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
                            | WebSocket + REST
+---------------------------v----------------+
|  FastAPI Server                             |
|  Routes: sessions, workflows, skills, kb   |
|  WebSocket: event encoding + push          |
|  SessionManager: tasks + cancel tokens     |
+-------+-------------------+----------------+
        |                   |
+-------v--------+  +-------v--------+
| Agent Runtime  |  | Knowledge Base |
| deepagents +   |  |                |
| LangGraph      |  | Chroma         |
| SkillsMiddleware|  | + PDF/Markdown |
| + KB Tool      |  |                |
|                |  |                |
+-------+--------+  +----------------+
        |
+-------v--------+
| Workflow       |
| Builder        |
| YAML -> Graph  |
| (动态生成)      |
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
| KB Ingestion | Python script + cron / webhook | Re-index on document update |

## Project Structure

```
optagent/
+-- backend/
|   +-- src/optagent/
|   |   +-- main.py                     # FastAPI entry
|   |   +-- config.py                   # Configuration (model, kb paths, etc.)
|   |   +-- agent/
|   |   |   +-- factory.py              # create_agent() wrapper
|   |   |   +-- tools.py                # Tool definitions (incl. kb_query)
|   |   +-- skills/
|   |   |   +-- registry.py             # SkillRegistry - hot-plug
|   |   |   +-- types.py                # SkillMetadata types
|   |   +-- workflow/
|   |   |   +-- builder.py              # WorkflowBuilder - YAML -> StateGraph
|   |   |   +-- loader.py               # Workflow YAML loader + validation
|   |   |   +-- types.py                # WorkflowDefinition type
|   |   +-- server/
|   |   |   +-- routes/
|   |   |   |   +-- sessions.py
|   |   |   |   +-- workflows.py        # /api/workflows - list/run
|   |   |   |   +-- skills.py
|   |   |   |   +-- data.py
|   |   |   |   +-- kb.py
|   |   |   +-- ws.py                   # WebSocket manager
|   |   |   +-- session_manager.py      # Session lifecycle
|   |   +-- models/
|   |   |   +-- session.py              # Pydantic models
|   |   +-- backends/
|   |   |   +-- filesystem.py
|   |   |   +-- knowledge_base.py       # KB abstraction + vector store
|   |   +-- kb/
|   |       +-- ingestion.py            # Document ingestion pipeline
|   |       +-- retriever.py            # Query + rerank logic
|   +-- workflows/                      # Workflow YAML definitions
|   |   +-- process-optimization.yaml   # 工艺参数优化工作流
|   +-- skills/                         # Example skills
|   |   +-- define-objective/SKILL.md
|   |   +-- identify-params/SKILL.md
|   |   +-- design-doe/SKILL.md
|   |   +-- collect-data/SKILL.md
|   |   +-- analyze-results/SKILL.md
|   |   +-- generate-report/SKILL.md
|   |   +-- knowledge-retrieval/SKILL.md
|   +-- kb_docs/
|   |   +-- doe-handbook/
|   |   +-- process-specs/
|   +-- config.yaml                     # Application configuration
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
|   |   |   +-- KbSearchResult.tsx
|   |   |   +-- KbDocumentList.tsx
|   |   +-- hooks/
|   |   |   +-- useWebSocket.ts
|   |   |   +-- useApi.ts
|   |   +-- types/
|   |       +-- events.ts
|   +-- package.json
|   +-- vite.config.ts
|
+-- README.md
```

## Workflow System

### Design Decision

Graphs are not hardcoded. Each workflow is defined as a YAML file. WorkflowBuilder reads the YAML and dynamically generates a LangGraph StateGraph at load time. This makes the framework truly extensible — adding a new workflow type does not require Python code changes.

### Workflow YAML Format

```yaml
# workflows/process-optimization.yaml
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
      on_failure: skip           # 用户可以手动补充数据后resume

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
    workflow_name: str
    messages: list[BaseMessage]          # Agent conversation history
    current_node: str                    # Current graph node
    completed_nodes: list[str]           # Nodes already executed
    node_statuses: dict[str, NodeStatus] # pending/running/completed/error/skipped
    node_results: dict[str, Any]         # Per-node output data
    node_durations: dict[str, float]     # Per-node execution time
    errors: list[NodeError]              # Error log
    kb_context: list[KBDocument]         # Retrieved KB docs (append-only across nodes)

    # Domain data (populated incrementally per workflow)
    optimization_objective: str
    key_parameters: list[Parameter]
    doe_design: DOEDesign
    experiment_results: list[ExperimentResult]
    analysis: AnalysisResult
    report: str
```

### Node Error Policy (per node, from YAML)

| on_failure | Behavior |
|------------|----------|
| terminate | Graph stops, saves checkpoint, user can resume |
| skip | Graph marks node as skipped, continues to next node |
| retry | Retries up to max_retries, then falls back to on_failure |

Recoverable errors (retry triggers):
- User input conflict or insufficient data
- Tool execution error (file not found, etc.)
- KB query failure

Unrecoverable errors (immediate terminate):
- LLM call failure (timeout, API error)
- Graph-level fatal error

## Skill System

Skills follow the deepagents / Anthropic Agent Skills specification:
- Each skill is a directory containing SKILL.md
- SKILL.md has YAML frontmatter (name, description) + Markdown body
- SkillsMiddleware scans skill directories, loads metadata, injects into system prompt
- Agent uses progressive disclosure: sees name+description, reads full file via read_file on demand

## Knowledge Base System

### Architecture

```
+--------------------------------------------------+
|  Knowledge Base                                   |
|                                                    |
|  Ingestion Pipeline:                              |
|    PDF/Markdown -> LangChain Loader -> Splitter   |
|      -> Embedding (configurable) -> Chroma         |
|                                                    |
|  Retrieval Pipeline:                               |
|    query_knowledge_base(query, top_k=5)            |
|      -> Chroma -> Rerank -> Return chunks          |
|                                                    |
|  Tool Layer:                                       |
|    query_knowledge_base registered as deepagents   |
|    tool, agent calls it just like read_file        |
+--------------------------------------------------+
```

### KB Tool

```python
@tool
def query_knowledge_base(
    query: str,
    top_k: int = 5,
    filter: dict | None = None
) -> list[Document]:
    """Search the knowledge base for documents related to the query.

    Use this when you need domain-specific knowledge about process
    optimization, DOE methods, material specifications, or best practices
    that may not be covered by general knowledge.

    Args:
        query: The search query, be specific about what you need
        top_k: Number of documents to return (default: 5)
        filter: Optional metadata filter (e.g. {"source": "doe-handbook"})
    """
    return retriever.search(query=query, top_k=top_k, filter=filter)
```

### KB Skill (knowledge-retrieval/SKILL.md)

```
---
name: knowledge-retrieval
description: 当你需要查找工艺规范、DOE方法、材料参数或历史案例时，主动查询知识库
---

# Knowledge Retrieval Skill

## When to Use

- 用户提及的材料/工艺参数需要查标准
- 用户想参考历史案例或已有DOE设计
- 你需要验证某个参数的合理取值范围
- 用户询问最佳实践或行业标准

## Progressive Search Strategy

1. 初始查询（宽泛）: 先用关键词做宽泛搜索，了解KB中有什么
2. 针对性查询（精确）: 基于用户的后续输入缩小范围
3. 深入查询（引用）: 需要引用具体数据或公式时精准定位

## Examples

用户: "我要优化焊接工艺"
  -> query("焊接工艺参数优化 DOE 方法")
  -> 返回: DOE手册章节、历史焊接DOE案例

用户: "温度范围是150-200°C"
  -> query("焊接温度 150-200°C 推荐参数 材料")
  -> 返回: 材料焊接温度规范表、历史参数记录

## 禁止

- 不要在没有用户上下文的情况下盲目查询KB
- 不要把KB结果当作唯一真理，需要结合用户的实际场景
```

### KB Query Event Flow (Progressive)

```
User: "我要优化焊接工艺良率"
                |
                v
Agent (in define_objective node) reads SKILL.md
                |
                v
query_knowledge_base("焊接工艺参数优化 DOE 方法 top_k=5")
                |
WS: { type: "kb:query",      query: "...", top_k: 5 }
WS: { type: "kb:result",     query: "...", chunks: [{title, snippet, source}], total: 5 }
                |
Agent 消化KB结果后，向用户提问
                |
User: "温度是150-200°C，压力3-5bar"
                |
                v
query_knowledge_base("焊接温度压力 150-200C 3-5bar 田口方法")
                |
WS: { type: "kb:query",      query: "..." }
WS: { type: "kb:result",     query: "...", chunks: [...] }
                |
Agent 整合KB信息 + 用户输入 -> 输出结构化目标
```

### KB Document Management

| Action | REST API | Description |
|--------|----------|-------------|
| List index | GET /api/kb/documents | List all indexed documents |
| Upload | POST /api/kb/upload | Upload PDF/Markdown for indexing |
| Delete | DELETE /api/kb/documents/:id | Remove document from index |
| Re-index | POST /api/kb/reindex | Full re-index of all sources |
| Search | GET /api/kb/search?q=... | Manual search for testing |

## Configuration

```yaml
# config.yaml
llm:
  provider: openai           # openai | anthropic | ollama | ...
  model: gpt-4o              # model name for the chosen provider
  api_key_env: OPENAI_API_KEY

embedding:
  provider: openai           # shared with llm provider or independent
  model: text-embedding-3-small
  api_key_env: OPENAI_API_KEY

knowledge_base:
  chroma_persist_dir: ./data/chroma
  chunk_size: 1000
  chunk_overlap: 200
  default_top_k: 5

server:
  host: 0.0.0.0
  port: 8000

skills:
  sources:
    - ./skills

workflows:
  directory: ./workflows
  default: process-optimization
```

## Hot-Plug Mechanism

SkillRegistry wraps deepagents' SkillsMiddleware sources:
- register(path) - adds a directory to middleware sources
- unregister(name) - removes a skill by name
- reload() - force-refresh all skills from configured sources
- Adding/removing SKILL.md on filesystem is reflected on next agent invocation

## WebSocket Event Protocol

All events are JSON with a type field:

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
| kb:query | S>C | KB search initiated (query + filters) |
| kb:result | S>C | KB search results (chunks with snippets) |
| kb:index_update | S>C | KB index updated (new/deleted docs) |
| user:message | C>S | User input |
| user:terminate | C>S | Termination request |
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
| POST | /api/kb/upload | Upload document for indexing |
| DELETE | /api/kb/documents/:id | Remove document |
| POST | /api/kb/reindex | Re-index all sources |
| GET | /api/kb/search | Manual KB search |

## Termination Mechanism

Layered approach:

1. Primary: LangGraph interruption - User clicks terminate -> WS sends user:terminate -> Server sets asyncio.Event -> Graph checks at tool call boundaries -> LangGraph NodeInterrupt -> Checkpoint -> WS pushes graph:interrupted

2. Fallback: asyncio task cancellation - If no interruption within timeout -> task.cancel() -> Catch CancelledError -> Save partial checkpoint

KB queries during termination are gracefully cancelled; partial results are discarded.

After interruption: view saved state, resume from interrupted node, or start over.

## Frontend Pages

| Page | Route | Content |
|------|-------|---------|
| Dashboard | / | Available workflows, active/past sessions |
| WorkflowDetail | /sessions/:id | DAG, node status, chat, terminate, KB search panel |
| KnowledgeBase | /kb | Document management, upload, search preview |
| Analysis | /sessions/:id/analysis | Factor rank, Pareto, heatmap, DOE matrix, scatter |
| Chat | /sessions/:id/chat | Full-screen agent conversation |

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Process model | Single process | Simpler deployment |
| Graph definition | YAML (dynamic) | Adding new workflows requires no code changes |
| Frontend | React SPA (Vite) | No SEO needed for dashboard |
| Charts | ECharts | Better complex chart support |
| WS protocol | JSON Lines | Simple, parseable |
| Skill-node mapping | skill_match keywords in YAML | Agent-driven, flexible per workflow |
| Termination | InterruptOnConfig | Graceful, state-preserving |
| KB vector store | Chroma | Local-first, no external infra needed |
| KB query | Tool-based (agent decides) | Aligns with progressive disclosure pattern |
| KB events | kb:query / kb:result in WS | Frontend shows search progress transparently |
| LLM model | Configurable via config.yaml | Support any tool-calling model provider |
| kb_context | Append-only across nodes | Frontend groups by node name for display |
| Error recovery | Per-node (configured in YAML) | Different nodes have different error tolerance |
| Workflow YAML format | Node list + edge list + per-node error strategy | Declarative, deterministic, easy to validate |
