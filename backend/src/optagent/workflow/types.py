from typing import Literal, Optional
from pydantic import BaseModel


OnFailure = Literal["terminate", "skip"]


class ErrorStrategy(BaseModel):
    max_retries: int = 3
    on_failure: OnFailure = "terminate"


class NodeDef(BaseModel):
    id: str
    name: str
    skill_match: list[str] = []
    error_strategy: ErrorStrategy = ErrorStrategy()


class EdgeDef(BaseModel):
    from_node: str
    to: str


class WorkflowDefinition(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0"
    nodes: list[NodeDef]
    edges: list[EdgeDef]
