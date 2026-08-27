"""
NeuraDocs - Conversation & Document Exporter
============================================
Exports chat histories and grounded responses in Markdown, Text, and JSON formats.
"""

from __future__ import annotations

import json
import time
from typing import List

from core.models import ChatMessage, ChatSession


def export_session_to_markdown(session: ChatSession) -> str:
    lines = [
        f"# NeuraDocs — Chat Export: {session.title}",
        f"*Exported on: {time.strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "---",
        "",
    ]

    for msg in session.messages:
        role_label = "🧑‍💻 User" if msg.role == "user" else "🧠 NeuraDocs AI"
        lines.append(f"### {role_label}")
        lines.append(msg.content.strip())
        lines.append("")

        if msg.sources:
            lines.append("**Sources Consulted:**")
            for s in msg.sources:
                page_str = f" (Page {s.get('page')})" if s.get("page") else ""
                lines.append(f"- 📄 `{s.get('source')}`{page_str} — Chunk #{s.get('chunk_id')}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def export_session_to_text(session: ChatSession) -> str:
    lines = [
        f"NeuraDocs Chat Session: {session.title}",
        f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
    ]
    for msg in session.messages:
        role = "USER" if msg.role == "user" else "ASSISTANT"
        lines.append(f"[{role}]:")
        lines.append(msg.content.strip())
        lines.append("")
        if msg.sources:
            lines.append("SOURCES:")
            for s in msg.sources:
                lines.append(f" - {s.get('source')} (Score: {s.get('score', 0):.2f})")
            lines.append("")
        lines.append("-" * 40)
        lines.append("")
    return "\n".join(lines)


def export_session_to_json(session: ChatSession) -> str:
    return json.dumps(session.to_dict(), indent=2)
