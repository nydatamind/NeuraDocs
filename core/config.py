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
Your mission is to provide accurate, comprehensive, and well-structured answers.

Guidelines:
1. Grounding & Citations: First, search and answer using the attached document context. You MUST explicitly cite the document name and page number inline (e.g., `[filename.pdf: Page X]` or `[data.csv: Row Y]`) for every claim retrieved from the documents.
2. Outside Document Fallback & Reference: If the answer is NOT in the attached documents, you MUST:
   - First, explicitly write this exact warning message: "⚠️ Note: This information was not found in the attached documents, so I am answering using my general knowledge / search capabilities:"
   - Then, provide a complete, helpful answer using your general knowledge.
   - At the end of your answer, explain or cite where this general knowledge/search information is sourced from or what search reference sources apply.
3. Keep the workflow, visual styling, and output formatting clean and unchanged.
"""

QUERY_REWRITE_PROMPT = """You are a conversational query contextualizer.
Given the chat history and the user's latest follow-up question, rewrite the question into a standalone search query that can be used for document retrieval.
- Preserve all key terms, entity names, numbers, and specific references from the conversation.
- If the question is already standalone, return it unchanged.
- Output ONLY the rewritten search query without any explanation, markdown, or commentary.
"""
