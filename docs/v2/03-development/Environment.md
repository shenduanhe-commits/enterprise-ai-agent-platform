# 开发环境 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/03-development/Environment.md`、`DEVELOPMENT.md`、`EAAP_DOCKER-USE.md`、`EAAP_PNPM-UV-USE.md`、`EAAP_DATABASE_USE.md` 中的现行说明 |

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
# 按需填 QWEN_API_KEY / QWEN_BASE_URL 或 OPENAI_API_KEY

# 2. 基础设施
docker compose up -d

# 3. 后端
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 前端（可选，R0 不需要）
# 仓库根目录
pnpm install
pnpm --filter apps-web dev
```

- API：http://localhost:8000 与 http://localhost:8000/docs
- Web：http://localhost:5173
- 本机演示账号（仅开发库）：`user@eaap.com` / `user`。登录字段是 email。R1 走一遍见 [JWT.md](JWT.md) 第 12 节。
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

已有：`POSTGRES_*`、`DATABASE_URL`、`REDIS_*`、`QDRANT_*`、`API_PORT`、`WEB_PORT`、`VITE_API_URL`、`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、以及代码中的 `QWEN_API_KEY` / `QWEN_BASE_URL`。

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
