"""
NeuraDocs - Modern Document Management & Preview Component
==========================================================
Displays document cards, metadata (size, chunks, pages), preview modal,
and single-file deletion.
"""

from __future__ import annotations

import streamlit as st
from typing import List, Optional

from core.database import Database
from core.models import DocumentRecord


def render_document_manager(db: Database, on_delete_callback=None):
    docs = db.get_documents()
    if not docs:
        st.info("No documents uploaded yet.")
        return

    st.markdown("##### 📑 Uploaded Documents")

    for doc in docs:
        col_icon, col_info, col_del = st.columns([1, 6, 1])

        # Icon based on type
        icon = "📄"
        if doc.file_type == "pdf":
            icon = "📕"
        elif doc.file_type in ("docx", "doc"):
            icon = "📘"
        elif doc.file_type in ("csv", "xlsx", "excel"):
            icon = "📊"

        with col_icon:
            st.markdown(f"<div style='font-size:1.4rem; padding-top:4px;'>{icon}</div>", unsafe_allow_html=True)

        with col_info:
            size_kb = doc.file_size_bytes / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            st.markdown(
                f"**{doc.filename}**  \n"
                f"<span style='font-size:0.75rem; color:var(--text-lo);'>"
                f"{doc.page_count} page(s) · {doc.chunk_count} chunks · {size_str}</span>",
                unsafe_allow_html=True,
            )

        with col_del:
            if st.button("🗑️", key=f"del_doc_{doc.doc_id}", help="Delete document"):
                db.delete_document(doc.filename)
                if on_delete_callback:
                    on_delete_callback(doc.filename)
                st.toast(f"Deleted {doc.filename}", icon="🗑️")
                st.rerun()

        st.markdown("<hr style='margin: 4px 0; opacity:0.15;'/>", unsafe_allow_html=True)
