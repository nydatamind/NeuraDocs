"""
NeuraDocs - Database Layer (SQLite Persistence)
==============================================
Provides persistent storage for documents, chunks, chat sessions, and settings.
"""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Dict, List, Optional

from core.config import DB_PATH
from core.models import ChatMessage, ChatSession, Chunk, DocumentRecord


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self._shared_conn = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:")
            self._shared_conn.row_factory = sqlite3.Row
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Documents Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL UNIQUE,
                    file_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    page_count INTEGER NOT NULL,
                    uploaded_at REAL NOT NULL,
                    checksum TEXT,
                    status TEXT NOT NULL
                )
            """
            )

            # Chunks Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id INTEGER NOT NULL,
                    doc_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    text TEXT NOT NULL,
                    page_number INTEGER,
                    section TEXT,
                    metadata_json TEXT,
                    PRIMARY KEY (doc_id, chunk_id),
                    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
                )
            """
            )

            # Chat Sessions Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    selected_docs_json TEXT NOT NULL
                )
            """
            )

            # Chat Messages Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    sources_json TEXT,
                    confidence REAL,
                    latency_sec REAL,
                    tokens_used INTEGER,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
                )
            """
            )

            conn.commit()

    # ------------------ Document Operations ------------------

    def save_document(self, doc: DocumentRecord, chunks: List[Chunk]) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Upsert document
            cursor.execute(
                """
                INSERT INTO documents (doc_id, filename, file_type, file_size_bytes, chunk_count, page_count, uploaded_at, checksum, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    doc_id=excluded.doc_id,
                    file_type=excluded.file_type,
                    file_size_bytes=excluded.file_size_bytes,
                    chunk_count=excluded.chunk_count,
                    page_count=excluded.page_count,
                    uploaded_at=excluded.uploaded_at,
                    checksum=excluded.checksum,
                    status=excluded.status
            """,
                (
                    doc.doc_id,
                    doc.filename,
                    doc.file_type,
                    doc.file_size_bytes,
                    doc.chunk_count,
                    doc.page_count,
                    doc.uploaded_at,
                    doc.checksum,
                    doc.status,
                ),
            )

            # Remove old chunks for this doc if any
            cursor.execute("DELETE FROM chunks WHERE doc_id = ?", (doc.doc_id,))

            # Insert chunks
            chunk_records = [
                (
                    c.chunk_id,
                    doc.doc_id,
                    c.source,
                    c.text,
                    c.page_number,
                    c.section,
                    json.dumps(c.metadata),
                )
                for c in chunks
            ]
            cursor.executemany(
                """
                INSERT INTO chunks (chunk_id, doc_id, source, text, page_number, section, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                chunk_records,
            )
            conn.commit()

    def get_documents(self) -> List[DocumentRecord]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
            rows = cursor.fetchall()
            return [
                DocumentRecord(
                    doc_id=r["doc_id"],
                    filename=r["filename"],
                    file_type=r["file_type"],
                    file_size_bytes=r["file_size_bytes"],
                    chunk_count=r["chunk_count"],
                    page_count=r["page_count"],
                    uploaded_at=r["uploaded_at"],
                    checksum=r["checksum"],
                    status=r["status"],
                )
                for r in rows
            ]

    def get_document_by_filename(self, filename: str) -> Optional[DocumentRecord]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE filename = ?", (filename,))
            r = cursor.fetchone()
            if not r:
                return None
            return DocumentRecord(
                doc_id=r["doc_id"],
                filename=r["filename"],
                file_type=r["file_type"],
                file_size_bytes=r["file_size_bytes"],
                chunk_count=r["chunk_count"],
                page_count=r["page_count"],
                uploaded_at=r["uploaded_at"],
                checksum=r["checksum"],
                status=r["status"],
            )

    def delete_document(self, filename: str) -> Optional[str]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT doc_id FROM documents WHERE filename = ?", (filename,))
            row = cursor.fetchone()
            if not row:
                return None
            doc_id = row["doc_id"]
            cursor.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.commit()
            return doc_id

    def clear_all_documents(self) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks")
            cursor.execute("DELETE FROM documents")
            conn.commit()

    def get_all_chunks(self) -> List[Chunk]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks ORDER BY doc_id, chunk_id")
            rows = cursor.fetchall()
            chunks = []
            for r in rows:
                meta = json.loads(r["metadata_json"]) if r["metadata_json"] else {}
                chunks.append(
                    Chunk(
                        text=r["text"],
                        source=r["source"],
                        chunk_id=r["chunk_id"],
                        page_number=r["page_number"],
                        section=r["section"],
                        doc_id=r["doc_id"],
                        metadata=meta,
                    )
                )
            return chunks

    # ------------------ Chat Session Operations ------------------

    def save_chat_session(self, session: ChatSession) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_sessions (session_id, title, created_at, updated_at, selected_docs_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    title=excluded.title,
                    updated_at=excluded.updated_at,
                    selected_docs_json=excluded.selected_docs_json
            """,
                (
                    session.session_id,
                    session.title,
                    session.created_at,
                    session.updated_at,
                    json.dumps(session.selected_docs),
                ),
            )

            # Refresh messages
            cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session.session_id,))
            msg_records = [
                (
                    m.message_id,
                    session.session_id,
                    m.role,
                    m.content,
                    m.timestamp,
                    json.dumps(m.sources),
                    m.confidence,
                    m.latency_sec,
                    m.tokens_used,
                )
                for m in session.messages
            ]
            cursor.executemany(
                """
                INSERT INTO chat_messages (message_id, session_id, role, content, timestamp, sources_json, confidence, latency_sec, tokens_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                msg_records,
            )
            conn.commit()

    def get_all_sessions(self) -> List[ChatSession]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat_sessions ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            sessions = []
            for r in rows:
                session_id = r["session_id"]
                # Fetch messages
                cursor.execute(
                    "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
                    (session_id,),
                )
                msg_rows = cursor.fetchall()
                messages = [
                    ChatMessage(
                        message_id=mr["message_id"],
                        role=mr["role"],
                        content=mr["content"],
                        timestamp=mr["timestamp"],
                        sources=json.loads(mr["sources_json"]) if mr["sources_json"] else [],
                        confidence=mr["confidence"],
                        latency_sec=mr["latency_sec"],
                        tokens_used=mr["tokens_used"],
                    )
                    for mr in msg_rows
                ]
                selected_docs = (
                    json.loads(r["selected_docs_json"]) if r["selected_docs_json"] else []
                )
                sessions.append(
                    ChatSession(
                        session_id=session_id,
                        title=r["title"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        messages=messages,
                        selected_docs=selected_docs,
                    )
                )
            return sessions

    def delete_session(self, session_id: str) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
            conn.commit()
