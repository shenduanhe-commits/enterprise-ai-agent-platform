# 数据设计 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/数据库设计文档 V1.0.md` |

三套存储：**PostgreSQL** 业务与审计，**Redis** 缓存/限流/可选 checkpoint，**Qdrant** 检索。表名单数（已从 users 迁到 `user`）。

---

## 1. 已落地表

### user

| 列 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| email | varchar(255) unique | |
| password_hash | varchar(255) | R0 起必须由服务端哈希写入 |
| created_at | timestamptz | |

关系：一个 user 有多个 agent、多个 conversation。

V1 的 username/department/status 未建。R1 不必补部门；R6 若做 RBAC 再加 `role` 或用户上的 `role` 字段。

### agent

| 列 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| name | varchar(100) | |
| provider | varchar(100) | qwen / openai / anthropic / mock |
| description | text null | |
| model_name | varchar(100) | |
| system_prompt | text | |
| created_by | FK user.id | |
| status | varchar(50) | active / disabled / archived |
| created_at | timestamptz | |

### prompt

| 列 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| agent_id | FK agent.id | |
| name | varchar(100) | |
| template | text | |
| version | int | 默认 1 |
| created_at | timestamptz | |

`PromptManager` 取某 Agent 最新一条；没有则用 `agent.system_prompt`。

### conversation

| 列 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| name | varchar(255) | 现用首条用户消息 |
| user_id | FK user.id | |
| agent_id | FK agent.id | |
| created_at / updated_at | timestamptz | |

### conversation_message

| 列 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| conversation_id | FK conversation.id ON DELETE CASCADE | |
| role | varchar(20) | user / assistant / system / tool |
| content | text | |
| created_at | timestamptz | |

给人看的历史。不含图里的 tool 中间态。

### run_span

| 列 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| conversation_id | FK conversation.id ON DELETE CASCADE | |
| node | varchar(50) | `call_model` / `execute_tools` |
| started_at | timestamptz | |
| duration_ms | int | |
| tool_name | varchar(100) null | `call_model` 为空 |
| status | varchar(20) | ok / error |
| error | text null | |

一次图节点执行。不存完整 prompt。`GET /api/v1/runs/{id}/spans`。HITL 暂停时往往只有已跑完的 `call_model`。

---

## 2. 计划中的表（未建）

按阶段加，一次只加当前阶段需要的。

### R1

- 不强制新表。JWT 不落库也可；若要登出黑名单再用 Redis。

### R2

- LangGraph checkpointer 自带表（`lifespan` 里 `setup()`）。
- 自建轨迹：`run_span`（已落地，见上）。

### R3

**knowledge_document**

- id、owner_user_id、title、source_uri、status（pending/ready/failed）、error、created_at

**knowledge_chunk**（可选，元数据也在 Qdrant payload）

- id、document_id、ordinal、text、token_count

Qdrant collection 建议：`eaap_chunks`，向量 + payload：`document_id`、`user_id`、`agent_id`、`text`、`source`。

### R4

**tool**（注册表）：name、description、schema、source（builtin/mcp）、mcp_url、requires_hitl、enabled

**agent_tool**：agent_id、tool_id

### R6

**audit_log**：actor_user_id、action、resource、payload、created_at

用户 `role`：`member` / `admin`

**usage_event**：user_id、agent_id、tokens_in/out、provider、created_at

V1 的完整 permission / role / department / task 表不一次建齐。

---

## 3. Redis

现状：Compose 有，业务未用。

用途优先级：刷新令牌黑名单或限流 → LangGraph checkpointer（若选 Redis）→ 缓存检索结果（有评测后再加）。

---

## 4. Qdrant

现状：健康检查通过，无业务 collection。

R3 要求：dense + sparse 混合；payload 过滤 user/agent；删除文档时同步删点。

---

## 5. 迁移

工具：Alembic。已有版本包括 user、agent、prompt、conversation、conversation_message、run_span、表名单数。

约定：模型改动必须有迁移；不在生产手改表。

---

## 6. 访问规则

- 所有业务查询带 `user_id`（R1 起从 JWT 来，不再信请求体里的 `user_id`）。
- Repository 不跨层做鉴权，Service 做。
- 级联：删 conversation 删 messages；删 agent 对 conversation 的策略保持限制删除或级联，需在实现时选一种并写进迁移。
