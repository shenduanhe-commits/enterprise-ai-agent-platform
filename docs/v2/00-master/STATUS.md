# EAAP 状态 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 更新日期 | 2026-08-15 |
| 替代 | 根目录 `EAAP_STATUS.md`、`PROJECT_CHANGELOG.md`（V1，已过期） |

---

## 1. 一句话

工程上已越过脚手架，后端能创建 Agent 并跑一轮非流式对话；**尚未对齐 V2 的 MVP（R0–R3）**。当前阶段：**R0 未开始**。

旧状态文件仍写着 Milestone 0 In Progress，以本文为准。

---

## 2. 进度条

```
R0  基线修复          ░░░░░░░░░░░░  未开始（代码有缺口）
R1  认证 + 流式 API   ░░░░░░░░░░░░  未开始
R2  LangGraph Runtime ░░░░░░░░░░░░  未开始
R3  企业 RAG          ░░░░░░░░░░░░  未开始
R4  MCP               ░░░░░░░░░░░░  未开始
R5  Multi-Agent / A2A ░░░░░░░░░░░░  未开始
R6  生产化 + 作品集   ░░░░░░░░░░░░  未开始
```

相对 MVP（R0–R3）约 **35–40%** 的代码预支（自研 Runtime 和 Agent CRUD），但 R0 的闭环修复还没做。

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
| User CRUD | `POST/GET /api/v1/users`（无登录，客户端仍传 `password_hash`） |
| Agent CRUD | `POST/GET /api/v1/agents` |
| Chat | `POST /api/v1/agents/{id}/chat`（非流式） |
| 模型 | `user`、`agent`、`prompt`、`conversation`、`conversation_message` |

### AI

- `LLMGateway`：Qwen / OpenAI / Anthropic（按 API Key 注册）。
- `AgentExecutor`：最多 5 轮工具循环。
- `PromptManager`：优先最新 Prompt 模板，否则 Agent `system_prompt`。
- `MemoryManager`：最近 10 条消息。
- `ToolManager`：仅内置 calculator；schema 参数目前为空。
- Qwen Provider 已解析 `tool_calls`；OpenAI Provider **未解析**。

### 前端

- 仍是 Vue 脚手架。`router/agents.ts` 等为空。**不阻塞 R0。**

### 测试

- `apps/api/tests/` 下有 repository / service / schema / runtime / prompt 等；存在命名问题（如 `text_agent_service.py`）。

---

## 4. 已知缺口（R0 必须修）

1. OpenAI（及需对齐的 Anthropic）未回传 `tool_calls`，工具循环在这些 Provider 上是断的。
2. `BaseTool.schema` 没有真实 JSON Schema 参数。
3. 密码由客户端当哈希传入。
4. 无 Mock Provider 默认路径时，无 Key 环境测试不稳。
5. Chat 非流式、无鉴权。

---

## 5. 下一步

只做 **R0**，不要并行开 LangGraph 或 RAG：

1. 所有 Provider 统一解析 `tool_calls`。
2. calculator 带真实 schema。
3. 服务端 Argon2 哈希，Schema 改为收 `password`。
4. Mock Provider 可跑通无 Key 测试。
5. runtime 测试覆盖：无工具 / 有工具 / 超轮次。

R0 完成标准：`POST /api/v1/agents/{id}/chat` 在 Qwen 或 Mock 下能走「计算题 → calculator → 答案」，pytest 全绿。

---

## 6. 变更记录（V2 起）

| 日期 | 说明 |
| --- | --- |
| 2026-08-15 | 建立 V2 文档集；确认基线与 R0 为下一步 |
| 2026-07-31 | （历史）M0 工程基础、M1 分层与 User、Agent CRUD 与自研 Runtime 已在代码中 |
| 2026-07-30 | （历史）Docker / Postgres / Redis / Qdrant 就绪 |
