# ADR 0002: Node execution via residence loop, state via message bridge

**Status:** Accepted

**Context:**

Each node in the workflow graph requires potentially multiple turns of agent-user
conversation before the step goal is reached. The graph needs to "stay" in the node
during this interaction. Additionally, the deepagents `create_deep_agent()` operates
on its own `DeepAgentState` (primarily `messages`), while the outer workflow has a
richer `WorkflowState` with domain fields, node statuses, and KB context.

Two problems to solve:
1. How does a node pause for user input without excessive checkpoint cost?
2. How does the outer WorkflowState communicate with the inner deepagents state?

**Decision:**

### Residence Loop (Problem 1)

Each node runs a while-loop that alternates between agent calls and user input:

```
node enter → while goal_not_reached:
               agent.astream_events({messages})
                 → WS push events (tokens, tool calls, agent messages)
               if agent asked a question:
                 ws.wait_for_message() → append to messages
node exit → checkpoint
```

Checkpoint happens only at node exit. Within the node, messages accumulate in
state["messages"] but no LangGraph checkpoint is written. This avoids the O(N)
checkpoint cost of per-turn interruption.

User termination via WS interrupts the loop mid-turn and saves a partial checkpoint.

### Message Bridge (Problem 2)

Nodes bridge between the two state types explicitly:

```python
async def run_node(state: WorkflowState, agent, ws):
    node_id = state["current_node"]
    while not _goal_reached(state, node_id):
        # 1. Call agent with only the messages it needs
        result = await agent.ainvoke({"messages": state["messages"]})

        # 2. Extract new messages from agent output
        state["messages"] = result["messages"]

        # 3. Push agent output to WebSocket (tokens streamed separately)
        agent_msg = result["messages"][-1]
        await ws.send({"type": "agent:message", "content": agent_msg.content})

        # 4. If agent needs user input, wait via WS
        if _needs_user_input(agent_msg):
            user_msg = await ws.wait_for_message("user:message")
            state["messages"].append(user_msg)
            # OR user terminated
            if user_msg["type"] == "user:terminate":
                return _interrupted_state(state)

    # 5. Extract domain-specific output from the conversation
    state["node_results"][node_id] = _extract_result(state["messages"])
    state["node_statuses"][node_id] = "completed"
    return state
```

The agent is created once (`create_deep_agent()`) and shared across all nodes in
a session via closure. SkillsMiddleware caches skill metadata after the first call,
so subsequent calls within the residence loop don't re-scan the filesystem.

**Consequences:**
- Positive: Simple, no nested graph complexity
- Positive: Checkpoint cost is O(1) per node, not O(turns)
- Positive: Agent sees a clean message list, no foreign state fields
- Positive: Users can freely converse with the agent mid-node
- Negative: Node function must manually bridge state
- Negative: "Needs user input" heuristic is heuristic (agent message ends with "?" + context)
- Negative: If agent crashes mid-loop, unsaved conversation turns may be lost

**Alternatives considered:**
- Per-turn interrupt: clean state but checkpoint cost O(N)
- Self-loop node: state model gets complex with "am I entering or looping" flags
