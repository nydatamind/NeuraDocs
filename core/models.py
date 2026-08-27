"""
NeuraDocs - Core Data Models
============================
Defines data structures for chunks, documents, retrieval results,
chat messages, and sessions.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Chunk:
    text: str
    source: str
    chunk_id: int
    page_number: Optional[int] = None
    section: Optional[str] = None
    doc_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "section": self.section,
            "doc_id": self.doc_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Chunk:
        return cls(
            text=data.get("text", ""),
            source=data.get("source", ""),
            chunk_id=data.get("chunk_id", 0),
            page_number=data.get("page_number"),
            section=data.get("section"),
            doc_id=data.get("doc_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DocumentRecord:
    doc_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    page_count: int
    uploaded_at: float = field(default_factory=time.time)
    checksum: Optional[str] = None
    status: str = "indexed"  # "indexed", "processing", "failed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "chunk_count": self.chunk_count,
            "page_count": self.page_count,
            "uploaded_at": self.uploaded_at,
            "checksum": self.checksum,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DocumentRecord:
        return cls(
            doc_id=data.get("doc_id", str(uuid.uuid4())),
            filename=data.get("filename", ""),
            file_type=data.get("file_type", ""),
            file_size_bytes=data.get("file_size_bytes", 0),
            chunk_count=data.get("chunk_count", 0),
            page_count=data.get("page_count", 1),
            uploaded_at=data.get("uploaded_at", time.time()),
            checksum=data.get("checksum"),
            status=data.get("status", "indexed"),
        )


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float
    retrieval_method: str = "hybrid"  # "vector", "bm25", "hybrid", "reranked"
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None


@dataclass
class ChatMessage:
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: Optional[float] = None
    latency_sec: Optional[float] = None
    tokens_used: Optional[int] = None
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "sources": self.sources,
            "confidence": self.confidence,
            "latency_sec": self.latency_sec,
            "tokens_used": self.tokens_used,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatMessage:
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", time.time()),
            sources=data.get("sources", []),
            confidence=data.get("confidence"),
            latency_sec=data.get("latency_sec"),
            tokens_used=data.get("tokens_used"),
        )


@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    messages: List[ChatMessage] = field(default_factory=list)
    selected_docs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [m.to_dict() for m in self.messages],
            "selected_docs": self.selected_docs,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatSession:
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            title=data.get("title", "New Conversation"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            messages=[ChatMessage.from_dict(m) for m in data.get("messages", [])],
            selected_docs=data.get("selected_docs", []),
        )
