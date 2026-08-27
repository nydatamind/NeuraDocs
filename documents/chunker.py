"""
NeuraDocs - Structure-Aware Document Chunker
===========================================
Splits structured documents into semantic chunks preserving headings,
paragraph boundaries, tables, and full page/section metadata.
"""

from __future__ import annotations

import re
from typing import List, Optional

from core.models import Chunk
from documents.loader import ExtractedDocument, ExtractedPage


class StructureAwareChunker:
    def __init__(self, chunk_size: int = 900, overlap: int = 150):
        self.chunk_size = chunk_size
        self.overlap = min(overlap, int(chunk_size * 0.4))

    def chunk_document(self, doc: ExtractedDocument, start_chunk_id: int = 0) -> List[Chunk]:
        chunks: List[Chunk] = []
        cid = start_chunk_id

        for page in doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # Check if this page contains dedicated markdown tables
            sections = self._split_into_sections(page_text)

            for section_title, section_body in sections:
                if not section_body.strip():
                    continue

                # If the body is a single compact table or section, keep intact if reasonably sized
                if "[TABLE]" in section_body and len(section_body) <= self.chunk_size * 1.5:
                    chunks.append(
                        Chunk(
                            text=section_body.replace("[TABLE]", "").replace("[/TABLE]", "").strip(),
                            source=doc.filename,
                            chunk_id=cid,
                            page_number=page.page_number,
                            section=section_title or page.section_name,
                            metadata={
                                "file_type": doc.file_type,
                                "is_table": True,
                                "has_tables": page.has_tables,
                            },
                        )
                    )
                    cid += 1
                else:
                    # Recursive split text
                    sub_chunks = self._recursive_split(section_body, self.chunk_size, self.overlap)
                    for text_part in sub_chunks:
                        if text_part.strip():
                            chunks.append(
                                Chunk(
                                    text=text_part.strip(),
                                    source=doc.filename,
                                    chunk_id=cid,
                                    page_number=page.page_number,
                                    section=section_title or page.section_name,
                                    metadata={
                                        "file_type": doc.file_type,
                                        "has_tables": page.has_tables,
                                    },
                                )
                            )
                            cid += 1

        return chunks

    def _split_into_sections(self, text: str) -> List[tuple[Optional[str], str]]:
        """Split text by Markdown / Document Headings (#, ##, ###) while preserving context."""
        lines = text.splitlines()
        sections: List[tuple[Optional[str], str]] = []
        current_heading = None
        current_lines = []

        heading_pattern = re.compile(r"^(#{1,4}\s+|[A-Z0-9\s]{4,30}:|^Chapter\s+\d+|^Section\s+\d+)", re.IGNORECASE)

        for line in lines:
            if heading_pattern.match(line.strip()):
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines)))
                    current_lines = []
                current_heading = line.strip().lstrip("#").strip()
                current_lines.append(line)
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_heading, "\n".join(current_lines)))

        return sections if sections else [(None, text)]

    def _recursive_split(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text cleanly on paragraph (\n\n), then line (\n), then sentence (. ), then word boundaries."""
        text = self._normalize_whitespace(text)
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        n = len(text)

        while start < n:
            end = min(start + chunk_size, n)
            window = text[start:end]

            if end < n:
                # Seek natural boundary near the end
                boundary = -1
                for delim in ("\n\n", ".\n", ". ", "\n", "; ", ", "):
                    b = window.rfind(delim)
                    if b > chunk_size * 0.4:
                        boundary = b + len(delim)
                        break

                if boundary != -1:
                    window = window[:boundary]
                    end = start + len(window)

            cleaned = window.strip()
            if cleaned:
                chunks.append(cleaned)

            if end >= n:
                break

            start = end - overlap if (end - overlap) > start else end

        return chunks

    def _normalize_whitespace(self, text: str) -> str:
        lines = [ln.strip() for ln in text.splitlines()]
        cleaned_lines = []
        blank_streak = 0
        for ln in lines:
            if ln == "":
                blank_streak += 1
                if blank_streak > 1:
                    continue
            else:
                blank_streak = 0
            cleaned_lines.append(ln)
        return "\n".join(cleaned_lines).strip()
