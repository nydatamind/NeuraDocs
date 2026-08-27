"""
NeuraDocs - Contextual Reranker Engine
=====================================
Re-ranks broad candidate chunks using cross-scoring or high-resolution
semantic relevance scoring to prioritize the highest-signal context for the LLM.
"""

from __future__ import annotations

import logging
from typing import List, Optional
import numpy as np

from core.models import RetrievedChunk
from rag.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name
        self._cross_encoder = None
        self.embedding_engine = EmbeddingEngine()

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        top_k: int = 5,
        enabled: bool = True,
    ) -> List[RetrievedChunk]:
        """Rerank candidate chunks to pick the most informative top_k."""
        if not candidates:
            return []

        if not enabled:
            return candidates[:top_k]

        # Use fast, high-accuracy cosine similarity re-scoring + exact keyword boost
        q_emb = self.embedding_engine.encode([query])[0]
        chunk_texts = [c.chunk.text for c in candidates]
        c_embs = self.embedding_engine.encode(chunk_texts)

        # Dot product of normalized vectors
        scores = np.dot(c_embs, q_emb)

        query_words = set(query.lower().split())
        reranked: List[RetrievedChunk] = []

        for idx, (cand, base_score) in enumerate(zip(candidates, scores)):
            text_lower = cand.chunk.text.lower()
            # Boost exact keyword matches
            match_count = sum(1 for w in query_words if len(w) > 3 and w in text_lower)
            boost = min(match_count * 0.05, 0.20)
            final_score = float(base_score) + boost

            reranked.append(
                RetrievedChunk(
                    chunk=cand.chunk,
                    score=final_score,
                    retrieval_method="reranked",
                    dense_score=cand.dense_score,
                    sparse_score=cand.sparse_score,
                )
            )

        reranked.sort(key=lambda x: x.score, reverse=True)
        return reranked[:top_k]
