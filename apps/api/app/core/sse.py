import json


def format_sse(event: str, data: dict) -> str:
    """把一条业务事件编码成 SSE 文本帧。

    浏览器 / curl 看到的就是这种格式：

        event: token
        data: {"text":"你"}

        event: done
        data: {"conversation_id":10}

    注意末尾必须有一个空行（\\n\\n），客户端才知道这一帧结束。
    """

    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
