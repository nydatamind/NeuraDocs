"""
NeuraDocs - Modern Sidebar Navigation & Settings Panel
======================================================
Coordinates multi-chat sessions, Groq API key, document uploading,
document filtering, and hyperparameters.
"""

from __future__ import annotations

import os
import streamlit as st
from typing import Callable, List, Optional

from core.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    GROQ_MODELS,
)
from core.database import Database
from core.models import ChatSession
from ui.doc_viewer import render_document_manager


def render_sidebar(
    db: Database,
    current_session: ChatSession,
    on_new_chat: Callable[[], None],
    on_switch_chat: Callable[[str], None],
    on_delete_chat: Callable[[str], None],
    on_rebuild_index: Callable[[], None],
):
    with st.sidebar:
        # Top Logo / Title
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                <div style="font-size:1.8rem;">🧠</div>
                <div>
                    <div style="font-family:'Space Grotesk', sans-serif; font-weight:700; font-size:1.3rem; line-height:1.1;">NeuraDocs</div>
                    <div style="font-size:0.75rem; color:var(--text-lo);">AI Document Intelligence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------- Multi-Chat Sessions -----------------
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            on_new_chat()

        all_sessions = db.get_all_sessions()
        if all_sessions:
            with st.expander("💬 Recent Chats", expanded=True):
                for s in all_sessions[:8]:
                    is_active = s.session_id == current_session.session_id
                    col_s1, col_s2 = st.columns([5, 1])
                    with col_s1:
                        btn_label = f"▸ {s.title[:22]}" if is_active else s.title[:22]
                        if st.button(
                            btn_label,
                            key=f"sess_{s.session_id}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            on_switch_chat(s.session_id)
                    with col_s2:
                        if st.button("✕", key=f"del_sess_{s.session_id}", help="Delete chat"):
                            on_delete_chat(s.session_id)
                            st.rerun()

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        # ----------------- Settings -----------------
        st.markdown("### ⚙️ Settings")

        # Models (excluding broken GPT-OSS)
        from core.config import get_groq_api_key
        api_key = get_groq_api_key()

        # Update models dict
        valid_models = {
            "Llama 3.3 70B Versatile (Recommended)": "llama-3.3-70b-versatile",
            "Llama 3.1 8B Instant (Ultra-Fast)": "llama-3.1-8b-instant",
            "DeepSeek R1 Distill Llama 70B": "deepseek-r1-distill-llama-70b",
            "Mixtral 8x7B (High Context)": "mixtral-8x7b-32768",
            "Gemma 2 9B IT (Balanced)": "gemma2-9b-it",
        }

        model_label = st.selectbox(
            "Model",
            list(valid_models.keys()),
            index=0,
            help="Choose reasoning, speed, or high context size.",
        )
        selected_model_id = valid_models[model_label]

        response_style = st.selectbox(
            "Response Style",
            ["Detailed", "Concise", "Professional", "Simple"],
            index=0,
        )

        st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
        st.markdown("### 🎙️ Voice settings")
        voice_answers = st.toggle("Voice answers (Read Aloud automatically)", value=False)

        st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)

        # Document Filter / Scope
        docs = db.get_documents()
        doc_names = [d.filename for d in docs]
        
        selected_filter_docs = []
        if doc_names:
            st.markdown("##### 🎯 Target Documents")
            filter_mode = st.radio(
                "Search Scope",
                ["All Documents", "Selected Only"],
                horizontal=True,
                label_visibility="collapsed",
            )
            if filter_mode == "Selected Only":
                selected_filter_docs = st.multiselect(
                    "Filter by document",
                    options=doc_names,
                    default=current_session.selected_docs if current_session.selected_docs else doc_names[:1],
                )

        # Clear button and doc manager
        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
        col_rst = st.columns(1)[0]
        with col_rst:
            reset_all_btn = st.button("🗑️ Clear All Index", use_container_width=True)

        if reset_all_btn:
            db.clear_all_documents()
            on_rebuild_index()
            st.toast("Cleared all stored documents!", icon="🗑️")
            st.rerun()

        with st.expander("📚 Stored Files", expanded=False):
            render_document_manager(db, on_delete_callback=lambda fname: on_rebuild_index())

        # RAG Advanced
        with st.expander("⚙️ Advanced RAG Settings", expanded=False):
            hybrid_search = st.toggle("Hybrid Search (BM25 + Dense)", value=True)
            enable_reranking = st.toggle("Context Reranker", value=True)
            query_rewriting = st.toggle("Conversational Query Rewriting", value=True)
            
            top_k = st.slider("Context chunks (Top-K)", 1, 10, DEFAULT_TOP_K)
            chunk_size = st.slider("Chunk size (chars)", 300, 2000, DEFAULT_CHUNK_SIZE, step=50)
            chunk_overlap = st.slider("Overlap (chars)", 0, 400, DEFAULT_CHUNK_OVERLAP, step=10)
            temperature = st.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, step=0.05)
            theme = st.selectbox("UI Theme", ["dark", "light"], index=0)

        st.markdown(
            """
            <div style="text-align:center; padding-top:20px; font-size:0.75rem; color:var(--text-lo);">
                NeuraDocs 2.0 · Developed by <b>Nitin Yadav</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return {
            "api_key": api_key,
            "model_id": selected_model_id,
            "selected_filter_docs": selected_filter_docs,
            "hybrid_search": hybrid_search,
            "enable_reranking": enable_reranking,
            "query_rewriting": query_rewriting,
            "top_k": top_k,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "temperature": temperature,
            "theme": theme,
            "response_style": response_style,
            "voice_answers": voice_answers,
        }

