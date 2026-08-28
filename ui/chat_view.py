"""
NeuraDocs - Chat Interface & Citations Component
================================================
Renders message bubbles, streaming tokens, action bars (Copy, TTS, Feedback),
and export controls.
"""

from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
import json

from core.models import ChatMessage


def render_message_bubble(msg: ChatMessage, msg_idx: int = 0, on_regenerate=None):
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

        # Action Bar for Assistant Messages (Only completed messages)
        if msg.role == "assistant" and msg.content:
            render_action_bar(msg, msg_idx, on_regenerate)


def render_action_bar(msg: ChatMessage, msg_idx: int, on_regenerate=None):
    # Escape quotes and formatting for Javascript safety
    clean_text = msg.content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    
    # Render HTML/JS action buttons (Copy, Read Aloud, Stop)
    action_html = f"""
    <div style="display: flex; gap: 8px; margin-top: 8px; font-family: monospace;">
        <button id="copy-btn-{msg_idx}" onclick="copyText()" style="
            background: rgba(0, 255, 136, 0.05);
            border: 1px solid rgba(0, 255, 136, 0.2);
            color: #80cbd6;
            border-radius: 6px;
            padding: 4px 10px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s ease;
        ">📋 Copy</button>
        
        <button id="speak-btn-{msg_idx}" onclick="speakText()" style="
            background: rgba(0, 229, 255, 0.05);
            border: 1px solid rgba(0, 229, 255, 0.2);
            color: #80cbd6;
            border-radius: 6px;
            padding: 4px 10px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s ease;
        ">🔊 Read aloud</button>

        <button id="stop-btn-{msg_idx}" onclick="stopText()" style="
            background: rgba(255, 23, 68, 0.05);
            border: 1px solid rgba(255, 23, 68, 0.2);
            color: #ff5f56;
            border-radius: 6px;
            padding: 4px 10px;
            cursor: pointer;
            font-size: 0.8rem;
            display: none;
            transition: all 0.2s ease;
        ">🛑 Stop</button>
    </div>

    <script>
    const textToProcess = `{clean_text}`;

    function copyText() {{
        navigator.clipboard.writeText(textToProcess).then(() => {{
            const btn = document.getElementById('copy-btn-{msg_idx}');
            btn.innerText = '✓ Copied';
            setTimeout(() => {{ btn.innerText = '📋 Copy'; }}, 2000);
        }});
    }}

    function speakText() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(textToProcess);
            utterance.onend = () => {{
                document.getElementById('stop-btn-{msg_idx}').style.display = 'none';
            }};
            document.getElementById('stop-btn-{msg_idx}').style.display = 'inline-block';
            window.speechSynthesis.speak(utterance);
        }} else {{
            alert("Text-to-speech is not supported by your browser.");
        }}
    }}

    function stopText() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            document.getElementById('stop-btn-{msg_idx}').style.display = 'none';
        }}
    }}
    </script>
    """
    components.html(action_html, height=45)

    # Regenerate & Feedback inside Streamlit to handle session state correctly
    col_reg, col_f1, col_f2, _ = st.columns([2, 1, 1, 8])
    with col_reg:
        if st.button("🔄 Regenerate", key=f"regen_btn_{msg_idx}", help="Regenerate this response"):
            if on_regenerate:
                on_regenerate(msg_idx)
    with col_f1:
        if st.button("👍", key=f"like_{msg_idx}"):
            st.toast("Feedback registered! Thank you.", icon="👍")
    with col_f2:
        if st.button("👎", key=f"dislike_{msg_idx}"):
            st.toast("Feedback registered! Thank you.", icon="👎")


def render_voice_and_export_controls(
    on_export_markdown=None,
    on_export_text=None,
    on_export_json=None,
):
    col_exp1, col_exp2, col_exp3, _ = st.columns([1, 1, 1, 3])

    with col_exp1:
        if on_export_markdown:
            on_export_markdown()

    with col_exp2:
        if on_export_text:
            on_export_text()

    with col_exp3:
        if on_export_json:
            on_export_json()
