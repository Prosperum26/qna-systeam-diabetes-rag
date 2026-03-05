from __future__ import annotations

import re
from typing import Dict, List, Sequence

from .token_counter import TokenCounter


LIST_MARKER_RE = re.compile(
    r"""^(
        [-*•+]       # bullet
        |\d+[.)]     # numbered list like "1." or "1)"
    )\s+""",
    re.VERBOSE,
)


def is_list_like(line: str) -> bool:
    """
    Heuristic to detect list/bullet lines.
    """
    stripped = line.lstrip()
    if not stripped:
        return False
    return bool(LIST_MARKER_RE.match(stripped))


def split_into_units(content: str) -> List[str]:
    """
    Split section content into logical units that should not be split across chunks.

    - Primary delimiter: newline.
    - Consecutive lines that belong to the same list item are merged.
    - Empty lines are discarded.
    """
    if not content:
        return []

    raw_lines = content.splitlines()
    units: List[str] = []
    buffer: List[str] = []
    current_is_list = False

    for raw_line in raw_lines:
        line = raw_line.rstrip()
        if not line.strip():
            # Flush current buffer on blank line.
            if buffer:
                units.append(" ".join(buffer).strip())
                buffer = []
                current_is_list = False
            continue

        line_is_list = is_list_like(line)

        if not buffer:
            buffer = [line.strip()]
            current_is_list = line_is_list
            continue

        if current_is_list and not line_is_list:
            # Continuation of the same list item.
            buffer.append(line.strip())
        elif not current_is_list and not line_is_list:
            # Same paragraph.
            buffer.append(line.strip())
        else:
            # New unit (e.g., new list item or switch between list/paragraph).
            units.append(" ".join(buffer).strip())
            buffer = [line.strip()]
            current_is_list = line_is_list

    if buffer:
        units.append(" ".join(buffer).strip())

    return [u for u in units if u]


def merge_small_sections(
    sections: Sequence[Dict[str, str]],
    token_counter: TokenCounter,
    min_tokens: int = 120,
) -> List[Dict[str, str]]:
    """
    Merge small sections (by token count) forward into the next section.

    - If a section has < min_tokens, it is merged with the following section when possible.
    - Heading of merged section is preserved from the first non-empty heading encountered.
    """
    merged: List[Dict[str, str]] = []
    buffer_section: Dict[str, str] | None = None

    for idx, section in enumerate(sections):
        heading = section.get("heading") or ""
        content = section.get("content") or ""
        if not content.strip():
            continue

        if buffer_section is None:
            buffer_section = {"heading": heading, "content": content}
        else:
            buffer_section["content"] = buffer_section["content"].rstrip() + "\n\n" + content
            if not buffer_section["heading"] and heading:
                buffer_section["heading"] = heading

        # Peek ahead if this is not the last section.
        is_last = idx == len(sections) - 1
        token_count = token_counter.count_tokens(buffer_section["content"])

        if token_count >= min_tokens or is_last:
            merged.append(buffer_section)
            buffer_section = None

    if buffer_section is not None:
        merged.append(buffer_section)

    return merged


__all__ = ["is_list_like", "split_into_units", "merge_small_sections"]

