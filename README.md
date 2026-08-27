# 🧠 NeuraDocs 2.0 — Enterprise AI Document Intelligence & RAG Chat

Chat with your **PDF, DOCX, CSV, Excel, TXT, MD, HTML** files with enterprise-grade retrieval precision.
Featuring **Hybrid Search (BM25 + FAISS via RRF)**, **Contextual Reranking**, **Real-Time Groq Token Streaming**, and **Zero-Cloud Local Embeddings**.

> **Developed by Nitin Yadav**

---

## ✨ Features

- 📁 **Universal Document Parsing**: Ingest PDF, Word (DOCX), Excel (XLSX), CSV, Markdown, Text, and HTML files with automatic table extraction and OCR fallback.
- 🎯 **Hybrid Retrieval (Dense + Sparse)**: Combines local semantic vector embeddings with BM25 exact keyword matching using Reciprocal Rank Fusion (RRF) for 100% precision on names, numbers, acronyms, and concepts.
- ⚡ **Contextual Reranking**: Two-stage pipeline over-fetches candidates and reranks them before context construction.
- 🧠 **Conversational Query Contextualization**: Automatically rewrites ambiguous follow-up questions using chat history into standalone search queries.
- 🚀 **Real-Time Token Streaming**: Direct streaming via Groq's high-speed inference engine (Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B, DeepSeek R1).
- 💾 **Persistent SQLite + FAISS Database**: Never lose your uploaded documents or chat sessions on page reload.
- 💬 **Multi-Chat Session Management**: Create, switch, rename, and delete conversation threads with ease.
- 🎯 **Document-Level Filtering**: Search across all documents or restrict query scope to selected documents.
- 📚 **Grounded Source Citations**: Inline citations with relevance scores, page numbers, and preview cards.
- 📥 **Export Functionality**: Export answers and chat histories directly to Markdown, Text, or JSON.
- 🎨 **Modern SaaS Design System**: Glassmorphism UI, Dark and Light mode toggles, micro-animations, and responsive layout.

---

## 🚀 Quickstart

### 1. Requirements
- Python 3.10+
- Free Groq API Key from [console.groq.com/keys](https://console.groq.com/keys)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment (Optional)
Copy `.env.example` to `.env` and add your Groq API key:
```bash
GROQ_API_KEY=gsk_your_key_here
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🏗️ Architecture Pipeline

```
DOCUMENT UPLOAD
  │
  ├─► Multi-Format Parser (PDF / DOCX / CSV / XLSX / HTML)
  ├─► Structure-Aware Chunker (Sections, Headings, Tables)
  ├─► Local SentenceTransformers Embedding (all-MiniLM-L6-v2)
  └─► Persistent SQLite & FAISS Storage

USER QUERY
  │
  ├─► Conversational Query Rewriter (Resolves pronouns & context)
  ├─► Hybrid Search (Dense FAISS Vector + Sparse BM25 Keyword)
  ├─► Reciprocal Rank Fusion (RRF)
  ├─► Candidate Re-ranking & Confidence Scoring
  └─► Groq Ultra-Fast Token Streaming with Inline Citations
```

---

## 📁 Project Structure

```
NeuraDocs/
├── app.py                      # Main Streamlit application
├── rag_engine.py               # Orchestrator & legacy compatibility layer
├── requirements.txt            # Production dependencies
├── .env.example                # Environment variables template
├── core/
│   ├── config.py               # Settings, model registry, prompts
│   ├── database.py             # SQLite persistence (documents, chunks, chats)
│   └── models.py               # Core data classes (Chunk, DocumentRecord, Session)
├── documents/
│   ├── loader.py               # Multi-format parsers (PDF, DOCX, CSV, Excel, etc.)
│   └── chunker.py              # Structure-aware recursive & table chunker
├── rag/
│   ├── embeddings.py           # Local SentenceTransformers embedding engine
│   ├── vector_store.py         # Persistent FAISS vector index
│   ├── hybrid_search.py        # BM25 + FAISS + Reciprocal Rank Fusion
│   ├── reranker.py             # Contextual candidate reranker
│   ├── query_rewriter.py       # Multi-turn query standalone contextualizer
│   └── llm.py                  # Groq streaming client & confidence scoring
└── ui/
    ├── styles.py               # Modern CSS glassmorphic design system
    ├── sidebar.py              # Sessions, file uploads, filters, settings
    ├── chat_view.py            # Streamed chat bubbles & source cards
    ├── doc_viewer.py           # Document explorer & inspector
    └── exporter.py             # Markdown, TXT, JSON chat exporter
```

---

<p align="center">Made with ❤️ — <b>Developed by Nitin Yadav</b></p>
