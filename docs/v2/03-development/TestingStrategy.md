# 测试策略 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/03-development/TestingStrategy.md`（V1） |

V1 把 E2E/Playwright 放得很重。V2：**pytest 是主战场**；前端 E2E 不是学习目标。Agent 质量靠评测集，不是靠点 UI。

---

## 1. 分层

| 层 | 工具 | 何时必须有 |
| --- | --- | --- |
| 单元 | pytest | Repository、Service、Prompt、Tool schema、Provider 解析 |
| Runtime | pytest + Mock LLM | 无工具 / 有工具 / 超轮次；R2 起 Graph 对照 |
| API | pytest + httpx AsyncClient | R1 鉴权与隔离 |
| RAG Eval | 脚本 + 黄金 JSON | R3 |
| Trajectory / Judge | 离线集 | R6 |
| 前端 E2E | 不做为门禁 | 选修 |

---

## 2. 原则

- 能自动的必须自动。
- LLM 单测默认 Mock Provider，不打真实付费 API（可另标 `@pytest.mark.live`）。
- 测行为：工具是否被调用、是否超轮次、是否隔离用户；少测「模型文案是否优美」。
- 测试文件必须是 `test_*.py`，且只放 pytest 用例。连库手写脚本用 `if __name__ == "__main__"` 保护，或移出 `tests/`。

---

## 3. Runtime 最低用例（R0）

1. 模型只回文本 → 不调工具，返回该文本。
2. 模型回 calculator tool_call → 执行 → 第二次无 tool_call → 答案含计算结果。
3. 连续 tool_call 超过 max iterations → `AgentRuntimeException`。
4. 未知工具名 → tool 消息为 not found，不崩溃。

R2 增加：同一用例 Graph vs legacy 工具序列一致；HITL 未 resume 时副作用为 0。

---

## 4. RAG Eval（R3）

- 20–50 条 `{ question, expected_doc_ids, notes }`。
- 指标：recall@k、citation precision、幻觉（答了但引用不支持）。
- 报告写入 `docs/v2` 或 `apps/api/evals/reports/`，不要只存在本地终端。

---

## 5. 怎么跑

```bash
cd apps/api
uv run pytest tests/test_agent_runtime.py tests/test_agent_service.py tests/test_agent_schema.py tests/test_sse.py tests/test_prompt_manager.py tests/test_providers.py tests/test_user_service.py -q
```

连库脚本不会在收集时执行。

CI（R6）：ruff + pytest。无 Key 必须绿。
