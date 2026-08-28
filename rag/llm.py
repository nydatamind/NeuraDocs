"""
NeuraDocs - Groq LLM Client & Real Streaming
============================================
Handles LLM streaming completion, prompt formatting, context injection,
and confidence calculation.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Generator, List, Optional, Tuple

from core.config import SYSTEM_PROMPT, FALLBACK_MODEL
from core.models import ChatMessage, RetrievedChunk


def build_context_block(retrieved: List[RetrievedChunk]) -> str:
    if not retrieved:
        return "No relevant excerpts found in documents."

    parts = []
    for i, r in enumerate(retrieved, start=1):
        page_info = f", Page {r.chunk.page_number}" if r.chunk.page_number else ""
        section_info = f", Section: {r.chunk.section}" if r.chunk.section else ""
        parts.append(
            f"=== EXCERPT {i} [Source: {r.chunk.source}{page_info}{section_info} | Chunk ID: #{r.chunk.chunk_id}] ===\n"
            f"{r.chunk.text}\n"
        )
    return "\n\n".join(parts)


def compute_confidence(retrieved: List[RetrievedChunk]) -> float:
    """Calculate an aggregate grounding confidence score based on retrieval scores."""
    if not retrieved:
        return 0.0

    scores = [r.score for r in retrieved]
    avg_score = sum(scores) / len(scores)

    # Normalize roughly to a 0.0 - 1.0 confidence indicator
    if retrieved[0].retrieval_method == "hybrid_rrf":
        # RRF scores typically range 0.015 - 0.035 for top results
        confidence = min(max((avg_score - 0.01) * 35.0, 0.1), 0.99)
    else:
        # Cosine / dot product score
        confidence = min(max(avg_score, 0.05), 0.99)

    return round(confidence, 2)


def stream_groq_response(
    api_key: str,
    model: str,
    question: str,
    retrieved: List[RetrievedChunk],
    history: Optional[List[ChatMessage]] = None,
    temperature: float = 0.2,
) -> Generator[str, None, None]:
    """Stream real token chunks from Groq's chat completion API.
    Automatically retries with FALLBACK_MODEL if the primary model fails.
    """
    from groq import Groq

    client = Groq(api_key=api_key)
    context_block = build_context_block(retrieved)

    user_content = (
        f"Context from uploaded documents:\n\n{context_block}\n\n"
        f"----------------------------------------\n"
        f"User Question: {question}\n\n"
        f"Please provide an accurate, grounded answer using the context above. Cite sources explicitly."
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for m in history[-6:]:
            if m.role in ("user", "assistant"):
                messages.append({"role": m.role, "content": m.content})

    messages.append({"role": "user", "content": user_content})

    models_to_try = [model]
    if model != FALLBACK_MODEL:
        models_to_try.append(FALLBACK_MODEL)

    last_exc = None
    for attempt_model in models_to_try:
        try:
            stream = client.chat.completions.create(
                model=attempt_model,
                messages=messages,
                temperature=temperature,
                max_tokens=2048,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
            return  # success — stop here
        except Exception as exc:
            last_exc = exc
            continue  # silently try fallback

    # Both models failed — raise the last error
    raise last_exc


def call_groq_blocking(
    api_key: str,
    model: str,
    question: str,
    retrieved: List[RetrievedChunk],
    history: Optional[List[ChatMessage]] = None,
    temperature: float = 0.2,
) -> str:
    """Non-streaming fallback for Groq chat completion."""
    tokens = []
    for t in stream_groq_response(api_key, model, question, retrieved, history, temperature):
        tokens.append(t)
    return "".join(tokens)
