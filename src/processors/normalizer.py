import re
import unicodedata


_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{2,}")


def normalize_text(text: str) -> str:
    """
    Normalize Unicode and whitespace according to project specification:
    - Unicode NFC
    - replace non-breaking space (\xa0) with regular space
    - collapse multiple spaces into one
    - collapse multiple newlines into a single newline
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)
    text = text.replace("\xa0", " ")

    lines = []
    for line in text.splitlines():
        line = _MULTI_SPACE_RE.sub(" ", line)
        lines.append(line.strip())
    text = "\n".join(lines)

    text = _MULTI_NEWLINE_RE.sub("\n", text).strip()

    return text


__all__ = ["normalize_text"]

