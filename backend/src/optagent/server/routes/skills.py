from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/skills", tags=["skills"])

_registry = None


def init(registry):
    global _registry
    _registry = registry


class RegisterRequest(BaseModel):
    path: str


@router.get("")
async def list_skills():
    if not _registry:
        return []
    return [s.model_dump() for s in _registry.list()]


@router.post("/register")
async def register_skill(req: RegisterRequest):
    if not _registry:
        raise HTTPException(503, "Not initialized")
    skills = _registry.register(req.path)
    return [s.model_dump() for s in skills]


@router.delete("/{name}")
async def unregister_skill(name: str):
    if not _registry:
        raise HTTPException(503, "Not initialized")
    ok = _registry.unregister(name)
    if not ok:
        raise HTTPException(404, f"Skill '{name}' not found")
    return {"ok": True}


@router.post("/reload")
async def reload_skills():
    if not _registry:
        raise HTTPException(503, "Not initialized")
    skills = _registry.reload()
    return [s.model_dump() for s in skills]
