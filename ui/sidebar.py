"""
NeuraDocs - Modern Sidebar Navigation & Settings Panel
======================================================
Coordinates multi-chat sessions, document uploading (auto-processed),
and RAG hyperparameters. API key is loaded from Streamlit Secrets / env
and never exposed in the UI.
"""

from __future__ import annotations

import hashlib
import os
import uuid
import time
import streamlit as st
from typing import Callable, List, Optional

from core.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
)
from core.database import Database
from core.models import ChatSession, Chunk, DocumentRecord
from documents.chunker import StructureAwareChunker
from documents.loader import extract_document

# ---------------------------------------------------------------------------
# AI-Themed Processing Animation (inline HTML/CSS/SVG)
# ---------------------------------------------------------------------------

_AI_ANIMATION_HTML = """
<div id="neura-anim-wrapper" style="
    padding: 12px 0 8px 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
">
  <canvas id="neura-canvas" width="260" height="110"
    style="border-radius:12px; background:rgba(10,12,24,0.85);"></canvas>
  <div id="neura-anim-label" style="
    font-size:0.78rem;
    color:#35d5ff;
    font-family:'Inter',sans-serif;
    letter-spacing:0.5px;
    font-weight:500;
    text-align:center;
  ">⚡ Indexing document…</div>
</div>

<script>
(function(){
  var canvas = document.getElementById('neura-canvas');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var W = canvas.width, H = canvas.height;

  // Neural nodes
  var nodes = [];
  var nodeCount = 18;
  for (var i = 0; i < nodeCount; i++) {
    nodes.push({
      x: 20 + Math.random() * (W - 40),
      y: 12 + Math.random() * (H - 24),
      r: 2.5 + Math.random() * 3,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      phase: Math.random() * Math.PI * 2
    });
  }

  // Data particles
  var particles = [];
  for (var p = 0; p < 28; p++) {
    particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      speed: 0.6 + Math.random() * 1.2,
      size: 1 + Math.random() * 1.5,
      alpha: 0.3 + Math.random() * 0.7,
      color: Math.random() > 0.5 ? '#7c5cff' : '#35d5ff'
    });
  }

  var frame = 0;

  function animate() {
    ctx.clearRect(0, 0, W, H);

    // Background gradient
    var bg = ctx.createLinearGradient(0, 0, W, H);
    bg.addColorStop(0, 'rgba(10,10,28,0.0)');
    bg.addColorStop(1, 'rgba(18,12,38,0.0)');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // Draw connections
    for (var i = 0; i < nodes.length; i++) {
      for (var j = i + 1; j < nodes.length; j++) {
        var dx = nodes[i].x - nodes[j].x;
        var dy = nodes[i].y - nodes[j].y;
        var dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 72) {
          var alpha = (1 - dist / 72) * 0.35;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = 'rgba(124,92,255,' + alpha + ')';
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }

    // Draw animated data particles (moving along x)
    for (var p = 0; p < particles.length; p++) {
      var pt = particles[p];
      pt.x += pt.speed;
      if (pt.x > W + 4) pt.x = -4;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, pt.size, 0, Math.PI * 2);
      ctx.fillStyle = pt.color.replace(')', ',' + pt.alpha + ')').replace('rgb', 'rgba').replace('##', '#');
      // simpler approach:
      ctx.globalAlpha = pt.alpha * (0.6 + 0.4 * Math.sin(frame * 0.04 + p));
      ctx.fillStyle = pt.color;
      ctx.fill();
      ctx.globalAlpha = 1.0;
    }

    // Draw nodes
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 8 || n.x > W - 8) n.vx *= -1;
      if (n.y < 8 || n.y > H - 8) n.vy *= -1;

      var pulse = 0.7 + 0.3 * Math.sin(frame * 0.05 + n.phase);

      // Glow
      var grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 3.5);
      grad.addColorStop(0, 'rgba(124,92,255,' + (0.5 * pulse) + ')');
      grad.addColorStop(1, 'rgba(53,213,255,0)');
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r * 3.5, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // Core dot
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r * pulse, 0, Math.PI * 2);
      ctx.fillStyle = i % 3 === 0 ? '#35d5ff' : '#7c5cff';
      ctx.fill();
    }

    // Pulsing scan line
    var scanY = ((frame * 1.5) % (H + 10)) - 5;
    var scanGrad = ctx.createLinearGradient(0, scanY - 8, 0, scanY + 8);
    scanGrad.addColorStop(0, 'rgba(53,213,255,0)');
    scanGrad.addColorStop(0.5, 'rgba(53,213,255,0.18)');
    scanGrad.addColorStop(1, 'rgba(53,213,255,0)');
    ctx.fillStyle = scanGrad;
    ctx.fillRect(0, scanY - 8, W, 16);

    frame++;
    requestAnimationFrame(animate);
  }
  animate();
})();
</script>
"""

# ---------------------------------------------------------------------------
# Internal API-key loader (never shown to user)
# ---------------------------------------------------------------------------

def _load_api_key() -> str:
    """Load Groq API key from Streamlit Secrets or environment variable."""
    key = ""
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    if not key:
        key = os.getenv("GROQ_API_KEY", "")
    return key


# ---------------------------------------------------------------------------
# Auto-processing helper
# ---------------------------------------------------------------------------

def _file_set_hash(files) -> str:
    """Return a deterministic hash representing the current set of uploaded files."""
    if not files:
        return ""
    return hashlib.md5(
        b"".join(hashlib.md5(f.getvalue()).digest() for f in sorted(files, key=lambda x: x.name))
    ).hexdigest()


def _process_uploaded_files(files, db, vector_store, hybrid_retriever, chunk_size, chunk_overlap):
    """Process and index all uploaded files; returns count of new chunks added."""
    chunker = StructureAwareChunker(chunk_size=chunk_size, overlap=chunk_overlap)
    total_files = len(files)
    progress_bar = st.sidebar.progress(0, text="Analyzing documents…")

    # Show AI animation
    anim_placeholder = st.sidebar.empty()
    anim_placeholder.markdown(_AI_ANIMATION_HTML, unsafe_allow_html=True)

    all_new_chunks: list[Chunk] = []
    next_chunk_id = len(vector_store.chunks)

    for i, file_obj in enumerate(files):
        progress_bar.progress(i / total_files, text=f"Reading {file_obj.name}…")
        raw_bytes = file_obj.getvalue()
        checksum = hashlib.md5(raw_bytes).hexdigest()

        # Skip if already indexed (same checksum)
        existing = db.get_documents()
        if any(getattr(d, "checksum", None) == checksum for d in existing):
            progress_bar.progress((i + 1) / total_files, text=f"Already indexed: {file_obj.name}")
            continue

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

        except Exception as e:
            st.sidebar.error(f"❌ Error parsing **{file_obj.name}**: {e}")

        progress_bar.progress((i + 1) / total_files, text=f"Indexed {file_obj.name} ✓")

    # Rebuild vector index if new chunks were added
    if all_new_chunks:
        progress_bar.progress(1.0, text="Rebuilding search index…")
        all_chunks = db.get_all_chunks()
        vector_store.rebuild_index(all_chunks)
        hybrid_retriever._sync_bm25()

    # Clear animation & progress
    time.sleep(0.4)
    anim_placeholder.empty()
    progress_bar.empty()

    return len(all_new_chunks)


# ---------------------------------------------------------------------------
# Main sidebar renderer
# ---------------------------------------------------------------------------

def render_sidebar(
    db: Database,
    current_session: ChatSession,
    on_new_chat: Callable[[], None],
    on_switch_chat: Callable[[str], None],
    on_delete_chat: Callable[[str], None],
    on_rebuild_index: Callable[[], None],
    vector_store=None,
    hybrid_retriever=None,
):
    with st.sidebar:
        # ── Logo / Branding ──────────────────────────────────────────────
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

        # ── API Key validation (silent — never shown to user) ────────────
        api_key = _load_api_key()
        if not api_key:
            st.error(
                "⚠️ **Admin Configuration Error**\n\n"
                "The `GROQ_API_KEY` secret is not configured.\n\n"
                "**For local use:** set it in `.env` or `.streamlit/secrets.toml`.\n\n"
                "**For Streamlit Cloud:** add it in App Settings → Secrets."
            )
            st.stop()

        # ── Multi-Chat Sessions ──────────────────────────────────────────
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

        # ── Document Upload (auto-processes on change) ───────────────────
        st.markdown("##### 📁 Document Ingestion")

        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "docx", "pptx", "txt", "md", "csv", "xlsx", "html"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            help="PDF, DOCX, PPTX, TXT, MD, CSV, XLSX, HTML — automatically indexed on upload.",
        )

        # Auto-process when file set changes
        current_hash = _file_set_hash(uploaded_files)
        last_hash = st.session_state.get("_last_uploaded_hash", "")

        if current_hash and current_hash != last_hash and vector_store and hybrid_retriever:
            new_count = _process_uploaded_files(
                uploaded_files, db, vector_store, hybrid_retriever,
                chunk_size=st.session_state.get("_chunk_size", DEFAULT_CHUNK_SIZE),
                chunk_overlap=st.session_state.get("_chunk_overlap", DEFAULT_CHUNK_OVERLAP),
            )
            st.session_state["_last_uploaded_hash"] = current_hash
            if new_count > 0:
                st.sidebar.success(f"✅ Indexed {new_count} new chunk(s)!")
                st.rerun()

        # Removed stored documents list section


        # ── Advanced RAG Settings ────────────────────────────────────────
        with st.expander("⚙️ Advanced RAG Settings", expanded=False):
            hybrid_search = st.toggle("Hybrid Search (BM25 + Dense)", value=True)
            enable_reranking = st.toggle("Context Reranker", value=True)
            query_rewriting = st.toggle("Conversational Query Rewriting", value=True)

            top_k = st.slider("Context chunks (Top-K)", 1, 10, DEFAULT_TOP_K)
            chunk_size = st.slider(
                "Chunk size (chars)", 300, 2000, DEFAULT_CHUNK_SIZE, step=50,
                key="_chunk_size",
            )
            chunk_overlap = st.slider(
                "Overlap (chars)", 0, 400, DEFAULT_CHUNK_OVERLAP, step=10,
                key="_chunk_overlap",
            )
            temperature = st.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, step=0.05)
            theme = st.selectbox("UI Theme", ["dark", "light"], index=0)

        # ── Developer Branding ───────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center; padding-top:20px; font-size:0.75rem; color:var(--text-lo);">
                Developed by <b>Nitin Yadav</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return {
            "api_key": api_key,
            "model_id": DEFAULT_MODEL,
            "selected_filter_docs": [],
            "hybrid_search": hybrid_search,
            "enable_reranking": enable_reranking,
            "query_rewriting": query_rewriting,
            "top_k": top_k,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "temperature": temperature,
            "theme": theme,
        }
