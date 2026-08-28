"""
NeuraDocs - Core Configuration & Constants
=========================================
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# App paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / ".neuradocs"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "neuradocs.db"
VECTOR_INDEX_DIR = DATA_DIR / "vector_store"
VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Internal models — not exposed in UI
DEFAULT_MODEL  = "openai/gpt-oss-20b"   # Primary: fastest
FALLBACK_MODEL = "openai/gpt-oss-120b"  # Secondary: best quality

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# RAG Hyperparameters Defaults
DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150
DEFAULT_TOP_K = 5
DEFAULT_CANDIDATE_K = 15
DEFAULT_TEMPERATURE = 0.2
DEFAULT_CONFIDENCE_THRESHOLD = 0.25

# System prompt
SYSTEM_PROMPT = """You are NeuraDocs, an elite, professional document intelligence and RAG analyst.
Your mission is to provide accurate, comprehensive, and well-structured answers grounded strictly in the provided document excerpts.

Guidelines:
1. Grounding: Answer using ONLY the provided context. Do NOT invent facts or speculate beyond the provided text.
2. Citations: Explicitly cite source filenames and pages inline using Markdown tags like `[filename.pdf: Page X]`.
3. Hallucination Control: If the provided documents do not contain the answer, explicitly state: "Based on the provided documents, I could not find information regarding [topic]."
4. Multi-Document Comparison: When contrasting multiple documents, organize the answer with clear headings for each source.
5. Numerical Precision: Preserve all exact figures, currencies, metrics, dates, and technical identifiers faithfully.
6. Formatting: Use Markdown lists, bold emphasis, code blocks, or tables where appropriate for maximum clarity.
"""

QUERY_REWRITE_PROMPT = """You are a conversational query contextualizer.
Given the chat history and the user's latest follow-up question, rewrite the question into a standalone search query that can be used for document retrieval.
- Preserve all key terms, entity names, numbers, and specific references from the conversation.
- If the question is already standalone, return it unchanged.
- Output ONLY the rewritten search query without any explanation, markdown, or commentary.
"""
