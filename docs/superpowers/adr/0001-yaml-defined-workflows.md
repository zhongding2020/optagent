# ADR 0001: Workflow graphs defined in YAML, not Python code

**Status:** Accepted

**Context:**

The initial design specified a hardcoded LangGraph StateGraph with 6 fixed nodes for process parameter optimization. However, different process types (welding, injection molding, heat treatment) may need different workflows with different numbers of steps, ordering, and error tolerance.

If graphs are hardcoded, supporting a new workflow type requires:
1. Writing new Python node functions
2. Modifying the graph builder
3. Testing and redeploying the server

This makes the framework less extensible than its stated principle.

**Decision:**

Workflows are defined declaratively in YAML files. WorkflowBuilder reads the YAML at runtime and dynamically generates a LangGraph StateGraph. The YAML format includes:
- Node list with `id`, `name`, `skill_match` keywords, and `error_strategy`
- Edge list defining the DAG topology
- Metadata (name, description, version)

Each node in the generated graph delegates to a deepagents agent, which uses SkillsMiddleware to discover and load the matching skill at runtime.

**Consequences:**
- Positive: Adding a new workflow is a YAML file + SKILL.md files, no Python code changes
- Positive: Non-developers can define workflow templates
- Positive: Workflows can be validated, versioned, and shared independently
- Negative: Dynamic graph construction adds startup complexity
- Negative: Cannot use Python-level type checking on the graph topology
- Negative: YAML DSL limits expressiveness compared to hand-written graph code

**Trade-offs considered:**
- Python code approach was simpler but killed extensibility
- Full DSL with custom node types was overkill for v1
- YAML strikes a balance: declarative, easy to validate with Pydantic, easy to extend later
