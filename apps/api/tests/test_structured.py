from app.ai.structured import FinalAnswer, parse_final_answer


def test_parse_final_answer_reads_json():
    parsed = parse_final_answer('{"answer": "89"}')
    assert parsed == FinalAnswer(answer="89")


def test_parse_final_answer_strips_fence():
    parsed = parse_final_answer('```json\n{"answer": "ok"}\n```')
    assert parsed.answer == "ok"


def test_parse_final_answer_coerces_plain_text():
    parsed = parse_final_answer("计算结果是 89")
    assert parsed.answer == "计算结果是 89"


def test_parse_final_answer_rejects_extra_fields_as_plain_text():
    parsed = parse_final_answer('{"answer": "x", "extra": 1}')
    assert parsed.answer == '{"answer": "x", "extra": 1}'
