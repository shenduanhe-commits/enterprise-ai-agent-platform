# Enterprise AI Agent Platform (EAAP)

企业级 AI Agent 平台。目标不是做一个聊天机器人，而是可创建、运行、治理 Agent 的应用基础设施。

当前也是一条学习路径：从前端转到 **Agent 开发工程师**。学习重点在后端和 Agent Runtime；前端只做演示壳。

---

## 现在能做什么

- 创建用户（密码在服务端 Argon2 哈希）
- 创建 Agent，用 **Qwen** 或 **Mock** 对话
- Mock 下「12\*7+5」会走 calculator 工具循环
- `run_loop` 有 pytest：无工具 / 有工具 / 超轮次

还没有：登录 JWT、资源隔离、SSE 流式、知识库 / RAG。下一步是 **R1**。

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
| LLM | Gateway：Qwen（可用）、Mock（测试）；OpenAI / Anthropic 未对齐 |

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

Swagger 可走：`POST /api/v1/users` → `POST /api/v1/agents`（`provider` 填 `mock` 或 `qwen`）→ `POST /api/v1/agents/{id}/chat`。

工具循环单测（不连数据库）：

```bash
cd apps/api
uv run pytest tests/test_agent_runtime.py -q
```

暂不要跑整个 `tests/`，里面还有会连库的手工脚本。

---

## 仓库结构

```text
apps/api     FastAPI + Agent Runtime
apps/web     Vue 演示壳（尚未接业务）
docs/v2      现行文档
```

Git：GitHub Flow。`main` 为可演示稳定点；功能分支如 `feature/r0-runtime-hardening`、`feature/r1-auth-sse`。
