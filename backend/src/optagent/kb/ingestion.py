from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .retriever import KBRetriever

ProgressCallback = Callable[[str, float, Optional[int]], None]


class KBIngestion:
    """Ingests documents into the knowledge base with chunking and progress reporting."""

    def __init__(
        self,
        retriever: KBRetriever,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.retriever = retriever
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def _get_loader(self, file_path: str):
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext == ".pdf":
            return PyPDFLoader(file_path)
        elif ext == ".md":
            return TextLoader(file_path)
        elif ext == ".txt":
            return TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    async def ingest_file(
        self,
        file_path: str,
        progress: Optional[ProgressCallback] = None,
    ) -> int:
        if progress:
            progress("loading", 0.0, None)

        loader = self._get_loader(file_path)
        docs = loader.load()

        if progress:
            progress("splitting", 0.3, len(docs))

        chunks = self.splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["source"] = file_path

        if progress:
            progress("embedding", 0.6, len(chunks))

        self.retriever.add_documents(chunks)

        if progress:
            progress("done", 1.0, len(chunks))

        return len(chunks)
