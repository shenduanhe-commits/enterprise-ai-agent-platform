# 部署 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/04-deployment/Deployment.md`、`Operations.md` 的现行部分 |

---

## 1. 当前（本地）

```bash
docker compose up -d          # postgres, redis, qdrant
cd apps/api && uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
# 可选：pnpm --filter apps-web dev
```

这是 R0–R5 的默认运行方式。不要求 Kubernetes。

---

## 2. 目标（R6）

- 一份 README：15 分钟从 clone 到 Swagger 走通 Chat。
- Compose 覆盖全部依赖（含 Langfuse 可选 profile）。
- API 与 web 可各打一个镜像，但仍是单机 Compose 演示，不是集群作业。

K8s / 多副本 / 灾备：选修，不进主路径。

---

## 3. 运维底线

- 健康检查：已有 compose healthcheck + `/api/v1/health`。
- 数据卷：`postgres_data`、`qdrant_data` 已持久化。
- 密钥只在环境变量。
- 日志先走 stdout；R6 再接 OTel。

V1 Operations 里的值班、SLA、多环境晋升：单人作品集阶段不建流程。
