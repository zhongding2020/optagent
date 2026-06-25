from fastapi import APIRouter, HTTPException
from ...workflow.loader import WorkflowLoader

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

_loader: WorkflowLoader | None = None


def init(loader: WorkflowLoader):
    global _loader
    _loader = loader


@router.get("")
async def list_workflows():
    if not _loader:
        return []
    names = _loader.list()
    return [{"name": name} for name in names]


@router.get("/{name}")
async def get_workflow(name: str):
    if not _loader:
        raise HTTPException(503, "Not initialized")
    defn = _loader.load(name)
    return defn.model_dump()
