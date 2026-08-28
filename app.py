"""
NeuraDocs — AI Document Intelligence & Enterprise RAG Assistant
==============================================================
Production-grade RAG Chat Application featuring:
- Premium AI Hacker Terminal Theme & CSS
- Shared Server-Side Groq API Key Setup
- Bottom Chat Input with File Popover (+) & Web Speech Voice recognition
- Automated File Upload status and Ingestion
- Real-Time Token Streaming with Groq & Live Terminal loading states
- SQLite + FAISS Persistent Vector Storage
- Interactive Action Bar (Copy, Read Aloud, Stop, Regenerate, Feedback)
- Excel / CSV Pandas Calculations and Matplotlib visualizations fallback
- Glitch Hacker success animation

Developed by Nitin Yadav
"""

from __future__ import annotations

import hashlib
import time
import uuid
import streamlit as st
import io
import os
import json
import base64
import streamlit.components.v1 as components

# Core imports
from core.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    GROQ_MODELS,
    get_groq_api_key,
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

if "processed_files" not in st.session_state:
    st.session_state.processed_files = {}
if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}
if "active_query" not in st.session_state:
    st.session_state.active_query = None

# Check for voice text in query params
if "voice_text" in st.query_params:
    voice_input = st.query_params["voice_text"]
    st.query_params.clear()
    st.session_state.active_query = voice_input
    st.rerun()

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


def handle_regenerate(msg_idx: int):
    if msg_idx > 0 and msg_idx < len(current_session.messages):
        user_msg = current_session.messages[msg_idx - 1]
        current_session.messages = current_session.messages[:msg_idx]
        st.session_state.active_query = user_msg.content
        db.save_chat_session(current_session)
        st.rerun()

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
)

# Apply Theme CSS
st.markdown(get_css_styles(theme=controls["theme"]), unsafe_allow_html=True)

# ============================================================================
# Main Futuristic Header
# ============================================================================

st.markdown(
    """
    <div class="neura-brand-container">
        <h1 class="neura-brand">NEURADOCS</h1>
        <div class="neura-subhead">AI Document + Data Intelligence Terminal</div>
        <div class="dev-by">Developed By</div>
        <div class="dev-name">NITIN YADAV</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================================
# Render Chat History
# ============================================================================

for idx, msg in enumerate(current_session.messages):
    render_message_bubble(msg, msg_idx=idx, on_regenerate=handle_regenerate)

# ============================================================================
# Attachment popover, Voice & Chat Input Section
# ============================================================================

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
col_plus, col_voice, col_files = st.columns([2, 2, 8])

with col_plus:
    with st.popover("＋ Attach", use_container_width=True):
        st.markdown("**Attach Files (Documents, Tables, Images)**")
        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "doc", "docx", "txt", "md", "csv", "xlsx", "xls", "ppt", "pptx", "png", "jpg", "jpeg", "webp", "rtf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="plus_uploader"
        )

with col_voice:
    mic_html = """
    <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
        <button id="mic-btn" onclick="toggleListening()" style="
            background: #080c14;
            color: #00ff88;
            border: 1px solid #00ff88;
            border-radius: 8px;
            width: 100%;
            height: 38px;
            font-family: monospace;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 0 8px rgba(0, 255, 136, 0.2);
            transition: all 0.3s ease;
        ">🎤 SPEAK</button>
    </div>
    <script>
        let recognition;
        let isListening = false;
        
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onstart = () => {
                isListening = true;
                const btn = document.getElementById('mic-btn');
                btn.style.background = '#ff1744';
                btn.style.color = '#ffffff';
                btn.style.border = '1px solid #ff1744';
                btn.innerText = '🔴 LISTENING...';
            };
            
            recognition.onend = () => {
                isListening = false;
                const btn = document.getElementById('mic-btn');
                btn.style.background = '#080c14';
                btn.style.color = '#00ff88';
                btn.style.border = '1px solid #00ff88';
                btn.innerText = '🎤 SPEAK';
            };
            
            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                const url = new URL(window.parent.location.href);
                url.searchParams.set("voice_text", text);
                window.parent.location.href = url.toString();
            };
            
            recognition.onerror = (event) => {
                console.error("Speech error", event.error);
            };
        } else {
            const btn = document.getElementById('mic-btn');
            btn.onclick = () => alert("Voice input is not supported by this browser.");
            btn.innerText = "🎤 Unsupported";
        }
        
        function toggleListening() {
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }
    </script>
    """
    components.html(mic_html, height=45)

# Handle file uploads and status display
if uploaded_files:
    new_files = []
    unsupported_files = []
    
    for f in uploaded_files:
        ext = f.name.lower().rsplit(".", 1)[-1] if "." in f.name else ""
        if ext in ("ppt", "pptx", "jpg", "jpeg", "png", "webp", "doc", "rtf"):
            unsupported_files.append(f.name)
        else:
            raw_bytes = f.getvalue()
            checksum = hashlib.md5(raw_bytes).hexdigest()
            if f.name not in st.session_state.processed_files or st.session_state.processed_files[f.name] != checksum:
                new_files.append((f, checksum, raw_bytes))
                
    if unsupported_files:
        for fname in unsupported_files:
            st.error(f"⚠️ {fname}: This file format is not currently supported.")
            
    if new_files:
        status_placeholder = st.empty()
        with status_placeholder.container():
            st.markdown('<div class="pill-badge pill-info"><span class="pill-dot"></span>Uploading...</div>', unsafe_allow_html=True)
            time.sleep(0.3)
            st.markdown('<div class="pill-badge pill-info"><span class="pill-dot"></span>Processing...</div>', unsafe_allow_html=True)
            time.sleep(0.3)
            st.markdown('<div class="pill-badge pill-info"><span class="pill-dot"></span>Indexing...</div>', unsafe_allow_html=True)
            
            chunker = StructureAwareChunker(
                chunk_size=controls["chunk_size"],
                overlap=controls["chunk_overlap"],
            )
            total_files = len(new_files)
            all_new_chunks: list[Chunk] = []
            next_chunk_id = len(vector_store.chunks)

            for i, (file_obj, checksum, raw_bytes) in enumerate(new_files):
                try:
                    extracted = extract_document(raw_bytes, file_obj.name)
                    doc_chunks = chunker.chunk_document(extracted, start_chunk_id=next_chunk_id)
                    next_chunk_id += len(doc_chunks)

                    doc_record = DocumentRecord(
                        doc_id=str(uuid.uuid4()),
                        filename=file_obj.name,
                        file_type=extracted.file_type,
                        file_size_bytes=len(raw_bytes),
                        chunk_count=len(doc_chunks),
                        page_count=len(extracted.pages),
                        checksum=checksum,
                        status="indexed",
                    )

                    db.save_document(doc_record, doc_chunks)
                    all_new_chunks.extend(doc_chunks)
                    
                    import pandas as pd
                    if file_obj.name.endswith(".csv"):
                        st.session_state.dataframes[file_obj.name] = pd.read_csv(io.BytesIO(raw_bytes))
                    elif file_obj.name.endswith((".xlsx", ".xls")):
                        st.session_state.dataframes[file_obj.name] = pd.read_excel(io.BytesIO(raw_bytes))

                    st.session_state.processed_files[file_obj.name] = checksum

                except Exception as e:
                    st.error(f"Error parsing {file_obj.name}: {e}")

            if all_new_chunks:
                all_chunks = db.get_all_chunks()
                vector_store.rebuild_index(all_chunks)
                hybrid_retriever._sync_bm25()
                st.markdown('<div class="pill-badge pill-success"><span class="pill-dot"></span>Ready ✓</div>', unsafe_allow_html=True)
                time.sleep(0.5)
            status_placeholder.empty()
            st.rerun()

with col_files:
    if uploaded_files:
        rendered_badges = ""
        for f in uploaded_files:
            icon = "📊" if f.name.endswith((".csv", ".xlsx", ".xls")) else "📄"
            rendered_badges += f'<span class="attachment-badge">{icon} {f.name}</span>'
        st.markdown(f'<div style="display: flex; flex-wrap: wrap;">{rendered_badges}</div>', unsafe_allow_html=True)

# ----------------- Chat Input -----------------
user_input = st.chat_input("Ask anything about your documents...")

active_question = st.session_state.active_query or user_input
if active_question:
    st.session_state.active_query = None # clear active query

if active_question:
    api_key = controls["api_key"]
    if not api_key:
        st.error("AI service is temporarily unavailable. Please try again later.")
    elif not vector_store.is_ready() and not st.session_state.dataframes:
        st.warning("⚠️ Please upload at least one document or spreadsheet to begin.")
    else:
        # Add User Message
        user_msg = ChatMessage(role="user", content=active_question)
        current_session.messages.append(user_msg)
        
        if len(current_session.messages) <= 2:
            current_session.title = active_question[:30] + ("..." if len(active_question) > 30 else "")
        
        db.save_chat_session(current_session)
        render_message_bubble(user_msg)

        # ----------------- Data Routing Logic -----------------
        is_data_question = False
        result_text = ""
        chart_markdown = ""
        
        if st.session_state.dataframes:
            data_keywords = ["average", "mean", "sum", "total", "sales", "chart", "plot", "max", "min", "highest", "lowest", "revenue", "correlation", "missing values", "column", "count", "rows"]
            if any(kw in active_question.lower() for kw in data_keywords):
                is_data_question = True
                
        if is_data_question:
            # Code Interpreter Execution
            with st.spinner("Analyzing tables and calculations..."):
                code_prompt = f"""You are a precise data analysis assistant.
You are given a dictionary of pandas DataFrames called `dfs` containing data from uploaded Excel/CSV files.
The keys of `dfs` are the filenames: {list(st.session_state.dataframes.keys())}.

Write a python script to answer the user's question: "{active_question}"
Your code must:
1. Perform the necessary calculations using pandas.
2. Store the final answer as a string in the variable `result_text`.
3. If the user asks for a chart, plot, or visualization, create a matplotlib figure using `import matplotlib.pyplot as plt; fig, ax = plt.subplots()` and store the figure object in the variable `fig`. Do not call `plt.show()`.
4. Do not make up any data. Only use the data from `dfs`.

Respond with ONLY the executable python code block. No explanations, no markdown formatting other than the python code block.
"""
                try:
                    from groq import Groq
                    client = Groq(api_key=api_key)
                    completion = client.chat.completions.create(
                        model=controls["model_id"],
                        messages=[{"role": "user", "content": code_prompt}],
                        temperature=0.1,
                    )
                    code = completion.choices[0].message.content
                    if "```python" in code:
                        code = code.split("```python")[1].split("```")[0]
                    elif "```" in code:
                        code = code.split("```")[1].split("```")[0]
                        
                    local_vars = {"dfs": st.session_state.dataframes}
                    exec(code, {}, local_vars)
                    result_text = local_vars.get("result_text", "Data analysis completed.")
                    
                    fig = local_vars.get("fig", None)
                    if fig:
                        import matplotlib.pyplot as plt
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", bbox_inches="tight")
                        buf.seek(0)
                        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                        chart_markdown = f"\n\n![Data Visualization](data:image/png;base64,{img_base64})"
                        plt.close(fig)
                except Exception as e:
                    # Fallback to standard RAG if code interpreter fails
                    is_data_question = False

        # ----------------- Standard RAG Execution Pipeline -----------------
        if not is_data_question:
            with st.chat_message("assistant", avatar="🧠"):
                start_time = time.time()
                
                # Terminal Status Indicators
                status_box = st.empty()
                status_text = ""

                def log_terminal(msg):
                    nonlocal status_text
                    status_text += f"> {msg}<br>"
                    status_box.markdown(
                        f"""
                        <div style="font-family:'Share Tech Mono', monospace; color:#00ff88; background:#020508; padding:10px; border-radius:6px; border:1px solid #00ff88; margin-bottom:12px;">
                            {status_text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                log_terminal("CONNECTING TO KNOWLEDGE CORE...")
                time.sleep(0.2)
                
                # 1. Multi-Turn Query Rewriting
                search_query = active_question
                if controls["query_rewriting"] and len(current_session.messages) > 1:
                    log_terminal("REWRITING CONVERSATIONAL QUERY...")
                    search_query = rewrite_query(
                        api_key=api_key,
                        model=controls["model_id"],
                        latest_query=active_question,
                        history=current_session.messages[:-1],
                    )

                log_terminal("SEARCHING DOCUMENTS...")
                # 2. Hybrid Retrieval (BM25 + FAISS via RRF)
                filter_docs = controls["selected_filter_docs"] or None
                candidate_k = max(controls["top_k"] * 3, 12)
                candidates = hybrid_retriever.search(
                    query=search_query,
                    top_k=candidate_k,
                    filter_sources=filter_docs,
                    hybrid_enabled=controls["hybrid_search"],
                )

                log_terminal("RANKING CONTEXT...")
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
                
                log_terminal("GENERATING RESPONSE...")
                time.sleep(0.1)
                status_box.empty()

                # 4. Real-Time Streaming Generation
                placeholder = st.empty()
                full_response = ""

                try:
                    # Append response style instruction inside prompt modifier
                    styled_question = active_question
                    if controls.get("response_style"):
                        styled_question += f"\n\n[Style Instruction: Respond in a {controls['response_style']} manner]"

                    token_stream = stream_groq_response(
                        api_key=api_key,
                        model=controls["model_id"],
                        question=styled_question,
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
                        "Something went wrong while generating the response. Please try again."
                    )
                    placeholder.markdown(full_response)

                latency = time.time() - start_time

                # Format source citations
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

                # Persist assistant message
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
                
                # Hacker Terminal Success Animation
                hacker_html = """
                <div class="terminal-anim">
                    <div class="terminal-header"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
                    <div class="terminal-body">
                        <p class="term-line">> CONNECTING TO KNOWLEDGE CORE...</p>
                        <p class="term-line">> ACCESS GRANTED.</p>
                        <p class="term-line">> SYSTEM ONLINE_</p>
                    </div>
                </div>
                <style>
                .terminal-anim {
                    background: #020508;
                    border: 1px solid #00ff88;
                    box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
                    border-radius: 6px;
                    padding: 10px;
                    font-family: monospace;
                    color: #00ff88;
                    margin: 10px 0;
                }
                .terminal-header {
                    display: flex;
                    gap: 6px;
                    margin-bottom: 5px;
                    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
                    padding-bottom: 3px;
                }
                .dot { width: 8px; height: 8px; border-radius: 50%; }
                .red { background: #ff5f56; }
                .yellow { background: #ffbd2e; }
                .green { background: #27c93f; }
                .term-line { margin: 2px 0; font-size: 0.85rem; }
                </style>
                """
                components.html(hacker_html, height=100)
                
                # Auto Voice playback
                if controls.get("voice_answers") and full_response:
                    voice_js = f"""
                    <script>
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        const u = new SpeechSynthesisUtterance({json.dumps(full_response)});
                        window.speechSynthesis.speak(u);
                    }}
                    </script>
                    """
                    components.html(voice_js, height=0)
                
                st.rerun()
        else:
            # Render CSV/Excel code execution result
            with st.chat_message("assistant", avatar="🧠"):
                complete_res = result_text + chart_markdown
                st.markdown(complete_res)
                
                # Persist assistant message
                asst_msg = ChatMessage(
                    role="assistant",
                    content=complete_res,
                    sources=[],
                    confidence=1.0,
                    latency_sec=0.5,
                )
                current_session.messages.append(asst_msg)
                current_session.updated_at = time.time()
                db.save_chat_session(current_session)
                
                # Auto Voice playback
                if controls.get("voice_answers") and result_text:
                    voice_js = f"""
                    <script>
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        const u = new SpeechSynthesisUtterance({json.dumps(result_text)});
                        window.speechSynthesis.speak(u);
                    }}
                    </script>
                    """
                    components.html(voice_js, height=0)
                
                st.rerun()

# ============================================================================
# Export & Utility Controls (at bottom of chat)
# ============================================================================

if current_session.messages:
    st.write("")
    render_voice_and_export_controls(
        on_export_markdown=lambda: st.download_button(
            "Download Markdown File",
            data=export_session_to_markdown(current_session),
            file_name=f"neuradocs_chat_{current_session.title[:15]}.md",
            mime="text/markdown",
            key="dl_md_btn",
        ),
        on_export_text=lambda: st.download_button(
            "Download Text File",
            data=export_session_to_text(current_session),
            file_name=f"neuradocs_chat_{current_session.title[:15]}.txt",
            mime="text/plain",
            key="dl_txt_btn",
        ),
        on_export_json=lambda: st.download_button(
            "Download JSON File",
            data=export_session_to_json(current_session),
            file_name=f"neuradocs_chat_{current_session.title[:15]}.json",
            mime="application/json",
            key="dl_json_btn",
        ),
    )

# ============================================================================
# ChatGPT-style Empty / Welcome State
# ============================================================================

if not current_session.messages:
    st.markdown(
        """
        <div class="glass-panel" style="text-align:center; margin-top:2rem; padding: 2.5rem 2rem;">
            <div style="font-size:2.8rem; margin-bottom:0.8rem;">🚀</div>
            <h2 style="font-family:'Space Grotesk', sans-serif; margin-bottom:0.5rem; letter-spacing:1px; color:#00ff88;">NEURADOCS TERMINAL</h2>
            <p style="color:var(--text-mid); max-width:600px; margin:0 auto 1.5rem auto; font-size:0.95rem;">
                State-of-the-art Document + Data Intelligence engine with hybrid search, candidate reranking, text-to-speech feedback, and deterministic CSV/Excel calculations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("##### 💡 Suggestions")
    
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    
    with col_s1:
        if st.button("💡 Summarize my documents", use_container_width=True, key="s_sum"):
            st.session_state.active_query = "Summarize the key findings in my documents"
            st.rerun()
            
    with col_s2:
        if st.button("🔎 Find important info", use_container_width=True, key="s_find"):
            st.session_state.active_query = "What are the primary findings and recommendations?"
            st.rerun()
            
    with col_s3:
        if st.button("📊 Analyze my Excel", use_container_width=True, key="s_anal"):
            st.session_state.active_query = "List columns and rows or average metric in my Excel data"
            st.rerun()
            
    with col_s4:
        if st.button("📝 Create a report", use_container_width=True, key="s_rep"):
            st.session_state.active_query = "Create a summary report of the context details"
            st.rerun()
            
    with col_s5:
        if st.button("❓ Ask questions", use_container_width=True, key="s_ask"):
            st.session_state.active_query = "What are the primary details specified in the files?"
            st.rerun()
