# 系统架构 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/02-architecture/System_Architecture.md`、`docs/系统架构设计文档 V1.0.md` |

---

## 1. 原则

- **模块化单体**：一个 FastAPI 进程，按目录分模块。R6 前不拆微服务。
- **可扩展**：新模型进 Gateway；新工具进注册表/MCP；新 Agent 是数据不是新服务。
- **安全默认**：无 JWT 不进业务 API（R1 起）；工具默认拒绝未授权。
- **AI 原生**：业务流围绕 Runtime，而不是先造一堆 CRUD 再挂模型。
- **前端是壳**：`apps/web` 不承载业务规则。

---

## 2. 逻辑分层

```
┌─────────────────────────────────────┐
│  Demo Shell (Vue) / Swagger / curl  │
└──────────────────┬──────────────────┘
                   │ REST + SSE
┌──────────────────▼──────────────────┐
│  Application  API / Service / Auth  │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│  AI Layer                           │
│  Gateway · Runtime · Prompt · Memory│
│  Tools/MCP · RAG · Eval             │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│  Data  PostgreSQL · Redis · Qdrant  │
└─────────────────────────────────────┘
```

V1 的 Workflow Application 不作为独立层，复杂流程用 LangGraph 表达。

---

## 3. 仓库结构（已落地 + 将长出）

```text
enterprise-ai-agent-platform
├── apps
│   ├── api/app
│   │   ├── api/v1/            # auth, users, agents, knowledge, runs
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── handlers/
│   │   ├── core/              # config, database, exceptions, security
│   │   └── ai/
│   │       ├── llm/           # Gateway + providers
│   │       ├── runtime/       # agent_executor.py + StateGraph
│   │       ├── tools/         # calculator / send_email
│   │       ├── mcp/           # servers.py + Client；本地 Server 在 local_mcp_server/
│   │       ├── memory/
│   │       ├── prompts/
│   │       └── knowledge/     # 解析 / 切块 / 检索 / rerank / eval
│   └── web/                   # 演示壳
├── docker-compose.yml
└── docs/v2/                   # 现行文档
```

请求路径：

```
Router → Service → Repository → SQLAlchemy
                ↘ AgentExecutor / Graph → Gateway / Tools / Memory
```

规则：

- Repository 返回数据或 None，不抛业务异常。
- Service 抛 `EAAPException`。
- Router 保持薄，不写业务 try/except。
- `main.py` 注册统一异常处理。

---

## 4. 前端（演示壳）

继续 Vue 3 + TS + Vite + Pinia + Vue Router。页面上限：

- Login
- Agents
- Chat
- Knowledge（R3，一个上传框即可）

不建设计系统，不上 Playwright 学习任务。超过每阶段 1–3 天的前端工作视为范围膨胀。

---

## 5. 后端运行时

- Python 3.12、FastAPI、asyncio、uv。
- 配置：`pydantic-settings` 读根目录 `.env`。
- 生命周期：`lifespan` 里管理引擎/连接。
- 一个 API 进程服务所有模块。

---

## 6. 数据与基础设施

| 组件 | 用途 | 状态 |
| --- | --- | --- |
| PostgreSQL 16 | 用户、Agent、会话、审计、checkpoint | 已部署；业务表部分已有 |
| Redis 7 | 缓存、限流（目标）、可选 checkpoint | 已部署，业务未用 |
| Qdrant | 向量 + 稀疏检索 | 已部署；上传/检索/按文档删除 `eaap_chunks` |
| Docker Compose | 本地依赖 | 已有 |

对象存储 V1 规划了，V2 的 R3 先用本地磁盘或 Postgres 存文件元数据，不先上 MinIO。

---

## 7. 关键运行时路径（目标态）

```
POST /api/v1/agents/{id}/chat
  → 鉴权、加载 Agent 与 Conversation
  → AgentExecutor 拼 messages（含 KnowledgeRetriever）
  → Runtime.execute（StateGraph）
       → LLMGateway.chat / stream（可含 tools）
       → ToolManager 或 MCP
       → interrupt HITL
       → 写回 messages + trace
  → SSE 或 JSON
```

---

## 8. 演进

| 阶段 | 架构变化 |
| --- | --- |
| 现在 | 单体 + JWT + StateGraph + 知识库（Qdrant hybrid） |
| R1 | 同一单体 + Auth 依赖 |
| R2 | 同一单体 + Graph Runtime + checkpointer |
| R3 | 同一单体 + `ai/knowledge` + Qdrant 真正使用 |
| R4 | 同一单体 + 进程内 MCP（stdio / HTTP 可配） |
| R5 | Chat 仍单体；Writer 可 `standalone` 另起进程（A2A HTTP） |
| R6 | 加 telemetry sidecar（Langfuse），不拆业务服务 |

---

## 9. 质量属性如何落地

| 属性 | 做法 |
| --- | --- |
| 可测试 | Service/Runtime 可注入 Gateway/Tool |
| 可替换模型 | Provider 接口统一 |
| 可观测 | R2 记 node；R6 接 OTel/Langfuse |
| 安全 | R1 JWT；R4 Agent 工具绑定；R6 护栏 |
