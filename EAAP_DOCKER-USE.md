# Docker 使用总结（结合 EAAP）

你们现在用 Docker 主要跑三个基础服务：**Postgres、Redis、Qdrant**，配置在 `docker-compose.yml`，变量在 `.env`。

---

## 一、核心概念

| 概念 | 含义 |
|--|--|
| Image（镜像） | 只读模板，如 `postgres:16`、`redis:7` |
| Container（容器） | 镜像跑起来的实例 |
| Compose | 用一个 YAML 一次管理多个容器 |
| Volume（卷） | 持久化数据，删容器数据还在 |
| Network（网络） | 容器互通；同网络可用服务名访问 |
| Port mapping | `主机端口:容器端口`，让本机访问容器 |
| Healthcheck | 定期探测服务是否健康 |

---

## 二、你们项目里有什么

```text
postgres  → 关系库，端口 POSTGRES_PORT→5432，数据卷 postgres_data
redis     → 缓存，端口 REDIS_PORT→6379
qdrant    → 向量库，端口 QDRANT_PORT→6333，数据卷 qdrant_data
网络      → eaap-network（三者互通）
```

端口示例：`"5432:5432"` = 本机 `localhost:5432` → 容器内 `5432`。

---

## 三、常用命令

在仓库根目录执行：

```powershell
# 启动（后台）
docker compose up -d

# 查看状态
docker compose ps

# 看日志
docker compose logs -f
docker compose logs -f postgres

# 停止（保留数据）
docker compose stop

# 停止并删除容器（卷默认还在）
docker compose down

# 进容器
docker compose exec postgres psql -U eaap
docker compose exec redis redis-cli
docker compose exec redis sh

# 只重建某个服务
docker compose up -d --force-recreate qdrant
```

`.env` 改端口/密码后，通常要 `up -d` 或 recreate 才生效。

---

## 四、容器内 vs 宿主机访问

| 从哪访问 | 怎么写 |
|--|--|
| 本机 PowerShell / 浏览器 | `localhost:5432`、`localhost:6379`、`localhost:6333` |
| 另一个 Compose 容器内 | 服务名：`postgres`、`redis`、`qdrant` |

例如在 Redis 容器测 DNS：

```powershell
docker compose exec redis sh -c "getent hosts postgres"
```

容器镜像往往没有 `ping`，解析通不等于装了 ping。

---

## 五、你踩过的坑（记住即可）

1. **`.env` 端口没配** → 出现 `variable is not set`，主机端口可能被随机分配（如 `50334`）
2. **健康检查用了镜像没有的命令** → Qdrant 曾因没有 `curl` 显示 `unhealthy`（服务可能仍在跑）
3. **`health: starting`** → 还在探测；多次失败后变 `unhealthy`
4. **PowerShell 的 `curl`** → 实际是 `Invoke-WebRequest`，调 Qdrant 应用 `curl.exe` 或 `Invoke-RestMethod`
5. **psql 提示符 `eaap-#`** → 上一条 SQL 没结束；误输入可用 `\r` 取消

---

## 六、数据会丢吗

- `docker compose stop` / 关电脑：数据一般还在（有 volume）
- `docker compose down`：容器删了，**命名卷默认还在**
- `docker compose down -v`：连卷一起删，**数据清空**

Postgres / Qdrant 配了 volume；Redis 你们没挂卷，重启后内存数据会丢（开发阶段通常可接受）。

---

## 七、和开发的关系

```text
Docker Compose          本机开发进程
─────────────          ────────────
Postgres / Redis /     pnpm（前端）
Qdrant（基础设施）      uv（后端 API）
```

基础设施用 Docker；应用代码仍在本机用 `pnpm` / `uv` 跑，通过 `localhost` + `.env` 里的端口连这些服务。

---

## 八、最小日常清单

```powershell
# 第一次 / 日常启动
copy .env.example .env   # 若还没有 .env
docker compose up -d
docker compose ps        # 确认 healthy

# 连库试试
docker compose exec postgres psql -U eaap -d eaap

# 收工
docker compose stop
```

**一句话：** Docker Compose 把 Postgres、Redis、Qdrant 打包成可一键启停的本地基础设施；本机用端口访问，容器之间用服务名访问，重要数据靠 volume 持久化。
