# EAAP 状态 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 更新日期 | 2026-08-18 |
| 替代 | 根目录 `EAAP_STATUS.md`、`PROJECT_CHANGELOG.md`（V1，已过期） |

---

## 1. 一句话

后端能注册登录、创建自己的 Agent，并用 Mock / Qwen 跑工具循环；SSE 流式已接通。**当前阶段：R1 收口中。** MVP 仍差 R2–R3。

---

## 2. 进度条

```
R0  基线修复          ████████████  完成
R1  认证 + 流式 API   ██████████░░  进行中（后端主路径已有，前端演示壳未接）
R2  LangGraph Runtime ░░░░░░░░░░░░  未开始
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
| Chat | `POST /api/v1/agents/{id}/chat`（非流式）、`/chat/stream`（SSE） |
| 会话 | `GET /api/v1/conversations`、`GET /api/v1/conversations/{id}/messages` |
| 模型 | `user`、`agent`、`prompt`、`conversation`、`conversation_message` |

### AI

- `LLMGateway`：mock 始终注册；Qwen / OpenAI / Anthropic 按 API Key 注册。
- `AgentExecutor`：最多 5 轮工具循环；SSE 事件 `token` / `tool` / `done` / `error`。
- Qwen、OpenAI 解析 OpenAI 形态 `tool_calls`；Anthropic 走 `messages.create` + `tool_use`。
- `PromptManager`：优先最新 Prompt 模板，否则 Agent `system_prompt`。
- `MemoryManager`：最近 10 条消息。
- `ToolManager`：内置 calculator，带 JSON Schema。calculator 内部仍是 `eval()`。

### 前端

- 仍是 Vue 脚手架。`router/agents.ts` 等为空。**不阻塞后端验收。**

### 测试

- pytest：`test_agent_runtime.py`、`test_agent_service.py`、`test_agent_schema.py`、`test_sse.py`、`test_prompt_manager.py`、`test_providers.py`、`test_user_service.py`。
- 连库手写脚本已用 `if __name__ == "__main__"` 保护。

---

## 4. 已知缺口

1. Calculator 使用 `eval()`，不能当生产工具。
2. SSE `token` 是整段回答切块，不是模型真流式。
3. 会话 `update` / `delete` 尚未挂路由，Service 层也不带 `user_id`。
4. 前端未接登录 / Agent / Chat。
5. R2 起：LangGraph、RAG、MCP。

---

## 5. 下一步

只收口 R1 演示与文档，**不要开 LangGraph**：

1. Swagger/curl：注册 → 登录 → 建 Agent → `/chat/stream` → 拉会话历史。
2. 前端三页（选修）或保持 Swagger。
3. 视需要把 calculator 换成安全表达式解析。

R1 完成标准：独立走通「注册 → 建 Agent → 两轮对话 → 拉历史」。

---

## 6. 变更记录（V2 起）

| 日期 | 说明 |
| --- | --- |
| 2026-08-18 | R0 闭环 + R1 后端：JWT access/refresh、SSE、会话历史；OpenAI/Anthropic tool 解析对齐 |
| 2026-08-18 | 测试命名：`text_agent_service.py` → `test_agent_service.py`；`conversation_message_service` 拼写已改 |
| 2026-08-15 | 建立 V2 文档集；确认基线与 R0 为下一步 |
| 2026-07-31 | （历史）M0 工程基础、M1 分层与 User、Agent CRUD 与自研 Runtime 已在代码中 |
| 2026-07-30 | （历史）Docker / Postgres / Redis / Qdrant 就绪 |
