from typing import Any, Callable, Dict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from typing_extensions import TypedDict

from .types import WorkflowDefinition


class WorkflowState(TypedDict):
    """Shared state passed through the workflow graph."""

    workflow_name: str
    messages: list[Any]
    current_node: str
    completed_nodes: list[str]
    node_statuses: Dict[str, str]
    node_results: Dict[str, Any]
    node_durations: Dict[str, float]
    errors: list[Dict[str, Any]]
    kb_context: list[Dict[str, Any]]


NodeHandler = Callable[[WorkflowState], Any]


class WorkflowBuilder:
    """Builds a compiled langgraph StateGraph from a WorkflowDefinition."""

    def __init__(self, definition: WorkflowDefinition):
        self.defn = definition

    def build(self, node_handlers: Dict[str, NodeHandler]) -> StateGraph:
        graph = StateGraph(WorkflowState)

        for node in self.defn.nodes:
            handler = node_handlers.get(node.id)
            if not handler:
                raise ValueError(f"No handler registered for node: {node.id}")
            graph.add_node(node.id, handler)

        for edge in self.defn.edges:
            graph.add_edge(edge.from_node, edge.to)

        first_node = self.defn.nodes[0].id if self.defn.nodes else None
        if first_node:
            graph.set_entry_point(first_node)

        return graph.compile(checkpointer=MemorySaver())
