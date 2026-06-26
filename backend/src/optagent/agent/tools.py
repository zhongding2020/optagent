"""Agent tools: knowledge base retrieval, step management, and data analysis."""

import json
import logging
from typing import Any, Optional
from langchain_core.tools import tool
from ..kb.retriever import KBRetriever

logger = logging.getLogger("optagent.tools")

_kb_retriever: Optional[KBRetriever] = None
_uploaded_data_store: dict = {}


def init_tools(retriever: KBRetriever):
    global _kb_retriever
    _kb_retriever = retriever


def store_uploaded_data(key: str, data: dict):
    """Store parsed file data for later retrieval by the agent."""
    _uploaded_data_store[key] = data


# ── KB Tool ──────────────────────────────────────────────────────────────────

@tool
def query_knowledge_base(
    query: str,
    top_k: int = 5,
    filter: Optional[dict] = None,
) -> list[dict]:
    """Search the knowledge base for documents related to the query.

    Use this when you need domain-specific knowledge about process
    optimization, DOE methods, material specifications, or best practices.

    Args:
        query: The search query, be specific about what you need
        top_k: Number of documents to return (default: 5)
        filter: Optional metadata filter (e.g. {"source": "doe-handbook"})
    """
    if _kb_retriever is None:
        return []
    docs = _kb_retriever.search(query, top_k=top_k, filter=filter)
    return [
        {"content": d.page_content, "metadata": d.metadata}
        for d in docs
    ]


# ── Step Complete ────────────────────────────────────────────────────────────

@tool
def step_complete(result_summary: str) -> str:
    """Call this when the current step's goal has been reached.

    Provide a concise summary of what was accomplished in this step.
    The summary will be stored and used as context for the next step.

    Args:
        result_summary: One-sentence summary of what was achieved
    """
    return f"Step marked complete. Summary: {result_summary}"


# ── Uploaded Data Access ─────────────────────────────────────────────────────

@tool
def get_uploaded_data(data_key: str = "") -> str:
    """Get data the user uploaded to this session for analysis.

    Use this tool when the user has uploaded a file (CSV, Excel) and asks you
    to analyze it. Returns the data as JSON in {columns, rows} format, which
    can be passed directly to correlation_analysis, factor_importance, and
    other analysis tools.

    Args:
        data_key: Optional data key returned after upload. Leave empty for most
                  recent data (recommended for single-dataset sessions).
    """
    if not _uploaded_data_store:
        return json.dumps({"error": "No data uploaded yet. Tell the user to upload a file first."})
    
    key = data_key if data_key else list(_uploaded_data_store.keys())[-1]
    data = _uploaded_data_store.get(key)
    if not data:
        return json.dumps({"error": f"Data not found (key: {key})"})
    
    return json.dumps({"columns": data.get("columns", []), "rows": data.get("rows", [])})
