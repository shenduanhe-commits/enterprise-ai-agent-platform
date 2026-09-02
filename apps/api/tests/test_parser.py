from io import BytesIO

from app.ai.knowledge.parser import extract_text, supported_suffix


def _docx_bytes(text: str) -> bytes:
    from docx import Document

    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _pdf_bytes(text: str) -> bytes:
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET".encode("latin-1")
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n",
        b"4 0 obj<< /Length %d >>stream\n" % len(stream)
        + stream
        + b"\nendstream\nendobj\n",
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
    ]
    body = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(body))
        body += obj
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        xref += f"{offset:010d} 00000 n \n".encode("ascii")
    tail = (
        b"trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(len(body)).encode("ascii")
        + b"\n%%EOF\n"
    )
    return body + xref + tail


def test_supported_suffix():
    assert supported_suffix("a.MD") == ".md"
    assert supported_suffix("a.pdf") == ".pdf"
    assert supported_suffix("a.docx") == ".docx"
    assert supported_suffix("a.txt") is None
    assert supported_suffix(None) is None


def test_extract_markdown():
    assert "年假" in extract_text("handbook.md", "# 年假\n15 天\n".encode())


def test_extract_docx():
    text = extract_text("handbook.docx", _docx_bytes("年假为 15 天。"))
    assert "年假为 15 天" in text


def test_extract_pdf():
    text = extract_text("handbook.pdf", _pdf_bytes("Annual leave is 15 days."))
    assert "15 days" in text
