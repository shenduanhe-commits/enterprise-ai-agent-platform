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

### knowledge_document

| 列 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| owner_user_id | FK user.id | JWT 用户，列表按此隔离 |
| agent_id | FK agent.id | 必须是该用户的 Agent |
| title | varchar(255) | 默认用文件名（不含扩展名） |
| source_uri | varchar(500) | 相对 `apps/api/data/knowledge/` 的路径 |
| status | varchar(20) | `pending` / `ready` / `failed`；插入为 `pending`，切块入库后为 `ready` 或 `failed` |
| error | text null | 入库失败原因 |
| created_at | timestamptz | |

R3：上传 `.md` / `.pdf` / `.docx` 后同步切块并写入 Qdrant；接口返回最终 `ready` / `failed`。扫描件无文字会 `failed`。Chat 检索已接（见第 4 节）。

---

## 2. 计划中的表（未建）

按阶段加，一次只加当前阶段需要的。

### R1

- 不强制新表。JWT 不落库也可；若要登出黑名单再用 Redis。

### R2

- LangGraph checkpointer 自带表（`lifespan` 里 `setup()`）。
- 自建轨迹：`run_span`（已落地，见上）。

### R3

**knowledge_document** 已落地（见上）。切块不进 Postgres；向量在 Qdrant `eaap_chunks`。

### R4

**tool**（已落地）：name、description、schema（JSONB；接口输出为 `input_schema`）、source（builtin/mcp）、mcp_url（当前多为空）、requires_hitl、enabled。启动 upsert；缺席的 MCP 名只 `enabled=false`。

**agent_tool**（已落地）：agent_id、tool_id；空绑定 = 该 Agent 无工具。

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

Collection：`eaap_chunks`。named dense cosine（`dense`，维数 hash 64 或 `EMBEDDING_DIM`）+ named sparse（`sparse`，词面哈希 + IDF）。维数或 schema 对不上会重建 collection，启动时按磁盘原文件重新切块嵌入，不必让用户再传一遍。

Payload：`document_id`、`user_id`、`agent_id`、`ordinal`、`text`、`source`。Point id = uuid5(`document_id:ordinal`)。

Chat 检索：dense 与 sparse 各查一条，RRF 融合；filter 仍是 `user_id`/`agent_id`。准入后 rerank（配了 `RERANK_MODEL` / `RERANK_API_KEY` / `RERANK_BASE_URL` 则 cross-encoder，否则或调用失败则特征 rerank），取前 4 条，再按 `KNOWLEDGE_CONTEXT_TOKENS` 装入 Prompt。删除文档时按 `document_id` + `user_id` 删点。检索黄金集见 `apps/api/evals/`。

---

## 5. 迁移

工具：Alembic。已有版本包括 user、agent、prompt、conversation、conversation_message、run_span、knowledge_document、表名单数。

约定：模型改动必须有迁移；不在生产手改表。

---

## 6. 访问规则

- 所有业务查询带 `user_id`（R1 起从 JWT 来，不再信请求体里的 `user_id`）。
- Repository 不跨层做鉴权，Service 做。
- 级联：删 conversation 删 messages；删 agent 对 conversation 的策略保持限制删除或级联，需在实现时选一种并写进迁移。
