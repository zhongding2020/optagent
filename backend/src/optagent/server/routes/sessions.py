from fastapi import APIRouter, HTTPException
from ...models.session import SessionCreate

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

_manager = None


def init(manager):
    global _manager
    _manager = manager


@router.post("")
async def create_session(req: SessionCreate):
    if not _manager:
        raise HTTPException(503, "Not initialized")
    session = _manager.create_session(req)
    return session.model_dump()


@router.get("")
async def list_sessions():
    if not _manager:
        return []
    sessions = _manager.list_sessions()
    return [s.model_dump() for s in sessions]


@router.get("/{session_id}")
async def get_session(session_id: str):
    if not _manager:
        raise HTTPException(503, "Not initialized")
    session = _manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.model_dump()


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    if not _manager:
        raise HTTPException(503, "Not initialized")
    _manager.delete_session(session_id)
    return {"ok": True}


@router.post("/{session_id}/terminate")
async def terminate_session(session_id: str):
    if not _manager:
        raise HTTPException(503, "Not initialized")
    _manager.terminate(session_id)
    return {"ok": True}
