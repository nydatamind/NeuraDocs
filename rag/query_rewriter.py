"""
NeuraDocs - Conversational Query Rewriter
=========================================
Contextualizes follow-up questions using prior chat turns so search
engines can retrieve the correct chunks even when pronouns or implicit
references are used.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from core.config import QUERY_REWRITE_PROMPT
from core.models import ChatMessage

logger = logging.getLogger(__name__)


def rewrite_query(
    api_key: str,
    model: str,
    latest_query: str,
    history: List[ChatMessage],
) -> str:
    """Rewrite follow-up question into a standalone search query using Groq."""
    if not history or not api_key:
        return latest_query

    # If the question is already long or explicit and history is empty, skip
    non_system_history = [m for m in history if m.role in ("user", "assistant")]
    if len(non_system_history) == 0:
        return latest_query

    # Format last 4 turns
    recent_history = non_system_history[-4:]
    history_text = "\n".join(
        f"{m.role.capitalize()}: {m.content[:300]}" for m in recent_history
    )

    prompt = (
        f"{QUERY_REWRITE_PROMPT}\n\n"
        f"--- CONVERSATION HISTORY ---\n"
        f"{history_text}\n\n"
        f"--- LATEST QUESTION ---\n"
        f"{latest_query}\n\n"
        f"Standalone Query:"
    )

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=100,
        )
        rewritten = completion.choices[0].message.content.strip()
        # Clean quotes
        rewritten = rewritten.strip('"').strip("'")
        if rewritten and len(rewritten) > 2:
            return rewritten
    except Exception as e:
        logger.warning(f"Query rewrite failed ({e}), falling back to original query.")

    return latest_query
