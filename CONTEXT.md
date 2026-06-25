# OptAgent Domain Glossary

## Core Concepts

**Workflow**
A directed acyclic graph (DAG) of steps defined in YAML. Each workflow describes
a domain process (e.g., process parameter optimization). Workflows are loaded at
runtime by WorkflowBuilder and compiled into LangGraph StateGraphs.

**Node**
A single step in a workflow. Each node has a `skill_match` list that the agent
uses to discover which skill to load. Nodes use the residence loop pattern:
a while-loop that calls the agent and waits for user input until the step goal
is reached.

**Residence Loop**
A node's execution pattern. The node enters a conversation loop with the user
through the agent, alternating agent turns and user turns, until the step goal
is reached. Checkpoint happens only at node boundaries, not per turn.

**Skill**
A Markdown file (SKILL.md) with YAML frontmatter that encodes domain expertise.
Skills are hot-pluggable: adding/removing a SKILL.md in the skills directory is
reflected on the next agent invocation. Skills follow the progressive disclosure
pattern (name+description in prompt, full content loaded on demand via read_file).

**SkillRegistry**
Manages the hot-plug lifecycle of skills. Wraps deepagents' SkillsMiddleware
sources. Supports register, unregister, and reload operations.

**Agent**
A deepagents agent instance (single shared instance per session). Operates on
messages only. Created via create_deep_agent() and shared across all nodes
in a session.

**Knowledge Base (KB)**
A Chroma vector store indexed from local PDF and Markdown documents. Agent
queries KB via the `query_knowledge_base` tool. Document upload is async with
progress pushed via WebSocket.

**EventTransformer**
A utility class that converts LangGraph astream_events into optagent's
WebSocket event format (JSON Lines with `type` field).

**Session**
A single execution of a workflow. Persisted in SQLite with LangGraph checkpoint
backup. Supports resume after interruption.

## Domain Layer (Process Parameter Optimization)

**Process Parameter Optimization**
A specific workflow with 6 steps: define objective, identify parameters,
design DOE, collect data, analyze results, generate report.

**DOE**
Design of Experiments. A statistical method for planning experiments to
identify the relationship between process parameters and outputs.
