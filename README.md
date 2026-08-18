# Enterprise AI Agent Platform (EAAP)

企业级 AI Agent 平台。目标不是做一个聊天机器人，而是可创建、运行、治理 Agent 的应用基础设施。

当前也是一条学习路径：从前端转到 **Agent 开发工程师**。学习重点在后端和 Agent Runtime；前端只做演示壳。

---

## 现在能做什么

- 创建用户（密码在服务端 Argon2 哈希）；`POST /api/v1/auth/register` 或 `/users`
- 登录拿 JWT（access + refresh），Agent / Chat / 会话按用户隔离
- 创建 Agent，用 **Qwen**、**OpenAI**、**Anthropic** 或 **Mock** 对话
- Mock 下「12\*7+5」会走 calculator 工具循环
- `POST /api/v1/agents/{id}/chat/stream` 推 SSE；可 `GET /conversations` 拉历史
- pytest：runtime / provider / auth / prompt / sse

还没有：前端演示页、知识库 / RAG、LangGraph。下一步按 [STATUS.md](docs/v2/00-master/STATUS.md) 收口 R1 演示。

进度与计划以文档为准，不要看 `docs/` 下的 V1 文件。

---

## 文档

**只读 V2：** [docs/v2/README.md](docs/v2/README.md)

| 想了解 | 打开 |
| --- | --- |
| 做到哪、下一步 | [docs/v2/00-master/STATUS.md](docs/v2/00-master/STATUS.md) |
| 阶段 R0–R6 | [docs/v2/00-master/Project_Master_Plan.md](docs/v2/00-master/Project_Master_Plan.md) |
| 怎么把环境跑起来 | [docs/v2/03-development/Environment.md](docs/v2/03-development/Environment.md) |
| Git 怎么用 | [docs/v2/03-development/GitWorkflow.md](docs/v2/03-development/GitWorkflow.md) |

---

## 技术栈

| 层 | 选择 |
| --- | --- |
| 前端（演示壳） | Vue 3 + TypeScript + Vite |
| 后端 | Python 3.12 + FastAPI + uv |
| 数据 | PostgreSQL 16、Redis 7、Qdrant |
| Agent | 自研 `AgentExecutor`（R2 再上 LangGraph） |
| LLM | Gateway：Qwen / OpenAI / Anthropic / Mock |

---

## 本地启动

需要：Git、Python 3.12、uv、Docker Desktop。前端演示壳另需 Node.js + pnpm。

```bash
cp .env.example .env
# 用 Qwen 时填写 QWEN_API_KEY、QWEN_BASE_URL；只用 Mock 可以不填

docker compose up -d

cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API：http://localhost:8000
- Swagger：http://localhost:8000/docs

Swagger 可走：`POST /api/v1/auth/register` → `POST /api/v1/auth/login`（Authorize 填 access）→ `POST /api/v1/agents`（`provider` 填 `mock` 或 `qwen`）→ `POST /api/v1/agents/{id}/chat` 或 `/chat/stream`。

不连数据库的单测：

```bash
cd apps/api
uv run pytest tests/test_agent_runtime.py tests/test_agent_service.py tests/test_agent_schema.py tests/test_sse.py tests/test_prompt_manager.py tests/test_providers.py tests/test_user_service.py -q
```

`tests/` 里还有连库手写脚本，已用 `if __name__ == "__main__"` 保护；全量 pytest 不会执行它们。

---

## 仓库结构

```text
apps/api     FastAPI + Agent Runtime
apps/web     Vue 演示壳（尚未接业务）
docs/v2      现行文档
```

Git：GitHub Flow。`main` 为可演示稳定点；功能分支如 `feature/r0-runtime-hardening`、`feature/r1-auth-sse`。
