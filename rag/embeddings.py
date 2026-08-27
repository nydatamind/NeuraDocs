"""
NeuraDocs - Local Embedding Engine
==================================
Embeds text chunks using SentenceTransformers with local caching,
batching, normalization, and memory optimization.
"""

from __future__ import annotations

import logging
from typing import List, Optional
import numpy as np

from core.config import EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    _instance: Optional[EmbeddingEngine] = None
    _model = None

    def __new__(cls, model_name: str = EMBEDDING_MODEL_NAME):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model_name = model_name
        return cls._instance

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype="float32")

        model = self._load_model()
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=batch_size,
        ).astype("float32")
        return embeddings

    def encode_query(self, query: str) -> np.ndarray:
        return self.encode([query])[0]
