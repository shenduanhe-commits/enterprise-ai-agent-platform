from app.ai.knowledge.budget import estimate_tokens, fit_context_budget
from app.ai.knowledge.store import SearchHit


def _hit(document_id: int, text: str) -> SearchHit:
    return SearchHit(
        document_id=document_id,
        user_id=7,
        agent_id=3,
        ordinal=0,
        text=text,
        source="doc",
        score=1.0,
        chunk_id=str(document_id),
        dense_score=1.0,
    )


def test_estimate_tokens_counts_cjk_as_one():
    assert estimate_tokens("年假十五天") == 5
    assert estimate_tokens("ABC") == 1


def test_budget_keeps_prefix_hits_that_fit():
    hits = [
        _hit(1, "一二三四五六七八九十"),
        _hit(2, "甲乙丙丁戊己庚辛壬癸"),
        _hit(3, "子丑寅卯辰巳午未申酉"),
    ]
    fitted = fit_context_budget(hits, max_tokens=15)
    assert [hit.document_id for hit in fitted] == [1]
    assert fitted[0].text == hits[0].text


def test_budget_truncates_first_hit_when_it_alone_overflows():
    fitted = fit_context_budget([_hit(1, "年假为十五天必须提前报备审批")], max_tokens=6)
    assert len(fitted) == 1
    assert fitted[0].document_id == 1
    assert fitted[0].text.endswith("…")
    assert estimate_tokens(fitted[0].text) <= 6
    assert len(fitted[0].text) < len("年假为十五天必须提前报备审批")
