"""
NeuraDocs - Chat Interface & Citations Component
================================================
Renders message bubbles, streaming tokens, rich source citations cards,
audio read-aloud buttons, and export buttons.
"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List, Optional

from core.models import ChatMessage, RetrievedChunk


def render_message_bubble(msg: ChatMessage):
    avatar = "🧑‍💻" if msg.role == "user" else "🧠"
    with st.chat_message(msg.role, avatar=avatar):
        st.markdown(msg.content)

        # Render Source Citations Accordion
        if msg.sources:
            num_sources = len(msg.sources)
            unique_docs = len(set(s.get("source") for s in msg.sources))
            conf_str = f" · Confidence: {int(msg.confidence * 100)}%" if msg.confidence else ""
            latency_str = f" · {msg.latency_sec:.2f}s" if msg.latency_sec else ""

            with st.expander(f"📚 {num_sources} chunk(s) from {unique_docs} document(s){conf_str}{latency_str}"):
                for idx, s in enumerate(msg.sources, start=1):
                    page_label = f" · Page {s.get('page')}" if s.get("page") else ""
                    section_label = f" · Section: {s.get('section')}" if s.get("section") else ""
                    score_label = f" · Relevance: {s.get('score', 0):.2f}" if s.get("score") is not None else ""

                    st.markdown(
                        f"""
                        <div class="src-card">
                            <div class="src-header">
                                <span>📄 <b>{s.get('source')}</b>{page_label}{section_label}</span>
                                <span style="font-size:0.75rem; color:var(--accent-2);">{score_label}</span>
                            </div>
                            <div class="src-preview">
                                {s.get('preview', '')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


def render_voice_and_export_controls(
    on_export_markdown=None,
    on_export_text=None,
    on_export_json=None,
):
    col_exp1, col_exp2, col_exp3, col_audio = st.columns([1, 1, 1, 3])

    with col_exp1:
        if st.button("📥 Export .MD", key="btn_exp_md", help="Download conversation as Markdown"):
            if on_export_markdown:
                on_export_markdown()

    with col_exp2:
        if st.button("📄 Export .TXT", key="btn_exp_txt", help="Download conversation as Text"):
            if on_export_text:
                on_export_text()

    with col_exp3:
        if st.button("💾 Export .JSON", key="btn_exp_json", help="Download conversation as JSON"):
            if on_export_json:
                on_export_json()
