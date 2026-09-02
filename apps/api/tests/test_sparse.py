from app.ai.knowledge.sparse import encode_sparse, rrf_scores, sparse_dot


def test_encode_sparse_is_stable_and_ordered():
    first = encode_sparse("年假为 15 天。")
    second = encode_sparse("年假为 15 天。")
    assert first.indices == second.indices
    assert first.values == second.values
    assert first.indices == sorted(first.indices)
    assert not first.is_empty()


def test_sparse_dot_matches_shared_terms():
    query = encode_sparse("ABC-123")
    ticket = encode_sparse("工单号 ABC-123 已关闭。")
    weather = encode_sparse("今天天气很好，适合散步。")
    assert sparse_dot(query, ticket) > 0
    assert sparse_dot(query, weather) == 0


def test_rrf_scores_prefer_items_on_both_lists():
    scores = rrf_scores(["weather", "ticket"], ["ticket"])
    assert scores["ticket"] > scores["weather"]
