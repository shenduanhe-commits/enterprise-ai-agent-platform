import json
import re

from pydantic import BaseModel, ConfigDict


class FinalAnswer(BaseModel):
    """最终给用户的结构化答案。工具循环仍用 tool_calls，只有收束时走这里。"""

    model_config = ConfigDict(extra="forbid")

    answer: str


FINAL_ANSWER_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "final_answer",
        "strict": True,
        "schema": FinalAnswer.model_json_schema(),
    },
}


def parse_final_answer(content: str | None) -> FinalAnswer:
    text = (content or "").strip()
    if not text:
        return FinalAnswer(answer="")

    fenced = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text)
    if fenced:
        text = fenced.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return FinalAnswer(answer=content or "")

    try:
        return FinalAnswer.model_validate(data)
    except Exception:
        return FinalAnswer(answer=content or "")
