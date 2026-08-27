"""
NeuraDocs - Hybrid Retrieval (Dense Vector + BM25 Keyword + RRF)
================================================================
Combines deep semantic similarity (FAISS) with exact keyword matching (BM25)
via Reciprocal Rank Fusion (RRF) for optimal recall across names, numbers,
technical terms, and conceptual queries.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Set

from core.models import Chunk, RetrievedChunk
from rag.vector_store import VectorStore


class BM25Index:
    """Lightweight, zero-dependency BM25 index for sparse keyword search."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[Chunk] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.term_freqs_list: List[Counter] = []
        self.num_docs: int = 0

    def _tokenize(self, text: str) -> List[str]:
        # Split on non-alphanumeric, lowercase, filter short tokens
        tokens = re.findall(r"\w+", text.lower())
        return [t for t in tokens if len(t) > 1]

    def build(self, chunks: List[Chunk]) -> None:
        self.corpus = chunks
        self.num_docs = len(chunks)
        if self.num_docs == 0:
            return

        self.doc_lengths = []
        self.term_freqs_list = []
        self.doc_freqs = Counter()

        total_length = 0
        for chunk in chunks:
            tokens = self._tokenize(chunk.text)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_length += length

            tf = Counter(tokens)
            self.term_freqs_list.append(tf)

            for term in tf.keys():
                self.doc_freqs[term] += 1

        self.avg_doc_length = total_length / self.num_docs if self.num_docs > 0 else 1.0

    def search(
        self,
        query: str,
        top_k: int = 15,
        filter_sources: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        if self.num_docs == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores: List[tuple[int, float]] = []

        for idx, chunk in enumerate(self.corpus):
            if filter_sources and chunk.source not in filter_sources:
                continue

            doc_len = self.doc_lengths[idx]
            tf_map = self.term_freqs_list[idx]
            score = 0.0

            for token in query_tokens:
                if token not in tf_map:
                    continue
                tf = tf_map[token]
                df = self.doc_freqs.get(token, 0)
                # BM25 IDF formulation
                idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
                # Term score
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_length))
                score += idf * (numerator / (denominator + 1e-9))

            if score > 0:
                scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = scores[:top_k]

        return [
            RetrievedChunk(
                chunk=self.corpus[idx],
                score=score,
                retrieval_method="bm25_sparse",
                sparse_score=score,
            )
            for idx, score in top_matches
        ]


class HybridRetriever:
    """Orchestrates BM25 + FAISS Vector Search and merges rankings using RRF."""

    def __init__(self, vector_store: VectorStore, rrf_k: int = 60):
        self.vector_store = vector_store
        self.bm25 = BM25Index()
        self.rrf_k = rrf_k
        self._sync_bm25()

    def _sync_bm25(self) -> None:
        if self.vector_store.chunks:
            self.bm25.build(self.vector_store.chunks)

    def search(
        self,
        query: str,
        top_k: int = 15,
        filter_sources: Optional[List[str]] = None,
        hybrid_enabled: bool = True,
    ) -> List[RetrievedChunk]:
        # Always check BM25 sync
        if len(self.bm25.corpus) != len(self.vector_store.chunks):
            self._sync_bm25()

        # 1. Fetch dense candidates
        dense_results = self.vector_store.search_dense(
            query, top_k=top_k * 2, filter_sources=filter_sources
        )

        if not hybrid_enabled or len(self.vector_store.chunks) == 0:
            return dense_results[:top_k]

        # 2. Fetch sparse (BM25) candidates
        sparse_results = self.bm25.search(
            query, top_k=top_k * 2, filter_sources=filter_sources
        )

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF Score = 1 / (60 + rank_dense) + 1 / (60 + rank_sparse)
        chunk_map: Dict[int, Chunk] = {}
        rrf_scores: Dict[int, float] = Counter()
        dense_score_map: Dict[int, float] = {}
        sparse_score_map: Dict[int, float] = {}

        for rank, r in enumerate(dense_results, start=1):
            cid = r.chunk.chunk_id
            chunk_map[cid] = r.chunk
            rrf_scores[cid] += 1.0 / (self.rrf_k + rank)
            dense_score_map[cid] = r.score

        for rank, r in enumerate(sparse_results, start=1):
            cid = r.chunk.chunk_id
            chunk_map[cid] = r.chunk
            rrf_scores[cid] += 1.0 / (self.rrf_k + rank)
            sparse_score_map[cid] = r.score

        # Sort by RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda c: rrf_scores[c], reverse=True)

        final_results: List[RetrievedChunk] = []
        for cid in sorted_cids[:top_k]:
            chunk = chunk_map[cid]
            final_results.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=rrf_scores[cid],
                    retrieval_method="hybrid_rrf",
                    dense_score=dense_score_map.get(cid),
                    sparse_score=sparse_score_map.get(cid),
                )
            )

        return final_results
