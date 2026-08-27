"""
NeuraDocs - Persistent FAISS Vector Store
=========================================
Persistent vector index that synchronizes with SQLite storage.
Supports addition, filtering, deletion, and cosine similarity search.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
import numpy as np

from core.config import VECTOR_INDEX_DIR
from core.models import Chunk, RetrievedChunk
from rag.embeddings import EmbeddingEngine


class VectorStore:
    def __init__(self, index_dir: Path = VECTOR_INDEX_DIR):
        self.index_dir = Path(index_dir)
        self.index_path = self.index_dir / "faiss.index"
        self.engine = EmbeddingEngine()
        self._index = None
        self.chunks: List[Chunk] = []
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        import faiss

        if self.index_path.exists():
            try:
                self._index = faiss.read_index(str(self.index_path))
            except Exception:
                self._index = None

    def _save_to_disk(self) -> None:
        import faiss

        if self._index is not None:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self._index, str(self.index_path))

    def set_chunks(self, chunks: List[Chunk]) -> None:
        """Set chunk metadata in memory (typically loaded from SQLite)."""
        self.chunks = chunks

    def is_ready(self) -> bool:
        return self._index is not None and len(self.chunks) > 0 and self._index.ntotal == len(self.chunks)

    def rebuild_index(self, chunks: List[Chunk]) -> None:
        """Rebuild entire FAISS index from a list of chunks."""
        import faiss

        self.chunks = chunks
        if not chunks:
            self._index = None
            if self.index_path.exists():
                self.index_path.unlink()
            return

        texts = [c.text for c in chunks]
        embeddings = self.engine.encode(texts, batch_size=32)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # Normalized cosine inner product
        index.add(embeddings)
        self._index = index
        self._save_to_disk()

    def add_chunks(self, new_chunks: List[Chunk]) -> None:
        """Incrementally add new chunks to existing index."""
        if not new_chunks:
            return
        import faiss

        texts = [c.text for c in new_chunks]
        embeddings = self.engine.encode(texts, batch_size=32)

        if self._index is None or self._index.ntotal != len(self.chunks):
            # Index needs a fresh build
            all_chunks = self.chunks + new_chunks
            self.rebuild_index(all_chunks)
            return

        self._index.add(embeddings)
        self.chunks.extend(new_chunks)
        self._save_to_disk()

    def search_dense(
        self,
        query: str,
        top_k: int = 15,
        filter_sources: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Dense semantic search using cosine similarity."""
        if not self.is_ready():
            return []

        q_emb = self.engine.encode([query]).astype("float32")
        total = len(self.chunks)
        fetch_k = min(top_k * 3 if filter_sources else top_k, total)

        scores, idxs = self._index.search(q_emb, fetch_k)

        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]

            # Apply document filtering if specified
            if filter_sources and chunk.source not in filter_sources:
                continue

            results.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=float(score),
                    retrieval_method="dense_vector",
                    dense_score=float(score),
                )
            )
            if len(results) >= top_k:
                break

        return results

    def clear(self) -> None:
        self.chunks = []
        self._index = None
        if self.index_path.exists():
            self.index_path.unlink()
