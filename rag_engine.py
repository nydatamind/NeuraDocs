"""
NeuraDocs - Core RAG Engine Orchestrator
=======================================
Maintains backward compatibility with earlier versions while wiring
together the modular loaders, chunkers, hybrid search (BM25 + FAISS),
reranker, and streaming LLM components.

Developed by Nitin Yadav
"""

from __future__ import annotations

from typing import Any, Dict, Generator, List, Optional

from core.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    SYSTEM_PROMPT,
)
from core.models import Chunk, DocumentRecord, RetrievedChunk
from documents.chunker import StructureAwareChunker
from documents.loader import ExtractedDocument, extract_document
from rag.embeddings import EmbeddingEngine
from rag.hybrid_search import HybridRetriever
from rag.llm import (
    build_context_block,
    call_groq_blocking,
    compute_confidence,
    stream_groq_response,
)
from rag.query_rewriter import rewrite_query
from rag.reranker import Reranker
from rag.vector_store import VectorStore


# ================= Legacy Backward Compatibility Layer =================

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Legacy helper function returning raw text."""
    doc = extract_document(file_bytes, filename)
    return doc.full_text


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    start_id: int = 0,
) -> List[Chunk]:
    """Legacy chunking helper."""
    doc = extract_document(text.encode("utf-8"), source)
    chunker = StructureAwareChunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk_document(doc, start_chunk_id=start_id)


class VectorIndex:
    """Main VectorIndex maintaining compatibility with VectorStore and HybridRetriever."""

    def __init__(self):
        self.store = VectorStore()
        self.retriever = HybridRetriever(self.store)
        self.reranker = Reranker()

    @property
    def chunks(self) -> List[Chunk]:
        return self.store.chunks

    @chunks.setter
    def chunks(self, val: List[Chunk]):
        self.store.set_chunks(val)

    def is_ready(self) -> bool:
        return self.store.is_ready()

    def build(self, chunks: List[Chunk]) -> None:
        self.store.rebuild_index(chunks)
        self.retriever._sync_bm25()

    def add(self, chunks: List[Chunk]) -> None:
        self.store.add_chunks(chunks)
        self.retriever._sync_bm25()

    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        filter_sources: Optional[List[str]] = None,
        hybrid: bool = True,
        rerank: bool = True,
    ) -> List[RetrievedChunk]:
        """High-precision hybrid retrieval with candidate over-fetch & reranking."""
        candidate_k = max(top_k * 3, 12)
        candidates = self.retriever.search(
            query=query,
            top_k=candidate_k,
            filter_sources=filter_sources,
            hybrid_enabled=hybrid,
        )

        if rerank and len(candidates) > 0:
            return self.reranker.rerank(query=query, candidates=candidates, top_k=top_k)

        return candidates[:top_k]

    def clear(self) -> None:
        self.store.clear()


def call_groq(
    api_key: str,
    model: str,
    question: str,
    retrieved: List[RetrievedChunk],
    history: Optional[List[dict]] = None,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    """Legacy blocking Groq call."""
    from core.models import ChatMessage

    chat_history = []
    if history:
        for h in history:
            chat_history.append(
                ChatMessage(
                    role=h.get("role", "user"),
                    content=h.get("content", ""),
                )
            )
    return call_groq_blocking(
        api_key=api_key,
        model=model,
        question=question,
        retrieved=retrieved,
        history=chat_history,
        temperature=temperature,
    )
