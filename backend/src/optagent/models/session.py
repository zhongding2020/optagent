from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class NodeStatus(BaseModel):
    status: str = "pending"  # pending | running | completed | error | skipped | interrupted
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    retry_count: int = 0
    error: Optional[str] = None


class SessionMetadata(BaseModel):
    id: str
    workflow_name: str
    workflow_version: str = "1.0"
    status: str = "pending"  # pending | running | completed | error | interrupted
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    checkpoint_id: Optional[str] = None
    current_node: Optional[str] = None
    node_statuses: dict[str, NodeStatus] = Field(default_factory=dict)
    node_results: dict[str, Any] = Field(default_factory=dict)


class SessionCreate(BaseModel):
    workflow_name: str = "process-optimization"
