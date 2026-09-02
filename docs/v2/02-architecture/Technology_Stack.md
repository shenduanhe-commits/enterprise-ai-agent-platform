# 技术栈 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 评审基准 | 2026-08 |
| 替代 | `docs/02-architecture/Technology_Stack.md`（V1） |

每个 R 阶段 Day 1 按第 5 节重评。官方弃用则改本文，不改代码假装没看见。

---

## 1. 选型原则

1. 官方当前推荐，不看过时教程。
2. 先协议后框架。
3. 企业可控（状态、权限、轨迹）优先于「全自动」。
4. 已在仓库里且仍现代的技术不换（Vue、FastAPI、uv、Qdrant）。
5. 前端不作为学习选型场。

---

## 2. 总表

| 领域 | 采用 | 状态 |
| --- | --- | --- |
| 前端演示壳 | Vue 3.5 + TypeScript + Vite 8 + Pinia + Vue Router + Tailwind 4 | 已有脚手架 |
| 包管理 JS | pnpm | 已有 |
| 后端 | Python 3.12 + FastAPI + Uvicorn | 已有 |
| 包管理 Py | uv | 已有 |
| ORM / 迁移 | SQLAlchemy 2 async + Alembic + asyncpg | 已有 |
| 校验 | Pydantic v2 + pydantic-settings | 已有 |
| 业务库 | PostgreSQL 16 | 已有 |
| 缓存 | Redis 7 | 已部署，待用 |
| 向量 | Qdrant dense + sparse；特征 rerank 或 cross-encoder API | 混合检索 + rerank 已接 |
| Agent 编排 | LangGraph v1 StateGraph + Checkpointer | R2 |
| 简单工厂 | `langchain.agents.create_agent`（可选薄封装） | R2 |
| LLM | Gateway：Qwen 兼容接口 / OpenAI Responses / Anthropic 官方 SDK | 部分已有 |
| 工具协议 | MCP Client + 自建 Server | R4 |
| 多 Agent 协议 | A2A（或当时官方仍推的等价协议） | R5 |
| 流式 | SSE | R1 |
| 认证 | JWT + refresh + Argon2 | R1 |
| 可观测 | Langfuse + OpenTelemetry | R2/R6 |
| 测试 | pytest + pytest-asyncio；ruff | 已有 |
| 容器 | Docker Compose | 已有 |

---

## 3. 雷达

### Adopt

LangGraph StateGraph、MCP、Qdrant 混合检索、SSE、JWT+Argon2、OpenAI **Responses API**（新 OpenAI 能力）、Langfuse、结构化输出。

### Trial（不绑死全站）

- Open Responses：Gateway 预留。
- PydanticAI：一次结构化单 Agent 对照。
- OpenAI Agents SDK：理解 handoff/guardrail，不当事主 Runtime。

### Hold

完整 IAM、K8s、训模、Marketplace、前端补课、MinIO（R3 先本地文件）。

### Avoid

| 避免 | 原因 |
| --- | --- |
| LangChain `AgentExecutor` / `initialize_agent` | 维护模式，EOL ~2026-12 |
| `create_react_agent` | 已被 `create_agent` 取代 |
| OpenAI Assistants API | 迁 Responses，限期约 2026-08-26 |
| ConversationBufferMemory 等旧 Memory | 状态必须显式 |
| AutoGPT / BabyAGI 失控自治 | 企业要图 |
| CrewAI 作主 Runtime | 演示向 |
| Naive RAG 当最终方案 | 面试会追问 hybrid/rerank/eval |
| 同步阻塞调 LLM | 与 async 栈相反 |
| 客户端提交 `password_hash` | 不安全 |
| 把前端当学习主线 | 与转 Agent 目标冲突 |

现有 `app.ai.runtime.agent_executor.AgentExecutor` **不是** LangChain 那个类，保留作对照。

---

## 4. LLM Provider 策略

```
Runtime → LLM Gateway（messages / tools / stream / structured）
            ├─ Qwen：OpenAI-compatible Chat Completions（直到 Responses 稳定）
            ├─ OpenAI：新能力走 Responses
            └─ Anthropic：官方当前 SDK
```

Gateway 必须补齐 tool_calls、streaming、structured output。不要为每个模型复制业务逻辑。

---

## 5. 阶段开工评审（强制）

半天内回答：

1. 本阶段 API/框架官方是否仍推荐？
2. 有没有新协议能替换自研接口？
3. 最近 Agent Engineer JD 有无新必会词？
4. 若弃用：本阶段迁还是记入下一阶段？

结论写进 `docs/v2/00-master/STATUS.md` 或该阶段短笔记（只写 V2）。

---

## 6. 为何留下这些选择（摘要）

- **FastAPI**：async、OpenAPI、与 Python AI 生态一致。见 ADR-001。
- **LangGraph**：循环、HITL、checkpoint 是企业 Agent 的主场。见 ADR-002。
- **uv / pnpm**：已落地且仍是当前推荐包管理。见 ADR-003。
- **Vue 留下但不学**：已有且你会，换 React 零收益。见 ADR-005。
- **Qdrant**：已在 Compose 里，支持混合检索，不必换 pgvector（可用作对照实验，不替换）。
