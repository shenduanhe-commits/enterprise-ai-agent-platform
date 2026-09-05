# 开发环境 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/03-development/Environment.md`、`DEVELOPMENT.md`；学习笔记见 [01-PNPM-UV.md](../05-notes/01-PNPM-UV.md)、[02-Docker.md](../05-notes/02-Docker.md)、[03-Database.md](../05-notes/03-Database.md) |

---

## 1. 需要安装

| 工具 | 用途 |
| --- | --- |
| Git | 版本管理 |
| Node.js 22 或 24（见 `apps/web/package.json` engines） | 前端演示壳 |
| pnpm | JS 包管理 |
| Python 3.12 | 后端 |
| uv | Python 包与运行 |
| Docker Desktop | Postgres / Redis / Qdrant |

OS：Windows 10/11 即可（当前开发机）。不必为学习再上 WSL。

---

## 2. 仓库结构

```text
enterprise-ai-agent-platform
├── apps/api          # FastAPI
├── apps/web          # Vue 演示壳
├── docker-compose.yml
├── .env.example
└── docs/v2
```

---

## 3. 第一次启动

```bash
# 1. 环境变量
cp .env.example .env
# 按需填 QWEN_API_KEY / QWEN_BASE_URL 或 OPENAI_API_KEY（聊天）
# 知识库向量另填 EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL
# Cross-encoder rerank 另填 RERANK_API_KEY / RERANK_BASE_URL / RERANK_MODEL（不配则本地特征 rerank）
# R4 MCP：改 apps/api/app/ai/mcp/servers.py（MCP_ENABLED / MCP_TIMEOUT / 三类 Server list）

# 2. 基础设施
docker compose up -d

# 3. 后端
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3b. 选修：跨进程 Writer（另一终端；不要把 URL 写进长期 .env）
# pnpm dev:api-writer
# 然后本终端：
# Windows PowerShell:
#   $env:A2A_WRITER_URL="http://127.0.0.1:8001/api/v1/a2a/message"
#   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Chat 打「写一页简报」时，8000 的 Supervisor 寄信，8001 的 Writer 回信。

# 4. 前端（可选，R0 不需要）
# 仓库根目录
pnpm install
pnpm --filter apps-web dev
```

- API：http://localhost:8000 与 http://localhost:8000/docs
- Web：http://localhost:5173
- 本机演示账号（仅开发库）：`user@eaap.com` / `user`。登录字段是 email。R1 走一遍见 [08-JWT.md](../05-notes/08-JWT.md) 第 12 节。
- Postgres：`localhost:${POSTGRES_PORT}`
- Redis：`localhost:${REDIS_PORT}`
- Qdrant：http://localhost:6333

`DATABASE_URL` 在 `.env`。SQLAlchemy 异步 URL 若与同步 Alembic 不一致，以 `apps/api` 现有 `alembic/env.py` 与 `core/database.py` 为准。

---

## 4. 常用命令

```bash
# 后端测试
cd apps/api && uv run pytest

# 后端 lint
cd apps/api && uv run ruff check .

# 迁移
cd apps/api && uv run alembic revision --autogenerate -m "reason"
cd apps/api && uv run alembic upgrade head

# 基础设施
docker compose ps
docker compose logs -f postgres
docker compose down
```

---

## 5. 环境变量（根 `.env`）

已有：`POSTGRES_*`、`DATABASE_URL`、`REDIS_*`、`QDRANT_*`、`API_PORT`、`WEB_PORT`、`VITE_API_URL`、`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`QWEN_API_KEY` / `QWEN_BASE_URL`。知识库 embedding 单独配：`EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL`、`EMBEDDING_MODEL`、`EMBEDDING_DIM`、`EMBEDDING_BATCH`（默认 16）。知识摘录上限：`KNOWLEDGE_CONTEXT_TOKENS`（默认 1024）。Cross-encoder rerank 单独配：`RERANK_API_KEY`、`RERANK_BASE_URL`、`RERANK_MODEL`（三者都有才启用）。百炼 `qwen3.7-text-rerank` 的 URL 必须是 `.../api/v1/services/rerank/text-rerank/text-rerank`，不要抄 embedding 的 `compatible-mode/v1`。不配 embedding Key 或模型则本地 hash；不配 rerank 则本地特征 rerank。R4 MCP：开关、超时和 Server 名单都在 `apps/api/app/ai/mcp/servers.py`（`MCP_ENABLED`、`MCP_TIMEOUT`；http / stdio / inprocess 三类 list，每条带 `kind`，启动时合并后连 Client）。HTTP 条目可加 `headers`（如 `Authorization`），每台 Server 自己写，不要共用一把全局钥匙。默认只有进程内模拟订单。一个 Server 挂了不影响其它。R5 A2A：`A2A_WRITER_URL` 空则 Writer 进程内；填 `http://host:port/api/v1/a2a/message` 则 Supervisor 用 HTTP 信封调用（`A2A_INTERNAL_KEY` / 头 `X-EAAP-A2A-Key`）。

R1 将加：`JWT_SECRET`、`JWT_EXPIRE_MINUTES`。不要把真实 Key 提交进 Git。

---

## 6. 依赖管理

- Python：只通过 `uv add` / `uv add --dev` 改 `apps/api/pyproject.toml`，提交 `uv.lock`。
- JS：pnpm，提交 lockfile。不要用 pip / npm 往本仓库装包。

---

## 7. 验证基础设施（V1 已做过，新机器再做一次）

- Postgres：能连、能 CRUD、compose down 后数据还在。
- Redis：PING、SET/GET、TTL。
- Qdrant：建 collection、插入向量、相似度检索。
