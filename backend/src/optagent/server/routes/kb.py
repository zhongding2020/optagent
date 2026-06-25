import uuid
import asyncio
import os
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/api/kb", tags=["kb"])

_retriever = None
_ingestion = None
_ws_handler = None
_jobs: dict[str, dict] = {}


def init(retriever, ingestion, ws_handler=None):
    global _retriever, _ingestion, _ws_handler
    _retriever = retriever
    _ingestion = ingestion
    _ws_handler = ws_handler


@router.get("/documents")
async def list_documents():
    if not _retriever:
        return []
    data = _retriever.list_documents()
    return [
        {"id": id, "metadata": meta}
        for id, meta in zip(data.get("ids", []), data.get("metadatas", []))
    ]


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not _ingestion:
        raise HTTPException(503, "KB not initialized")
    job_id = str(uuid.uuid4())
    temp_path = f"/tmp/optagent_{job_id}_{file.filename}"
    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    async def _send_progress(phase: str, progress: float, doc_count: int | None = None):
        event = {
            "type": "kb:index_progress",
            "job_id": job_id,
            "phase": phase,
            "progress": progress,
            "documents": doc_count,
        }
        _jobs[job_id] = event
        if _ws_handler:
            await _ws_handler(event)

    asyncio.create_task(_run_ingestion(job_id, temp_path, _send_progress))
    return {"job_id": job_id, "filename": file.filename}


async def _run_ingestion(job_id: str, path: str, progress_fn):
    try:
        await _ingestion.ingest_file(path, progress=progress_fn)
    except Exception as e:
        _jobs[job_id] = {
            "type": "kb:index_progress", "job_id": job_id,
            "phase": "error", "error": str(e),
        }
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    if not _retriever:
        raise HTTPException(503, "KB not initialized")
    _retriever.delete_document(doc_id)
    return {"ok": True}


@router.post("/reindex")
async def reindex():
    return {"ok": True, "message": "Not yet implemented"}


@router.get("/search")
async def search(q: str, top_k: int = 5):
    if not _retriever:
        return []
    try:
        docs = _retriever.search(q, top_k=top_k)
    except Exception:
        docs = []
    return [
        {"content": d.page_content[:500], "metadata": d.metadata}
        for d in docs
    ]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    return _jobs.get(job_id, {"error": "job not found"})
