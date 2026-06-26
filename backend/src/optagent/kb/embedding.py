"""Hybrid embeddings with ONNX support.

Default: character n-gram (zero-download, works everywhere).
Upgrade: install onnxruntime + transformers + torch for model-based embeddings:
    pip install onnxruntime transformers torch optimum
"""

import hashlib
import logging
from typing import List, Optional
from langchain_core.embeddings import Embeddings
from pathlib import Path

logger = logging.getLogger("optagent.embedding")


class FastEmbeddings(Embeddings):
    """Hybrid embeddings with automatic ONNX fallback.

    Default: character n-gram (TF-weighted, sublinear scaling).
    Upgrade: set model_name to any HuggingFace model ID to use ONNX.
    """

    NGRAM_RANGE = (2, 5)
    DIM = 512

    def __init__(self, model_name: str = "ngram"):
        self.model_name = model_name
        self._model = None
        self._tokenizer = None
        if model_name and model_name != "ngram":
            self._try_init(model_name)

    def _try_init(self, model_name: str):
        """Try to initialize a transformer/ONNX model."""
        try:
            from transformers import AutoTokenizer
            from optimum.onnxruntime import ORTModelForFeatureExtraction
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = ORTModelForFeatureExtraction.from_pretrained(
                model_name, export=True
            )
            logger.info(f"Loaded ONNX model '{model_name}'")
        except ImportError:
            logger.info(
                f"Install optimum[onnxruntime] for model '{model_name}', "
                "falling back to ngram"
            )
        except Exception as e:
            logger.warning(f"Failed to load model '{model_name}': {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._model:
            return self._onnx_embed(texts)
        return [self._ngram_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        if self._model:
            return self._onnx_embed([text])[0]
        return self._ngram_embed(text)

    def _onnx_embed(self, texts: List[str]) -> List[List[float]]:
        try:
            import torch
            inputs = self._tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
            outputs = self._model(**inputs)
            mask = inputs["attention_mask"].unsqueeze(-1)
            emb = (outputs.last_hidden_state * mask).sum(1) / mask.sum(1)
            return emb.tolist()
        except Exception as e:
            logger.error(f"ONNX embedding failed: {e}")
            return [self._ngram_embed(t) for t in texts]

    def _ngram_embed(self, text: str) -> List[float]:
        """Character n-gram hashing with sublinear TF scaling."""
        vec = [0.0] * self.DIM
        ngrams = {}
        for n in range(self.NGRAM_RANGE[0], self.NGRAM_RANGE[1]):
            for i in range(len(text) - n + 1):
                ng = text[i:i+n]
                ngrams[ng] = ngrams.get(ng, 0) + 1
        for ng, freq in ngrams.items():
            h = hashlib.md5(ng.encode('utf-8')).digest()
            idx = int.from_bytes(h[:2], 'big') % self.DIM
            vec[idx] += 1.0 + (freq - 1) * 0.5
        norm = sum(v*v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec
