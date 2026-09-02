import pytest

from app.ai.knowledge.chunker import chunk_markdown
from app.ai.knowledge.embedding import VECTOR_SIZE, HashEmbeddingClient


def test_chunk_markdown_splits_headings():
    chunks = chunk_markdown("# Leave\n15 days.\n\n# Sick\n5 days.\n")
    assert len(chunks) == 2
    assert chunks[0].startswith("# Leave")
    assert chunks[1].startswith("# Sick")


def test_chunk_markdown_empty():
    assert chunk_markdown("  \n\n") == []


def test_chunk_markdown_splits_long_section():
    body = "x" * 2000
    chunks = chunk_markdown(f"# Title\n{body}", max_chars=800)
    assert len(chunks) > 1
    assert all(len(chunk) <= 800 for chunk in chunks)
    assert "x" * 800 in "".join(chunks)


@pytest.mark.asyncio
async def test_hash_embedding_is_stable_and_unit_length():
    client = HashEmbeddingClient()
    first = await client.embed(["hello"])
    second = await client.embed(["hello", "world"])
    assert first[0] == second[0]
    assert first[0] != second[1]
    assert len(first[0]) == VECTOR_SIZE
    norm = sum(value * value for value in first[0]) ** 0.5
    assert abs(norm - 1.0) < 1e-9
