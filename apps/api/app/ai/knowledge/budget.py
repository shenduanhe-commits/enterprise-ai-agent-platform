from dataclasses import replace

from app.ai.knowledge.store import SearchHit


def estimate_tokens(text: str) -> int:
    """粗估：汉字约 1 token，其余约 4 字符 1 token。不引入 tiktoken。"""
    if not text:
        return 0
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    other = len(text) - cjk
    return cjk + (other + 3) // 4


def fit_context_budget(hits: list[SearchHit], max_tokens: int) -> list[SearchHit]:
    """按 rerank 顺序整段装入。装不下下一条就停；第一条就超则截断该段。"""
    if max_tokens <= 0 or not hits:
        return []
    selected: list[SearchHit] = []
    used = 0
    for hit in hits:
        cost = estimate_tokens(hit.text)
        if used + cost <= max_tokens:
            selected.append(hit)
            used += cost
            continue
        if not selected:
            selected.append(_truncate_hit(hit, max_tokens))
        break
    return selected


def _truncate_hit(hit: SearchHit, max_tokens: int) -> SearchHit:
    text = hit.text
    if estimate_tokens(text) <= max_tokens:
        return hit
    lo, hi = 0, len(text)
    best = "…"
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = text[:mid] + "…"
        if estimate_tokens(candidate) <= max_tokens:
            best = candidate
            lo = mid + 1
        else:
            hi = mid - 1
    return replace(hit, text=best)
