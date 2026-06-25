from fastapi import APIRouter

router = APIRouter(prefix="/api/sessions/{session_id}/data", tags=["data"])

_store = None


def init(store):
    global _store
    _store = store


@router.get("")
async def get_analysis_data(session_id: str):
    if not _store:
        return {}
    session = _store.get(session_id)
    if not session:
        return {"error": "Session not found"}
    return {"session_id": session_id, "data": {}}
