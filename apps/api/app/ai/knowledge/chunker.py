import re

_MAX_CHARS = 800


def chunk_markdown(text: str, max_chars: int = _MAX_CHARS) -> list[str]:
    """按 Markdown 标题切开，过长再按段落切。空文档返回空列表。"""
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    sections = re.split(r"(?m)(?=^#{1,6} )", normalized)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        chunks.extend(_split_long(section, max_chars))
    return chunks


def _split_long(section: str, max_chars: int) -> list[str]:
    if len(section) <= max_chars:
        return [section]

    pieces: list[str] = []
    paragraphs = re.split(r"\n\s*\n", section)
    buf = ""
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        candidate = f"{buf}\n\n{paragraph}".strip() if buf else paragraph
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            pieces.append(buf)
            buf = ""
        if len(paragraph) <= max_chars:
            buf = paragraph
            continue
        for start in range(0, len(paragraph), max_chars):
            pieces.append(paragraph[start : start + max_chars])
    if buf:
        pieces.append(buf)
    return pieces
