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
- **Extensible** — add new skills or knowledge sources without changing graph code

## Architecture

```
+--------------------------------------------+
|  Web UI (React SPA)                        |
|  Dashboard / WorkflowDetail / Analysis     |
+---------------------------+----------------+
                            | WebSocket + REST
+---------------------------v----------------+
|  FastAPI Server                             |
|  Routes: sessions, skills, data, kb        |
|  WebSocket: event encoding + push          |
|  SessionManager: tasks + cancel tokens     |
+-------+-------------------+----------------+
        |                   |
+-------v--------+  +-------v--------+
| Agent Runtime  |  | Knowledge Base |
| deepagents +   |  |                |
| LangGraph      |  | Vector Store   |
| SkillsMiddleware|  | (Chroma/Qdrant)|
| + KB Tool      |  | + Files (PDF/  |
|                |  |   Markdown)    |
+----------------+  +----------------+
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|----------|
| Agent Runtime | deepagents (Python) | LangGraph-based, built-in SkillsMiddleware |
| Graph | @langchain/langgraph (Python) | Stateful DAG, streaming, checkpointing |
| API Server | FastAPI | Native WebSocket, async, Python |
| KB Vector Store | Chroma (embeddings via OpenAI/text-embedding-3-small) | Lightweight, local-first, easy setup |
| KB Document Loader | LangChain document loaders | PDF, Markdown, Confluence, SharePoint |
| Frontend | React + Vite (SPA) | Fast dev, rich chart ecosystem |
| Real-time | WebSocket (JSON Lines) | Bidirectional, terminate support |
| Charts | ECharts | Heatmaps, Pareto, scatter for DOE |
| Skills Format | Markdown + YAML frontmatter | deepagents native, hot-pluggable |
| KB Ingestion Pipeline | Python script + cron / webhook | Re-index on document update |

## Project Structure

```
optagent/
+-- backend/
|   +-- src/optagent/
|   |   +-- main.py                     # FastAPI entry
|   |   +-- agent/
|   |   |   +-- factory.py              # create_agent() wrapper
|   |   |   +-- tools.py                # Tool definitions (incl. kb_query)
|   |   +-- skills/
|   |   |   +-- registry.py             # SkillRegistry - hot-plug
|   |   |   +-- types.py                # SkillMetadata types
|   |   +-- graph/
|   |   |   +-- builder.py              # StateGraph builder
|   |   |   +-- nodes.py                # Node definitions
|   |   +-- server/
|   |   |   +-- routes/
|   |   |   |   +-- sessions.py
|   |   |   |   +-- skills.py
|   |   |   |   +-- data.py
|   |   |   |   +-- kb.py               # /api/kb - manage index
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
|   +-- skills/                         # Example skills
|   |   +-- define-objective/SKILL.md
|   |   +-- identify-params/SKILL.md
|   |   +-- design-doe/SKILL.md
|   |   +-- collect-data/SKILL.md
|   |   +-- analyze-results/SKILL.md
|   |   +-- generate-report/SKILL.md
|   |   +-- knowledge-retrieval/SKILL.md   # KB 查询 skill
|   +-- kb_docs/                        # Example KB documents
|   |   +-- doe-handbook/
|   |   +-- process-specs/
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
|   |   |   +-- KbSearchResult.tsx       # KB 搜索结果展示
|   |   |   +-- KbDocumentList.tsx       # KB 文档管理面板
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

## Workflow Graph Design

The process optimization workflow is a LangGraph StateGraph with 6 sequential nodes. Each node uses a deepagents agent (with SkillsMiddleware) to:
1. Read state (previous step results)
2. SkillsMiddleware injects available skill descriptions into system prompt
3. Agent selects and reads the matching SKILL.md based on current context
4. Agent follows skill instructions to guide user through the step
5. As needed, agent queries knowledge base via `query_knowledge_base` tool
6. Output updates state, transitions to next node

```
define_objective >> identify_params >> design_doe
     |                                        |
     v                                        v
generate_report << analyze_results << collect_data

Throughout: agent may call query_knowledge_base() at any node
             to ground its reasoning in domain documents
```

### State Schema

```python
class OptimizationState(TypedDict):
    messages: list[BaseMessage]          # Agent conversation history
    current_node: str                    # Current graph node
    node_statuses: dict[str, NodeStatus] # Per-node status
    node_results: dict[str, Any]         # Per-node output data
    node_durations: dict[str, float]     # Per-node execution time
    errors: list[NodeError]              # Error log
    kb_context: list[KBDocument]         # Retrieved KB documents (cross-node)

    # Domain data (populated incrementally)
    optimization_objective: str
    key_parameters: list[Parameter]
    doe_design: DOEDesign
    experiment_results: list[ExperimentResult]
    analysis: AnalysisResult
    report: str
```

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
|      -> Embedding (OpenAI) -> Vector Store         |
|                                                    |
|  Retrieval Pipeline:                               |
|    query_knowledge_base(query, top_k=5)            |
|      -> Vector Store -> Rank -> Return chunks      |
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
    ...
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
| node:error | S>C | Recoverable node error |
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
| POST | /api/sessions | Create session |
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
| Dashboard | / | Active/past sessions, status, duration |
| WorkflowDetail | /sessions/:id | DAG, node status, chat, terminate, KB search panel |
| KnowledgeBase | /kb | Document management, upload, search preview |
| Analysis | /sessions/:id/analysis | Factor rank, Pareto, heatmap, DOE matrix, scatter |
| Chat | /sessions/:id/chat | Full-screen agent conversation |

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Process model | Single process | Simpler deployment |
| Frontend | React SPA (Vite) | No SEO needed for dashboard |
| Charts | ECharts | Better complex chart support |
| WS protocol | JSON Lines | Simple, parseable |
| Skill-node mapping | Dynamic (not hardcoded) | Adding skills doesn't need graph changes |
| Termination | InterruptOnConfig | Graceful, state-preserving |
| KB vector store | Chroma | Local-first, no external infra needed |
| KB query | Tool-based (agent decides) | Aligns with progressive disclosure pattern |
| KB retrieval | query tool + KB skill description | Agent actively chooses when and what to search |
| KB events | kb:query / kb:result in WS | Frontend shows search progress transparently |
