# OptAgent Design Spec

An agent-based framework for process parameter optimization, built on deepagents (Python) + LangGraph, with a React SPA frontend and FastAPI backend.

## Overview

OptAgent is a framework that combines AI agent capabilities with structured process optimization workflows. It leverages deepagents' skill system to provide domain-specific guidance, LangGraph for stateful workflow execution, and a web UI for real-time visualization and interaction.

**Target users:** Process engineers and domain specialists who need guidance through parameter optimization workflows (DOE, factor analysis, etc.)

**Core principles:**
- **Skill-driven** — domain knowledge encoded as Markdown SKILL.md files, hot-pluggable
- **Agent-guided** — LLM agent leads the user through each optimization step
- **Visual-first** — real-time graph visualization, interactive charts, live streaming
- **Extensible** — add new skills without changing graph code

## Architecture

```
+--------------------------------------------+
|  Web UI (React SPA)                        |
|  Dashboard / WorkflowDetail / Analysis     |
+---------------------------+----------------+
                            | WebSocket
+---------------------------v----------------+
|  FastAPI Server                             |
|  Routes: sessions, skills, data            |
|  WebSocket: event encoding + push          |
|  SessionManager: tasks + cancel tokens     |
+---------------------------+----------------+
                            |
+---------------------------v----------------+
|  Agent Runtime (deepagents + LangGraph)    |
|  create_deep_agent() -> CompiledStateGraph |
|  Skills + Filesystem + SubAgent middleware |
+--------------------------------------------+
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|----------|
| Agent Runtime | deepagents (Python) | LangGraph-based, built-in SkillsMiddleware |
| Graph | @langchain/langgraph (Python) | Stateful DAG, streaming, checkpointing |
| API Server | FastAPI | Native WebSocket, async, Python |
| Frontend | React + Vite (SPA) | Fast dev, rich chart ecosystem |
| Real-time | WebSocket (JSON Lines) | Bidirectional, terminate support |
| Charts | ECharts | Heatmaps, Pareto, scatter for DOE |
| Skills Format | Markdown + YAML frontmatter | deepagents native, hot-pluggable |

## Project Structure

```
optagent/
+-- backend/
|   +-- src/optagent/
|   |   +-- main.py                     # FastAPI entry
|   |   +-- agent/
|   |   |   +-- factory.py              # create_agent() wrapper
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
|   |   |   +-- ws.py                   # WebSocket manager
|   |   |   +-- session_manager.py      # Session lifecycle
|   |   +-- models/
|   |   |   +-- session.py              # Pydantic models
|   |   +-- backends/
|   |       +-- filesystem.py
|   +-- skills/                         # Example skills
|   |   +-- define-objective/SKILL.md
|   |   +-- identify-params/SKILL.md
|   |   +-- design-doe/SKILL.md
|   |   +-- collect-data/SKILL.md
|   |   +-- analyze-results/SKILL.md
|   |   +-- generate-report/SKILL.md
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
5. Output updates state, transitions to next node

```
define_objective >> identify_params >> design_doe
     |                                        |
     v                                        v
generate_report << analyze_results << collect_data
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

## Termination Mechanism

Layered approach:

1. Primary: LangGraph interruption - User clicks terminate -> WS sends user:terminate -> Server sets asyncio.Event -> Graph checks at tool call boundaries -> LangGraph NodeInterrupt -> Checkpoint -> WS pushes graph:interrupted

2. Fallback: asyncio task cancellation - If no interruption within timeout -> task.cancel() -> Catch CancelledError -> Save partial checkpoint

After interruption: view saved state, resume from interrupted node, or start over.

## Frontend Pages

| Page | Route | Content |
|------|-------|---------|
| Dashboard | / | Active/past sessions, status, duration |
| WorkflowDetail | /sessions/:id | DAG, node status, chat, terminate |
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
