from app.core.sse import format_sse


def test_format_sse_named_event_and_blank_line():
    frame = format_sse("token", {"text": "你"})

    assert frame.startswith("event: token\n")
    assert 'data: {"text": "你"}' in frame
    assert frame.endswith("\n\n")


def test_format_sse_done_keeps_conversation_id():
    frame = format_sse("done", {"conversation_id": 10})

    assert "event: done\n" in frame
    assert '"conversation_id": 10' in frame
