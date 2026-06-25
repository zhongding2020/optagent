from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


class KBRetriever:
    """Vector-store backed retriever for the optagent knowledge base."""

    def __init__(
        self,
        persist_dir: str = "./data/chroma",
        embedding_model: str = "text-embedding-3-small",
    ):
        self.persist_dir = persist_dir
        Path(persist_dir).parent.mkdir(parents=True, exist_ok=True)
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.vector_store = Chroma(
            collection_name="optagent_kb",
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        return self.vector_store.similarity_search(
            query, k=top_k, filter=filter
        )

    def add_documents(self, documents: List[Document]):
        self.vector_store.add_documents(documents)
        self.vector_store.persist()

    def delete_document(self, doc_id: str):
        self.vector_store.delete(ids=[doc_id])

    def list_documents(self) -> Dict[str, Any]:
        return self.vector_store.get()

    def count(self) -> int:
        return self.vector_store._collection.count()
