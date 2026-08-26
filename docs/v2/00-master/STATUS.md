# EAAP 状态 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 更新日期 | 2026-08-26 |
| 替代 | 根目录 `EAAP_STATUS.md`、`PROJECT_CHANGELOG.md`（V1，已过期） |

---

## 1. 一句话

后端能注册登录、创建自己的 Agent，并用 Mock / Qwen 跑工具循环；SSE 与手写 LangGraph 已接通，危险工具可 HITL 暂停。**R2 进行中**（checkpoint + interrupt；Structured output / Langfuse 未做）。前端演示壳仍未接。

---

## 2. 进度条

```
R0  基线修复          ████████████  完成
R1  认证 + 流式 API   ██████████░░  后端验收完成；前端演示壳选修
R2  LangGraph Runtime ████████░░░░  图 + checkpoint + HITL；缺结构化输出 / 轨迹
R3  企业 RAG          ░░░░░░░░░░░░  未开始
R4  MCP               ░░░░░░░░░░░░  未开始
R5  Multi-Agent / A2A ░░░░░░░░░░░░  未开始
R6  生产化 + 作品集   ░░░░░░░░░░░░  未开始
```

---

## 3. 已落地（以代码为准）

### 工程

- Monorepo：`apps/web`（Vue 3.5 / Vite 8 / Tailwind 4）、`apps/api`（Python 3.12 / uv / FastAPI）。
- Docker Compose：PostgreSQL 16、Redis 7、Qdrant。
- 分层：API → Service → Repository → Model；Alembic；`EAAPException`。

### 领域与 API

| 能力 | 路径 / 说明 |
| --- | --- |
| Health | `/api/v1/health` |
| 注册 | `POST /api/v1/auth/register`（`POST /users` 仍可用） |
| 登录 / 刷新 | `POST /api/v1/auth/login`、`/auth/refresh`；Bearer access JWT |
| 当前用户 | `GET /api/v1/auth/me` |
| Agent CRUD | `POST/GET /api/v1/agents`（按 `created_by` 隔离） |
| Chat | `POST /api/v1/agents/{id}/chat`（非流式，可 interrupted）、`/chat/stream`（SSE） |
| 会话 | `GET /api/v1/conversations`、`GET /api/v1/conversations/{id}/messages` |
| HITL | `GET /api/v1/runs/{id}`、`POST /api/v1/runs/{id}/resume`（run_id = conversation_id） |
| 模型 | `user`、`agent`、`prompt`、`conversation`、`conversation_message` |

### AI

- `LLMGateway`：mock 始终注册；Qwen / OpenAI / Anthropic 按 API Key 注册。
- `AgentExecutor`：非流式/SSE 走 `StateGraph`；loop 留下对照。
- LangGraph：手写图；Postgres checkpointer（连不上则内存）；`thread_id = conversation_id`。
- HITL：`send_email` 需批准；每个 tool call 单独勾选，一次 `/runs/{id}/resume` 提交 `decisions`。
- Qwen、OpenAI 解析 OpenAI 形态 `tool_calls`；Anthropic 走 `messages.create` + `tool_use`。
- `PromptManager`：优先最新 Prompt 模板，否则 Agent `system_prompt`。
- `MemoryManager`：最近 10 条消息。
- `ToolManager`：内置 calculator、send_email；calculator 内部仍是 `eval()`。

### 前端

- 仍是 Vue 脚手架。`router/agents.ts` 等为空。**不阻塞后端验收。**

### 测试

- pytest：含 `test_agent_graph.py`（图 / checkpoint / HITL）。
- 连库手写脚本已用 `if __name__ == "__main__"` 保护。

---

## 4. 已知缺口

1. Calculator 使用 `eval()`，不能当生产工具。
2. SSE `token` 是整段回答切块，不是模型真流式。
3. 会话 `update` / `delete` 尚未挂路由，Service 层也不带 `user_id`。
4. 前端未接登录 / Agent / Chat。
5. R2 剩余：Structured output、节点轨迹 / Langfuse。

---

## 5. 下一步

R2 已有图、checkpoint、HITL。**不要开 RAG**，除非明确开始 R3。

下一步可选：

1. Structured output（最终答案结构化）。
2. 节点可查（表或 Langfuse）。
3. 前端一个「批准」按钮，或继续 Swagger。

本机演示账号：`user@eaap.com` / `user`（仅开发库）。

---

## 6. 变更记录（V2 起）

| 日期 | 说明 |
| --- | --- |
| 2026-08-26 | R2：StateGraph + checkpoint + HITL（send_email / resume） |
| 2026-08-18 | R0 闭环 + R1 后端：JWT access/refresh、SSE、会话历史；OpenAI/Anthropic tool 解析对齐 |
| 2026-08-18 | 测试命名：`text_agent_service.py` → `test_agent_service.py`；`conversation_message_service` 拼写已改 |
| 2026-08-15 | 建立 V2 文档集；确认基线与 R0 为下一步 |
| 2026-07-31 | （历史）M0 工程基础、M1 分层与 User、Agent CRUD 与自研 Runtime 已在代码中 |
| 2026-07-30 | （历史）Docker / Postgres / Redis / Qdrant 就绪 |
