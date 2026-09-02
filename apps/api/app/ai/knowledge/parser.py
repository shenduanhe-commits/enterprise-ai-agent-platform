from io import BytesIO
from pathlib import Path

_SUPPORTED = {".md", ".pdf", ".docx"}


def supported_suffix(filename: str | None) -> str | None:
    if not filename:
        return None
    suffix = Path(filename).suffix.lower()
    if suffix in _SUPPORTED:
        return suffix
    return None


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".md":
        return content.decode("utf-8-sig")
    if suffix == ".pdf":
        return _extract_pdf(content)
    if suffix == ".docx":
        return _extract_docx(content)
    raise ValueError(f"unsupported suffix: {suffix}")


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(part for part in pages if part)


def _extract_docx(content: bytes) -> str:
    from docx import Document

    document = Document(BytesIO(content))
    paragraphs = [para.text.strip() for para in document.paragraphs if para.text.strip()]
    return "\n\n".join(paragraphs)
