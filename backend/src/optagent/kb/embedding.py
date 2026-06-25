"""Zero-download character n-gram embedding for local vector search.

Uses hashlib-based feature hashing of character n-grams (2-4).
No model downloads, no PyTorch, no API calls. Works for any language.
256-dimensional unit vectors. Swap for a transformer model when network permits.
"""

import hashlib
from typing import List
from langchain_core.embeddings import Embeddings


class FastEmbeddings(Embeddings):
    """Character n-gram hashing embeddings — works everywhere, no downloads."""

    NGRAM_RANGE = (2, 5)   # 2-4 character n-grams
    DIM = 512              # output vector dimension (compatible with chromadb default)

    def __init__(self, model_name: str = "ngram"):
        pass

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.DIM
        # Extract character n-grams
        ngrams = set()
        for n in range(self.NGRAM_RANGE[0], self.NGRAM_RANGE[1]):
            for i in range(len(text) - n + 1):
                ngrams.add(text[i:i+n])
        # Hash each n-gram into a fixed-dimension vector
        for ng in ngrams:
            h = hashlib.md5(ng.encode('utf-8')).digest()
            idx = int.from_bytes(h[:2], 'big') % self.DIM
            vec[idx] += 1.0
        # L2 normalize
        norm = sum(v*v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec
