# EAAP 学习路线 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 读者 | 前端开发人员 → Agent 开发工程师 |
| 替代 | `docs/00-master/LEARNING_ROADMAP.md`（V1） |

---

## 1. 学习哲学

```
读当天的官方文档 → 在 EAAP 里做最小增量 → 写 10 行决策 → 补测试或黄金用例 → 用面试口吻讲一遍
```

不单独「先学完再做」。V1 里的前端补课（Composition API、企业 UI、Playwright）作废。

时间分配：

```
后端工程 + 认证           ~25%
Agent Runtime / Tool / MCP ~40%
RAG / Eval / Observability ~25%
前端演示壳                 ~10%
```

---

## 2. 与阶段对应

| 阶段 | 你要变成谁 | 必须能讲清 |
| --- | --- | --- |
| R0 | 能讲自己写的 Agent loop | Gateway、tool_calls、max iterations |
| R1 | 全栈 AI 应用里的后端那一半 | JWT、资源隔离、SSE |
| R2 | Agent Engineer 雏形 | StateGraph、checkpoint、HITL |
| R3 | 带 RAG 的 Agent Engineer | hybrid、rerank、citation、eval |
| R4 | 会接企业工具的人 | MCP Client/Server、工具权限 |
| R5 | 会做协作的人 | Supervisor、A2A、何时不该多 Agent |
| R6 | 能交生产仓库的人 | Trace、护栏、成本、作品包 |

---

## 3. 分阶段知识

### R0 基线

- Python async、Pydantic、现有分层（API → Service → Repository）。
- LLM tool calling 协议：`tool_calls` / `tool` role / JSON Schema。
- 密码必须服务端哈希（Argon2），为什么不能收 `password_hash`。
- 工具链：[01-PNPM-UV.md](../05-notes/01-PNPM-UV.md)、[02-Docker.md](../05-notes/02-Docker.md)、[03-Database.md](../05-notes/03-Database.md)。
- 一次请求怎么走：[04-Request_Handle.md](../05-notes/04-Request_Handle.md)。

笔记按阶段编号，集中在 [05-notes/](../05-notes/)。

### R1 后端产品面

- JWT access + refresh；依赖注入拿当前用户（见 [08-JWT.md](../05-notes/08-JWT.md)）。
- HTTPS 与抓包：路径在 TLS 内，SNI/IP 对旁路可见（见 [09-HTTPS.md](../05-notes/09-HTTPS.md)）。
- CORS / 预检只约束浏览器，不是 JWT 门禁（见 [10-CORS.md](../05-notes/10-CORS.md)）。
- FastAPI `StreamingResponse`、SSE 事件格式、客户端断开。
- 请求 `Content-Type`、Response 种类、异常如何变成 JSON（见 [14-R1_FastAPI_ContentType_Response.md](../05-notes/14-R1_FastAPI_ContentType_Response.md)）。
- 统一错误体（见 [Request_Handle.md](../03-development/Request_Handle.md)）。

前端：用已有 Vue 能力接 3 个薄页面，不学新框架。

### R2 Runtime

学习笔记：[11-R2_Langgraph_Runtime.md](../05-notes/11-R2_Langgraph_Runtime.md)。一次执行逐步数据：[12-R2_Langgraph_Runtime_Flow.md](../05-notes/12-R2_Langgraph_Runtime_Flow.md)。Checkpoint 快照字段：[13-R2_Langgraph_Snapshot.md](../05-notes/13-R2_Langgraph_Snapshot.md)。

- LangGraph v1：手写 `StateGraph`（`call_model` / `execute_tools`），条件边，TypedDict 状态。
- Checkpointer（Postgres，失败则内存）与对话 Memory、`run_span` 的区别。
- `interrupt` / resume：节点会重跑；resume 列表按下标对齐。
- 节点轨迹：表 + `GET /runs/{id}/spans`。Langfuse 留 R6。
- Chat 不启用 Structured output；最终答案只在 `content`。
- **不要**学已弃用的 LangChain `AgentExecutor` / `create_react_agent`（本仓库自己的 `ai.runtime.agent_executor.AgentExecutor` 是接线层，要看）。

对照：把自研 loop 和 Graph 画在一张纸上，能指出每一步对应关系。

### R3 RAG

- 解析 → chunk → embedding → upsert。
- Qdrant 混合检索 + rerank（特征或 cross-encoder）。
- 上下文 token 预算；citation。
- 离线黄金集：recall@k、引用正确率、检索幻觉。
- RAG 失败 vs 模型编造，如何用 eval 分开。

### R4 MCP

- MCP 是工具协议，不是又一个 Agent 框架。
- Server 暴露 tools；Client（Runtime）发现并调用。
- 超时、鉴权、降级。
- 进程内工具与 MCP 工具并存。

### R5 Multi-Agent

- Supervisor vs 单 Agent 何时够用。
- 子图 / handoff；任务级状态。
- A2A：跨进程消息，不是 Python 函数互调冒充。

### R6 生产与求职

- Langfuse trace 怎么对应一次 Chat。
- 基础护栏：注入、PII、工具白名单。
- Token 成本。
- 3–5 分钟演示脚本；一页设计决策。

---

## 4. R3 之后必须能口头回答

1. Agent 和 Chatbot 差在哪？状态存在哪里？
2. 工具失败、模型死循环，系统怎么停？
3. 为什么不用 LangChain 旧 AgentExecutor？
4. RAG 答错时，如何区分检索错了还是模型编了？
5. 为什么工具走 MCP，而不是在 Agent 里写死 HTTP？
6. 多 Agent 什么时候不该用？
7. 一次请求成本怎么算？如何降？

---

## 5. 不学清单

- Vue 组件库、设计系统、Playwright 作为学习目标。
- 训模 / 微调。
- Kubernetes 运维课（R6 前）。
- 同时精通三套 Runtime（LangGraph + PydanticAI + OpenAI Agents SDK）。后两者最多做一次对照实验。
- 旧教程里的 ConversationBufferMemory、Assistants API、initialize_agent。

---

## 6. 推荐阅读节奏

每个阶段 Day 1 只读：

- 本阶段将用到的**官方文档当前页**（LangGraph / MCP / Qdrant / FastAPI / 模型厂商）；
- 本目录对应架构文档；
- 最近几条 Agent Engineer JD，核对关键词有没有变。

读完立刻写代码，不要做读书笔记长文。
