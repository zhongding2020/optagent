import json
from fastapi import APIRouter, HTTPException
from ...models.session import SessionCreate
from langchain_core.messages import messages_from_dict

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

_manager = None
_store = None


def init(manager, store=None):
    global _manager
    global _store
    _manager = manager
    _store = store


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


@router.patch("/{session_id}")
async def update_session(session_id: str, body: dict):
    if not _store:
        raise HTTPException(503, "Not initialized")
    session = _store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if "name" in body:
        session.name = str(body["name"])
    if "workflow_name" in body:
        session.workflow_name = str(body["workflow_name"])
    _store.update(session)
    return session.model_dump()


@router.get("/{session_id}/messages")
async def get_session_messages(session_id: str):
    if not _store:
        raise HTTPException(503, "Not initialized")
    session = _store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    msg_json = _store.load_session_messages(session_id)
    if not msg_json:
        return {"messages": [], "total": 0}
    try:
        msgs = messages_from_dict(json.loads(msg_json))
        return {
            "messages": [
                {"role": type(m).__name__.replace("HumanMessage", "user").replace("AIMessage", "assistant").replace("SystemMessage", "system").lower(),
                 "content": m.content}
                for m in msgs if hasattr(m, "content") and m.content
            ],
            "total": len(msgs),
        }
    except Exception:
        return {"messages": [], "total": 0}


@router.get("/{session_id}/state")
async def get_session_state(session_id: str):
    if not _manager:
        raise HTTPException(503, "Not initialized")
    session = _manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    # Load messages from store for accurate count
    msg_count = 0
    if _store:
        msg_json = _store.load_session_messages(session_id)
        if msg_json:
            try:
                msg_count = len(messages_from_dict(json.loads(msg_json)))
            except Exception:
                msg_count = 0
    return {
        "session_id": session.id,
        "workflow_name": session.workflow_name,
        "status": session.status,
        "current_node": session.current_node,
        "node_statuses": {
            k: v.model_dump() for k, v in session.node_statuses.items()
        },
        "node_results": session.node_results,
        "message_count": msg_count,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.post("/{session_id}/terminate")
async def terminate_session(session_id: str):
    if not _manager:
        raise HTTPException(503, "Not initialized")
    _manager.terminate(session_id)
    return {"ok": True}
