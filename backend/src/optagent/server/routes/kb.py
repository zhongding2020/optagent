import uuid
import asyncio
import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/api/kb", tags=["kb"])

_retriever = None
_ingestion = None
_ws_handler = None
_jobs: dict[str, dict] = {}

_stats = {
    "total_queries": 0,
    "total_hits": 0,
    "queries_with_results": 0,
    "queries_no_results": 0,
    "top_sources": {},
    "recent_queries": [],
}


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


@router.get("/files")
async def list_files():
    """List documents grouped by source file with chunk details."""
    if not _retriever:
        return []
    data = _retriever.list_documents()
    files: dict[str, dict] = {}
    for i, (id, meta) in enumerate(zip(data.get("ids", []), data.get("metadatas", []))):
        src = meta.get("source", "unknown") if meta else "unknown"
        content = (data.get("documents") or [])[i] if i < len(data.get("documents", [])) else ""
        if src not in files:
            files[src] = {"source": src, "chunk_count": 0, "chunks": []}
        files[src]["chunks"].append({"id": id, "metadata": meta, "content": content[:500]})
        files[src]["chunk_count"] += 1
    return sorted(files.values(), key=lambda f: -f["chunk_count"])


@router.get("/stats")
async def get_stats():
    """Return KB usage statistics."""
    if not _retriever:
        return {"error": "KB not initialized"}
    data = _retriever.list_documents()
    total_chunks = len(data.get("ids", []))
    sources = set()
    for meta in data.get("metadatas", []):
        if meta:
            sources.add(meta.get("source", "unknown"))
    hr = 0
    if _stats["total_queries"] > 0:
        hr = round(_stats["total_hits"] / _stats["total_queries"] * 100, 1)
    top = sorted(_stats["top_sources"].items(), key=lambda x: -x[1])[:10]
    return {
        "total_files": len(sources),
        "total_chunks": total_chunks,
        "total_queries": _stats["total_queries"],
        "total_hits": _stats["total_hits"],
        "queries_with_results": _stats["queries_with_results"],
        "queries_no_results": _stats["queries_no_results"],
        "hit_rate": hr,
        "embedding_model": "ngram-hash (512d)",
        "top_sources": [{"source": s, "hits": c} for s, c in top],
        "recent_queries": list(reversed(_stats["recent_queries"][-15:])),
    }


def track_search(query: str, results_count: int, source: str = ""):
    """Record a KB query. Called from REST and WebSocket chat."""
    _stats["total_queries"] += 1
    _stats["total_hits"] += results_count
    if results_count > 0:
        _stats["queries_with_results"] += 1
        if source:
            _stats["top_sources"][source] = _stats["top_sources"].get(source, 0) + 1
    else:
        _stats["queries_no_results"] += 1
    _stats["recent_queries"].append({
        "query": query[:200],
        "results": results_count,
        "time": datetime.now().isoformat(),
    })


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
    track_search(q, len(docs))
    return [
        {"content": d.page_content[:500], "metadata": d.metadata}
        for d in docs
    ]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    return _jobs.get(job_id, {"error": "job not found"})
