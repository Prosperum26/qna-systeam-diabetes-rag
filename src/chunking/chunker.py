from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .rules import merge_small_sections, split_into_units
from .token_counter import TokenCounter


@dataclass
class HybridChunker:
    """
    Hybrid section-aware + sliding-window chunker for medical RAG documents.
    """

    token_counter: TokenCounter
    max_tokens_per_chunk: int = 450
    chunk_size: int = 400
    overlap: int = 60
    min_section_tokens: int = 120

    def chunk_document(self, document: Dict) -> List[Dict]:
        """
        Chunk a single document into embedding-ready chunks.
        """
        doc_id: str = document.get("doc_id", "")
        title: str = document.get("title", "")
        sections = document.get("sections") or []

        normalized_sections = merge_small_sections(
            sections=sections,
            token_counter=self.token_counter,
            min_tokens=self.min_section_tokens,
        )

        chunks: List[Dict] = []
        position = 0

        for section in normalized_sections:
            heading = section.get("heading") or ""
            content = section.get("content") or ""
            if not content.strip():
                continue

            section_chunks = self._chunk_single_section(
                doc_id=doc_id,
                title=title,
                heading=heading,
                content=content,
                start_position=position,
            )
            chunks.extend(section_chunks)
            position += len(section_chunks)

        return chunks

    def _build_chunk_text(self, title: str, heading: str, body: str) -> str:
        lines = []
        if title:
            lines.append(title.strip())
        if heading:
            lines.append(heading.strip())
        if body:
            lines.append(body.strip())
        return "\n".join(lines)

    def _chunk_single_section(
        self,
        doc_id: str,
        title: str,
        heading: str,
        content: str,
        start_position: int,
    ) -> List[Dict]:
        """
        Chunk a single (possibly merged) section into one or more chunks.
        """
        units = split_into_units(content)
        full_body = "\n\n".join(units) if units else content
        full_text = self._build_chunk_text(title, heading, full_body)
        total_tokens = self.token_counter.count_tokens(full_text)

        if total_tokens <= self.max_tokens_per_chunk:
            token_count = total_tokens
            chunk_id = f"{doc_id}_{start_position}"
            return [
                {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "title": title,
                    "heading": heading,
                    "text": full_text,
                    "position": start_position,
                    "token_count": token_count,
                }
            ]

        return self._sliding_window_chunks(
            doc_id=doc_id,
            title=title,
            heading=heading,
            units=units,
            start_position=start_position,
        )

    def _sliding_window_chunks(
        self,
        doc_id: str,
        title: str,
        heading: str,
        units: List[str],
        start_position: int,
    ) -> List[Dict]:
        """
        Apply sliding-window chunking over logical units (paragraphs/list items).
        """
        chunks: List[Dict] = []
        position = start_position
        n = len(units)
        start_idx = 0

        while start_idx < n:
            end_idx = start_idx
            best_text = ""
            best_token_count = 0

            while end_idx < n:
                body = "\n\n".join(units[start_idx : end_idx + 1])
                candidate_text = self._build_chunk_text(title, heading, body)
                token_count = self.token_counter.count_tokens(candidate_text)

                if token_count > self.max_tokens_per_chunk:
                    break

                best_text = candidate_text
                best_token_count = token_count
                end_idx += 1

                if best_token_count >= self.chunk_size:
                    break

            if not best_text:
                # Fallback: force one unit even if it slightly exceeds the limit.
                body = units[start_idx]
                best_text = self._build_chunk_text(title, heading, body)
                best_token_count = min(
                    self.token_counter.count_tokens(best_text),
                    self.max_tokens_per_chunk,
                )
                end_idx = start_idx + 1

            chunk_id = f"{doc_id}_{position}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "title": title,
                    "heading": heading,
                    "text": best_text,
                    "position": position,
                    "token_count": best_token_count,
                }
            )

            if end_idx >= n:
                break

            # Determine next start index to approximate token overlap.
            overlap_tokens = 0
            next_start = end_idx
            idx = end_idx - 1

            while idx >= 0 and overlap_tokens < self.overlap:
                body = "\n\n".join(units[idx:end_idx])
                overlap_text = self._build_chunk_text(title, heading, body)
                overlap_tokens = self.token_counter.count_tokens(overlap_text)
                next_start = idx
                idx -= 1

            if next_start <= start_idx:
                next_start = end_idx

            start_idx = next_start
            position += 1

        return chunks


__all__ = ["HybridChunker"]

