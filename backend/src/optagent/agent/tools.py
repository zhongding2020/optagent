 from typing import Any, Optional
 from langchain_core.tools import tool
 from ..kb.retriever import KBRetriever
 
 _kb_retriever: Optional[KBRetriever] = None
 
 
 def init_tools(retriever: KBRetriever):
     global _kb_retriever
     _kb_retriever = retriever
 
 
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
 
 
 @tool
 def step_complete(result_summary: str) -> str:
     """Call this when the current step's goal has been reached.
 
     Provide a concise summary of what was accomplished in this step.
     The summary will be stored and used as context for the next step.
 
     Args:
         result_summary: One-sentence summary of what was achieved
     """
     return f"Step marked complete. Summary: {result_summary}"
