from typing import Dict, List

from bs4 import Tag

from .normalizer import normalize_text


def split_sections(container: Tag) -> List[Dict[str, str]]:
    """
    Split content into sections preserving h1/h2/h3 hierarchy.

    - h1: document title level
    - h2: major section
    - h3: subsection under the nearest preceding h2/h1
    - p, ul, ol: assigned to the nearest heading above
    """
    sections: List[Dict[str, str]] = []

    current_heading: str = ""
    current_content_parts: List[str] = []

    def flush_section() -> None:
        nonlocal current_heading, current_content_parts
        if not current_content_parts and not current_heading:
            return

        content = normalize_text("\n".join(current_content_parts).strip())
        if content:
            sections.append(
                {
                    "heading": current_heading or "",
                    "content": content,
                }
            )
        current_content_parts = []

    for elem in container.descendants:
        if not isinstance(elem, Tag):
            continue

        name = elem.name.lower()

        if name in ("h1", "h2", "h3"):
            flush_section()
            heading_text = elem.get_text(" ", strip=True)
            current_heading = normalize_text(heading_text)
            continue

        if name in ("p", "ul", "ol"):
            text = elem.get_text(" ", strip=True)
            text = normalize_text(text)
            if text:
                current_content_parts.append(text)

    flush_section()

    return sections


__all__ = ["split_sections"]

