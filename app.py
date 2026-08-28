"""
NeuraDocs — AI Document Intelligence & Enterprise RAG Assistant
==============================================================
Production-grade RAG Chat Application featuring:
- Hybrid Search (BM25 Keyword + FAISS Dense Embeddings via RRF)
- Contextual Cross-Reranking
- Multi-Turn Conversational Query Contextualization
- Universal Multi-Format Loader (PDF, DOCX, PPTX, TXT, MD, CSV, XLSX, HTML)
- Real-Time Token Streaming with Groq
- SQLite + FAISS Persistent Vector Storage
- Multi-Chat Session Management
- Export to Markdown / TXT / JSON
- Voice-to-Text Input via Web Speech API

Developed by Nitin Yadav
"""

from __future__ import annotations

import time
import streamlit as st

# Core imports
from core.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
)
from core.database import Database
from core.models import ChatMessage, ChatSession, Chunk, DocumentRecord
from documents.chunker import StructureAwareChunker
from documents.loader import extract_document
from rag.embeddings import EmbeddingEngine
from rag.hybrid_search import HybridRetriever
from rag.llm import compute_confidence, stream_groq_response
from rag.query_rewriter import rewrite_query
from rag.reranker import Reranker
from rag.vector_store import VectorStore
from ui.chat_view import render_message_bubble, render_voice_and_export_controls
from ui.exporter import (
    export_session_to_json,
    export_session_to_markdown,
    export_session_to_text,
)
from ui.sidebar import render_sidebar
from ui.styles import get_css_styles

# ============================================================================
# Streamlit Page Config
# ============================================================================

st.set_page_config(
    page_title="NeuraDocs — AI Document Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# Persistent Database & RAG Initializers
# ============================================================================

@st.cache_resource
def get_database() -> Database:
    return Database()


@st.cache_resource
def get_vector_store() -> VectorStore:
    store = VectorStore()
    db = get_database()
    chunks = db.get_all_chunks()
    store.set_chunks(chunks)
    if chunks and not store.is_ready():
        store.rebuild_index(chunks)
    return store


@st.cache_resource
def get_hybrid_retriever() -> HybridRetriever:
    store = get_vector_store()
    return HybridRetriever(store)


@st.cache_resource
def get_reranker() -> Reranker:
    return Reranker()


db = get_database()
vector_store = get_vector_store()
hybrid_retriever = get_hybrid_retriever()
reranker = get_reranker()

# ============================================================================
# Session State Initialization
# ============================================================================

if "current_session_id" not in st.session_state:
    sessions = db.get_all_sessions()
    if sessions:
        st.session_state.current_session_id = sessions[0].session_id
    else:
        new_sess = ChatSession(title="Welcome Chat")
        db.save_chat_session(new_sess)
        st.session_state.current_session_id = new_sess.session_id

# Load active session
sessions_dict = {s.session_id: s for s in db.get_all_sessions()}
if st.session_state.current_session_id not in sessions_dict:
    new_sess = ChatSession(title="New Conversation")
    db.save_chat_session(new_sess)
    st.session_state.current_session_id = new_sess.session_id
    current_session = new_sess
else:
    current_session = sessions_dict[st.session_state.current_session_id]

# ============================================================================
# Sidebar Callbacks
# ============================================================================

def handle_new_chat():
    new_sess = ChatSession(title="New Conversation")
    db.save_chat_session(new_sess)
    st.session_state.current_session_id = new_sess.session_id
    st.rerun()


def handle_switch_chat(session_id: str):
    st.session_state.current_session_id = session_id
    st.rerun()


def handle_delete_chat(session_id: str):
    db.delete_session(session_id)
    remaining = db.get_all_sessions()
    if remaining:
        st.session_state.current_session_id = remaining[0].session_id
    else:
        new_sess = ChatSession(title="New Conversation")
        db.save_chat_session(new_sess)
        st.session_state.current_session_id = new_sess.session_id
    st.rerun()


def handle_rebuild_index():
    all_chunks = db.get_all_chunks()
    vector_store.rebuild_index(all_chunks)
    hybrid_retriever._sync_bm25()


# ============================================================================
# Render Sidebar & Fetch Controls
# ============================================================================

controls = render_sidebar(
    db=db,
    current_session=current_session,
    on_new_chat=handle_new_chat,
    on_switch_chat=handle_switch_chat,
    on_delete_chat=handle_delete_chat,
    on_rebuild_index=handle_rebuild_index,
    vector_store=vector_store,
    hybrid_retriever=hybrid_retriever,
)

# Apply Theme CSS
st.markdown(get_css_styles(theme=controls["theme"]), unsafe_allow_html=True)

# ============================================================================
# Main Header & Status Dashboard
# ============================================================================

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="neura-brand">🧠 NeuraDocs</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="neura-subhead">Enterprise AI Document Intelligence · Hybrid Search · Contextual Reranking · Citations</div>',
        unsafe_allow_html=True,
    )

with col_h2:
    all_docs = db.get_documents()
    num_docs = len(all_docs)
    num_chunks = len(vector_store.chunks)
    if num_docs > 0 or True: # Keep it consistent regardless of documents presence
        st.markdown(
            f'<div style="text-align:right; padding-top:10px;">'
            f'<span style="font-size:0.85rem; color:var(--text-lo); font-weight:500;">Developed by <b>Nitin Yadav</b></span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="text-align:right; padding-top:10px;">'
            f'<span style="font-size:0.85rem; color:var(--text-lo); font-weight:500;">Developed by <b>Nitin Yadav</b></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ============================================================================
# Suggested Prompt Chips (when no chat history)
# ============================================================================

suggested_prompt = None
if vector_store.is_ready() and not current_session.messages:
    st.markdown("##### 💡 Suggested Questions")
    chips = [
        "📋 Summarize the key findings in these documents",
        "🔑 Extract all numerical metrics, dates & figures",
        "⚖️ Compare the main methodologies or findings",
        "❓ What are the primary risks or recommendations mentioned?",
    ]
    cols = st.columns(len(chips))
    for col, chip_text in zip(cols, chips):
        with col:
            if st.button(chip_text, key=f"chip_{chip_text}", use_container_width=True, type="secondary"):
                suggested_prompt = chip_text.split(" ", 1)[1]

# ============================================================================
# Render Chat History
# ============================================================================

for msg in current_session.messages:
    render_message_bubble(msg)

# ============================================================================
# Chat Input & RAG Pipeline Execution
# ============================================================================

# ---------------------------------------------------------------------------
# Query Param Fallback Detection & Injector
# ---------------------------------------------------------------------------
voice_query = st.query_params.get("voice_input", "")
if voice_query:
    st.query_params.clear()
    st.session_state["voice_input_value"] = voice_query

user_input = st.chat_input(
    "Ask anything about your documents..."
    if vector_store.is_ready()
    else "Upload documents in the sidebar to start asking questions..."
)

# Render microphone next to the chat input using CSS injection
st.markdown(
    """
    <style>
    /* Position the voice recognition iframe absolute inside the chat input container */
    div[data-testid="stChatInput"] {
        position: relative;
        padding-right: 60px !important;
    }
    .voice-iframe-container {
        position: fixed;
        bottom: 46px;
        right: 154px;
        z-index: 999999;
        width: 44px;
        height: 44px;
    }
    /* Small screen adjust */
    @media (max-width: 768px) {
        .voice-iframe-container {
            bottom: 46px;
            right: 90px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display voice button container floating beside input
voice_container = st.empty()
with voice_container:
    st.markdown('<div class="voice-iframe-container">', unsafe_allow_html=True)
    render_voice_and_export_controls()
    st.markdown('</div>', unsafe_allow_html=True)

active_question = st.session_state.pop("voice_input_value", None) or suggested_prompt or user_input

if active_question:
    api_key = controls["api_key"]

    if not vector_store.is_ready():
        st.warning("⚠️ Please upload at least one document before asking questions.")
    else:
        # Add User Message to Session
        user_msg = ChatMessage(role="user", content=active_question)
        current_session.messages.append(user_msg)

        # If first question, update title
        if len(current_session.messages) <= 2:
            current_session.title = active_question[:30] + ("..." if len(active_question) > 30 else "")

        db.save_chat_session(current_session)
        render_message_bubble(user_msg)

        # ----------------- RAG Execution Pipeline -----------------
        with st.chat_message("assistant", avatar="🧠"):
            start_time = time.time()

            with st.spinner("Analyzing context and retrieving documents..."):
                # 1. Multi-Turn Query Rewriting
                search_query = active_question
                if controls["query_rewriting"] and len(current_session.messages) > 1:
                    search_query = rewrite_query(
                        api_key=api_key,
                        model=controls["model_id"],
                        latest_query=active_question,
                        history=current_session.messages[:-1],
                    )

                # 2. Hybrid Retrieval (BM25 + FAISS via RRF)
                candidate_k = max(controls["top_k"] * 3, 12)
                candidates = hybrid_retriever.search(
                    query=search_query,
                    top_k=candidate_k,
                    filter_sources=None,
                    hybrid_enabled=controls["hybrid_search"],
                )

                # 3. Contextual Reranking
                if controls["enable_reranking"] and candidates:
                    retrieved_chunks = reranker.rerank(
                        query=search_query,
                        candidates=candidates,
                        top_k=controls["top_k"],
                        enabled=True,
                    )
                else:
                    retrieved_chunks = candidates[: controls["top_k"]]

                confidence_score = compute_confidence(retrieved_chunks)

            # 4. Real-Time Streaming Generation
            placeholder = st.empty()
            full_response = ""

            try:
                token_stream = stream_groq_response(
                    api_key=api_key,
                    model=controls["model_id"],
                    question=active_question,
                    retrieved=retrieved_chunks,
                    history=current_session.messages[:-1],
                    temperature=controls["temperature"],
                )
                for token in token_stream:
                    full_response += token
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
            except Exception as e:
                full_response = (
                    f"❌ **Error communicating with Groq:** `{e}`\n\n"
                    "Please contact the administrator if this persists."
                )
                placeholder.markdown(full_response)

            latency = time.time() - start_time

            # Build source payload (stored internally, not shown as debug UI)
            source_payload = [
                {
                    "source": r.chunk.source,
                    "chunk_id": r.chunk.chunk_id,
                    "page": r.chunk.page_number,
                    "section": r.chunk.section,
                    "score": round(r.score, 3),
                    "preview": (r.chunk.text[:240] + "…") if len(r.chunk.text) > 240 else r.chunk.text,
                }
                for r in retrieved_chunks
            ]

            # Persist assistant message (with sources stored for exports)
            asst_msg = ChatMessage(
                role="assistant",
                content=full_response,
                sources=source_payload,
                confidence=confidence_score,
                latency_sec=latency,
            )
            current_session.messages.append(asst_msg)
            current_session.updated_at = time.time()
            db.save_chat_session(current_session)

# ============================================================================
# Export & Voice Controls (at bottom of chat)
# ============================================================================

# Removed bottom rendering to only use the floating input next to input bar



# ============================================================================
# Welcome / Empty State
# ============================================================================

if not current_session.messages and not vector_store.is_ready():
    st.markdown(
        """
        <div class="glass-panel" style="text-align:center; margin-top:2rem; padding: 2.5rem 2rem;">
            <div style="font-size:2.5rem; margin-bottom:0.8rem;">🚀</div>
            <h2 style="font-family:'Space Grotesk', sans-serif; margin-bottom:0.5rem;">Welcome to NeuraDocs 2.0</h2>
            <p style="color:var(--text-mid); max-width:600px; margin:0 auto 1.5rem auto; font-size:0.95rem;">
                State-of-the-art Document Intelligence engine with <b>Hybrid Keyword + Semantic Vector Search</b>,
                <b>Candidate Reranking</b>, and <b>Sub-Second Groq LLM Streaming</b>.
            </p>
            <p style="color:var(--text-lo); font-size:0.85rem; margin-bottom:1.5rem;">
                👈 Upload a document in the sidebar to begin. Processing starts automatically.
            </p>
            <div style="display:flex; justify-content:center; gap:20px; flex-wrap:wrap; margin-top:1rem;">
                <div class="stat-box" style="min-width:140px;">
                    <div class="stat-number">⚡ Fast</div>
                    <div class="stat-label">Groq LPU Inference</div>
                </div>
                <div class="stat-box" style="min-width:140px;">
                    <div class="stat-number">🎯 Hybrid</div>
                    <div class="stat-label">BM25 + FAISS RRF</div>
                </div>
                <div class="stat-box" style="min-width:140px;">
                    <div class="stat-number">🔒 Private</div>
                    <div class="stat-label">Local Embeddings</div>
                </div>
                <div class="stat-box" style="min-width:140px;">
                    <div class="stat-number">💾 Persistent</div>
                    <div class="stat-label">SQLite Storage</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
