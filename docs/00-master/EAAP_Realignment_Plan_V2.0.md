> **已并入现行文档集。** 请阅读 [`docs/v2/README.md`](../v2/README.md)。本文不再维护。

# EAAP Realignment Plan V2.1

# 职业目标对齐后的重新规划（前端转 Agent）

| 项目 | 内容 |
| --- | --- |
| 文档名称 | EAAP Realignment Plan |
| 版本 | V2.1 |
| 状态 | Active |
| 创建日期 | 2026-08-15 |
| 适用范围 | 从当前代码基线继续开发 |
| 学习者 | 前端开发人员转 Agent 工程师 |
| 与旧文档关系 | **不替代、不修改** `Project_Master_Plan.md` 等 V1.0 文档；本文件是按现状重排后的执行计划 |

---

## 1. 为什么要重新规划

原计划（`docs/00-master/Project_Master_Plan.md`）按 M0 → M5 线性推进。实际开发已经：

- 跳过了认证、组织、知识库、前端业务页；
- 提前做了自研 Agent Runtime（LLM Gateway、Tool Loop、短期 Memory）；
- 状态文件 `EAAP_STATUS.md` 仍停在 Milestone 0，和代码不一致。

继续按旧 Milestone 编号推进，会出现两件事：

1. 文档说「下一步做 M0.6」，代码其实已经在跑 Chat；
2. 为了「补齐旧清单」去堆组织架构、Marketplace，却缺面试官真正会问的 Runtime / RAG / Eval / MCP。

本计划只服务一个目标：

> 通过一个可演示、可解释、可迭代的企业级 Agent 平台，掌握 2026 年 Agent 开发工程师岗位要求的完整能力，并拿到offer。

产品仍然是 EAAP，但优先级改为：**先形成求职作品，再扩展平台广度。**

---

## 1.1 学习者画像：前端转 Agent，时间压在后端

你已经是前端开发人员。Vue / TypeScript / 工程化 **不是本计划的学习目标**，只是你已经会的交付工具。

时间分配（按学习小时，不是按仓库文件数）：

```
后端工程 + 数据模型 + 认证     约 25%
Agent Runtime / Tool / MCP     约 40%
RAG / Eval / Observability     约 25%
前端演示壳                     约 10%   ← 只接线，不学新概念
```

前端在本项目里的定位是 **演示壳（demo shell）**：

- 要：登录、选 Agent、发消息、看见流式字、点一下 HITL 确认、看见引文。
- 不要：设计系统、组件库选型、复杂状态架构、动画、响应式打磨、前端单测/E2E 作为学习、Pinia 最佳实践课。

日常验收以 **FastAPI `/docs`、curl、pytest** 为准。浏览器页面只为面试录屏服务，能用即可。SSE、鉴权、引用这些概念的学习发生在后端；前端只是把已有 API 接上。

旧 V1.0 里的前端学习路线（Composition API、企业 UI 架构、Playwright 等）对本计划作废。

---

## 2. 职业目标：面试官要看到什么

2026 年 Agent / Agentic 岗位（AI Application Engineer、Agent Engineer、生成AIエンジニア）常见要求不是「调过一次 ChatGPT API」，而是：

| 能力 | 为什么重要 | 作品里必须能指着代码讲 |
| --- | --- | --- |
| 生产级 Python 后端 | FastAPI、async、分层、测试 | 现有 API 层要补齐认证和错误边界 |
| Agent Runtime | 状态、循环、工具、失败恢复，而不是单轮问答 | 从自研 loop 演进到 LangGraph StateGraph |
| Tool / MCP | 工具与框架解耦，企业里工具会独立演进 | 自研 Tool + 至少一个 MCP Server/Client |
| 企业 RAG | 混合检索、重排、引用、评测，而不是「切块 + 向量」 | Qdrant 真正用起来 |
| Streaming | SSE / 增量输出是产品标配 | FastAPI 流式接口；前端只消费 EventSource |
| Observability + Eval | 能证明 Agent 质量，而不只是「感觉能用」 | Trace + 离线评测集 |
| 安全与治理 | 认证、权限、审计、护栏 | JWT + RBAC 基础 + 工具权限 |
| Multi-Agent / A2A | 加分项，复杂任务协作 | Supervisor + 标准协议，而不是硬编码互相调用 |

求职作品的最低合格线（**Swagger / curl 能走通即可**，有薄页面更好）：

```
能登录 → 创建 Agent → 流式对话 → 调用工具 → 基于企业文档回答并给出引用
→ 能打开一次执行 Trace → 能说出失败时系统怎么停、怎么重试
```

加分线：

```
Human-in-the-loop 审批 → MCP 接入外部工具 → 多 Agent 协作 → 有评测报告和成本数字
```

---

## 3. 当前代码基线（以仓库为准）

### 3.1 已经具备

| 层 | 现状 |
| --- | --- |
| 工程 | Monorepo；`apps/web` Vue 3.5 + Vite 8 + Tailwind 4；`apps/api` Python 3.12 + uv + FastAPI |
| 基础设施 | Docker Compose：PostgreSQL 16、Redis 7、Qdrant |
| 后端骨架 | API → Service → Repository → Model；Alembic；统一 `EAAPException` |
| 领域模型 | User、Agent、Prompt、Conversation、ConversationMessage |
| API | `/api/v1/users`、`/api/v1/agents`、`POST /api/v1/agents/{id}/chat` |
| AI | `LLMGateway`（Qwen / OpenAI / Anthropic）；`AgentExecutor` 工具循环（最多 5 轮）；`PromptManager`；短期 Memory（最近 10 条）；内置 calculator |
| 测试 | repository / service / schema / runtime / prompt 等单测已有雏形 |

这是很好的起点：你已经亲手写过 Agent loop，而不是只调框架。面试时这是优势。

### 3.2 明确缺口（相对可落地 / 可面试）

| 缺口 | 影响 |
| --- | --- |
| 无登录、无 JWT、密码由客户端直接传 `password_hash` | 不能当企业系统讲 |
| 前端仍是 Vue 脚手架 | 不影响学习；R1 用最小页面接线即可，Swagger 也能演示 |
| Chat 非流式 | 体验和岗位要求都不够 |
| OpenAI Provider 未解析 `tool_calls`（Qwen 已解析） | 工具循环在 OpenAI 上是断的 |
| Tool schema 参数为空 | 模型不知道怎么调工具 |
| Qdrant 已部署但业务未使用 | RAG 是空的 |
| 无 LangGraph，尽管 ADR-004 已选它 | 和岗位主流技术栈脱节 |
| 无 MCP / A2A / Eval / Trace | 缺 2026 年「生产 Agent」关键词 |
| 组织、Workflow、Marketplace | 旧计划有，但对当前求职目标不是第一优先级 |

### 3.3 和旧 Milestone 的对应关系

| 旧计划 | 实际 | 本计划处理 |
| --- | --- | --- |
| M0 工程基础 | 已完成 | 不再重做，只修阻塞项 |
| M1 用户 / 组织 / 知识库 / 工具管理 | 只做了 User/Agent CRUD | 拆开：认证和 Chat 先做，组织后置 |
| M2 Agent Runtime | 自研 loop 已通，框架级 Runtime 未做 | 作为 R2 的核心，升级而不是推倒 |
| M3–M5 企业能力 / 生产 / 生态 | 未开始 | 按求职价值重排，砍掉早期 Marketplace |

旧文档保留作历史。之后执行只认本文件的 R 阶段编号。

---

## 4. 技术原则：跟踪创新，不用过时方案

### 4.1 选型原则

1. **官方当前推荐优先**：以各厂商 / 框架 2026 年文档和 deprecation 公告为准，不以 2023–2024 教程为准。
2. **先协议、后框架**：LLM 调用、Tool、Agent 通信尽量走开放协议（OpenAI-compatible / Open Responses、MCP、A2A），框架可以换。
3. **自研保留理解，框架承接生产**：现有 `AgentExecutor` 作为对照实现保留；生产路径转到 LangGraph。
4. **每个阶段开始做一次技术雷达评审**（见 4.4），发现官方弃用立即改计划，而不是继续堆旧 API。

### 4.2 2026-08 技术雷达

#### Adopt（本项目默认采用）

| 领域 | 选择 | 原因 |
| --- | --- | --- |
| 前端（演示壳） | 继续现有 Vue 3 脚手架 | 你已会，不换栈、不学新前端；只接 API |
| 后端 | FastAPI + SQLAlchemy 2 async + Pydantic v2 + uv | 岗位常见组合，且已落地 |
| Agent 编排 | **LangGraph v1 `StateGraph` + Checkpointer** | 企业工作流、循环、HITL、持久状态的主流答案 |
| 简单 Agent 工厂 | `langchain.agents.create_agent`（内部跑 LangGraph） | 仅作薄封装；复杂流程仍手写 StateGraph |
| 工具协议 | **MCP**（Client + 自建 Server） | 2026 年工具接入标准，岗位高频 |
| 检索 | Qdrant **dense + sparse 混合检索** + rerank | 朴素向量检索不够企业精度 |
| 可观测 | **Langfuse** + OpenTelemetry | 开源、可自托管，作品集友好；概念对齐 LangSmith |
| 评测 | 黄金集 + trajectory eval + LLM-as-judge | Agent 质量必须能量化 |
| 流式 | SSE（FastAPI `StreamingResponse`） | Chat 产品标配 |
| 认证 | JWT + refresh + **Argon2** 密码哈希 | 企业最低安全线 |
| OpenAI 路径 | 新代码优先 **Responses API** | OpenAI 对新建项目的推荐；保留 reasoning / 托管工具能力 |

#### Trial（阶段内小范围验证，不绑死全站）

| 技术 | 用法 |
| --- | --- |
| Open Responses | 多模型统一接口的候选标准；Gateway 预留适配层 |
| PydanticAI | 用在「强类型单 Agent / 结构化输出」对比实验，不替换 Runtime |
| OpenAI Agents SDK | 做一次对照实现，理解 handoff / guardrail 原语，不作为主 Runtime |

#### Hold（知道、暂不作为主路径）

| 技术 | 原因 |
| --- | --- |
| 组织 / 多租户完整 IAM | 求职阶段用 RBAC 基础即可 |
| Kubernetes / 微服务拆分 | 单仓模块化先跑通，生产部署放到最后 |
| 自研模型 / 微调 | Agent 工程师岗位主考应用工程，不考训模 |
| Agent Marketplace | 旧 M5，对作品集边际收益低 |
| 前端能力补课 | 你已是前端；本项目不投入学习时间 |

#### Avoid（明确不要用）

| 避免 | 原因（2026） |
| --- | --- |
| LangChain `AgentExecutor` / `initialize_agent` | 维护模式，EOL 约 2026-12 |
| `langgraph.prebuilt.create_react_agent` | 已被 `langchain.agents.create_agent` 取代 |
| OpenAI **Assistants API** | 官方要求迁到 Responses，限期约 2026-08-26 |
| LangChain `ConversationBufferMemory` 等旧 Memory 类 | 状态应显式、可检查点，不要隐藏在框架里 |
| AutoGPT / BabyAGI 式「放开乱跑」 | 企业要可控图，不要失控自治 |
| CrewAI 作为主 Runtime | 演示向；企业编排仍以 LangGraph 为主 |
| 只做 Naive RAG（固定切块 + top-k）当最终方案 | 面试会被追问 hybrid / rerank / eval |
| 把前端做成学习主线（组件库、设计系统、E2E） | 与转 Agent 的目标抢时间 |
| 同步阻塞调用 LLM | 与现有 async 栈相反 |
| 前端提交 `password_hash` | 不安全，也不符合企业实践 |

现有自研 `app.ai.runtime.agent_executor.AgentExecutor` **不是** LangChain 那个已弃用的 `AgentExecutor`。它应保留为教学对照，R2 后生产流量走 LangGraph。

### 4.3 LLM Provider 策略

不要为每个模型写一套业务逻辑。保持现有 Gateway，但升级契约：

```
Agent Runtime (LangGraph)
        │
        ▼
   LLM Gateway          ← 统一：messages / tools / stream / structured output
        │
   ┌────┼────────────┐
   ▼    ▼            ▼
 Qwen  OpenAI     Anthropic
 (兼容) (Responses) (当前 SDK)
```

- **Qwen / 国内兼容接口**：继续走 OpenAI-compatible Chat Completions，直到对方稳定支持 Responses / Open Responses。
- **OpenAI**：新能力（reasoning 跨轮、托管 MCP、file_search）走 Responses；不要在新代码上继续加 Chat Completions 特性。
- **Anthropic**：用官方当前 SDK，不要经三层过时包装。
- Gateway 必须补齐：`tool_calls` 解析、streaming、structured output。这是 R0/R1 的硬条件。

### 4.4 技术迭代机制（每个 R 阶段 Day 1）

每个阶段开工前用半天做评审，只回答四个问题：

1. 本阶段计划用的 API / 框架，官方是否仍推荐？
2. 是否出现新的开放协议可以替换自研接口（MCP、A2A、Open Responses）？
3. 最近 10 条 Agent Engineer JD 是否出现新的必会词？
4. 若有弃用：是「本阶段内迁移」还是「记入下一阶段」？

评审结论写进该阶段的短笔记（新建文件，不改 V1.0 文档）。技术变了就改本计划的下一阶段，而不是假装旧 ADR 永远正确。

---

## 5. 重新划分的阶段

原则：每一阶段结束都有 **可运行演示 + 可写进简历的一句话 + 面试能讲的设计决策**。

```
R0  基线修复                 1–2 周
R1  认证 + 流式 API（演示壳）  3 周     ← 前端约 2–3 天接线，其余全在后端
R2  生产级 Agent Runtime      5 周
R3  企业 RAG                 5 周
R4  MCP 工具平台             4 周
R5  Multi-Agent + A2A        4 周
R6  生产化与作品集           3–4 周
```

合计约 **6–7 个月**。投递可以在 R3 结束后开始（已有鉴权 Chat + Runtime + RAG）；R5/R6 用来拉开和「教程仓库」的差距。

R1 比 V2.0 少一周，是因为前端不再当学习阶段。省下的时间留给 R2/R3，不要填回 UI。

旧计划里的「组织体系、Workflow 引擎、Marketplace、K8s」不进主路径。若有余力，作为 R6 之后的选修。

---

## 6. 阶段详述

### R0 — 基线修复（让现有 Runtime 诚实可用）

**目标**：现有 Chat 在至少一个真实模型和 Mock 上，工具循环是通的；安全上不再「明文当哈希」。

**必须做**

- 所有 Provider 统一解析并回传 `tool_calls`（先修 OpenAI / Anthropic，与 Qwen 对齐）。
- `BaseTool.schema` 必须带 JSON Schema 参数；calculator 要有真实 properties。
- 用户密码改为服务端 Argon2（或 bcrypt）哈希；禁止客户端传 `password_hash`。
- 给 Chat 补 Mock Provider 默认路径，保证无 Key 也能跑测试。
- 修测试命名（如 `text_agent_service.py`）并让 runtime 测试覆盖「有 tool_call / 无 tool_call / 超轮次」。

**不做**：新功能、新框架引入。

**学习**：把你已经写的 loop 讲清楚——为什么要 max iterations、tool 结果如何回灌、Gateway 为什么要和 Runtime 分开。

**验收**

- `POST /api/v1/agents/{id}/chat` 在 Qwen 或 Mock 下能完成「计算题 → 调 calculator → 返回答案」。
- 相关 pytest 全绿。

**简历句**：Built a provider-agnostic tool-calling agent loop (custom runtime) with FastAPI and PostgreSQL.

---

### R1 — 认证 + 流式 API（前端只做演示壳）

**目标**：后端具备企业最低产品面——登录、资源隔离、SSE 流式 Chat。前端用你已有的 Vue 能力花 **2–3 天** 接线，不作为本阶段学习内容。

**必须做（后端，学习主线）**

- 认证：注册 / 登录 / JWT access + refresh；Chat 和 Agent API 鉴权。
- 用户只能操作自己的 Agent / Conversation。
- Chat API 支持 **SSE 流式**（`StreamingResponse` + 可取消）；非流式保留给测试。
- OpenAPI / Swagger 能走通：注册 → 建 Agent → 对话 → 拉历史。
- 按 `EAAP_Request_Handle.md` 统一错误体。

**必须做（前端，只接线，不学）**

最少三页即可，样式用现成 Tailwind，不打磨：

- 登录 / 注册
- Agent 列表 + 创建（name / provider / model / system prompt）
- Chat：发消息、接 SSE、列出历史

不做：设计稿还原、组件库、Markdown 编辑器深度、移动端适配、前端测试。

**技术约束**

- 流式用 SSE，不要轮询。学习发生在 FastAPI 怎么推事件，不在 Vue 怎么画气泡。
- 继续现有 Vue 脚手架，不要换 React、不要上新前端框架。
- 不在这一阶段上 LangGraph。
- 若时间紧：**Swagger 演示优先于页面**。页面可以更丑，API 不能缺。

**学习（全是后端）**

- JWT 与资源隔离；
- SSE 与请求取消、背压；
- Prompt 变量与系统提示的边界。

**验收**

- 用 Swagger 或 curl 独立完成：注册 → 建 Agent → 连续两轮对话 → 拉历史。
- 有一个能录屏的薄页面即可，不作为否决项。

**简历句**：Built authenticated FastAPI agent APIs with SSE streaming and per-user resource isolation.

**面试故事**：为什么先做鉴权和流式 API 再上编排框架——没有边界和可观察的输出，Runtime 无法被验证。

---

### R2 — 生产级 Agent Runtime（本项目的能力分水岭）

**目标**：从「自己写的 for-loop」升级为 **可恢复、可审批、可追踪的状态图**。这是 Agent 工程师岗位的核心题。

**必须做**

- 引入 LangGraph v1：用手写 `StateGraph` 实现与现有 loop 等价的路径（LLM → 可选工具 → 再 LLM）。
- 状态用 Pydantic / TypedDict 显式建模：`messages`、`tool_calls`、`iteration`、`error`。
- Checkpointer 落到 PostgreSQL 或 Redis（进程重启后可恢复）。
- Human-in-the-loop：危险工具（先做「假的发邮件 / 写库」）执行前 `interrupt`；用 **resume API** 继续。前端只需一个确认按钮，或直接用 Swagger 调 resume。
- Structured output：最终答案用 Pydantic 模型校验。
- 现有 `AgentExecutor` 保留为 `legacy` 或对照测试，生产路径切到 Graph。
- 执行过程可查询：每一步 node、输入输出、耗时写入 trace 表或 Langfuse。

**禁止**

- 使用已弃用的 `AgentExecutor` / `initialize_agent` / `create_react_agent`。
- 把业务逻辑写进 LangChain Chain 深包装里，导致你讲不清控制流。

**学习**

- 图 vs 循环：哪些边是条件边，哪些必须是显式状态；
- checkpoint 与「对话 Memory」的区别；
- HITL 为什么是企业 Agent 的默认，而不是 extra。

**验收**

- 同一用例在自研 loop 与 LangGraph 上行为对照测试通过。
- 杀掉 API 进程再启动，未完成的图可以从 checkpoint 继续。
- 演示：模型要调「发送」类工具时执行暂停；调用 resume API（或页面上一个按钮）后才继续。

**简历句**：Replaced an ad-hoc tool loop with LangGraph StateGraph, durable checkpoints, and human-in-the-loop interrupts.

**面试故事**：为什么企业不用纯 ReAct 放开跑——要可审计、可暂停、可恢复。

---

### R3 — 企业 RAG（从「有 Qdrant」到「能答企业内部题」）

**目标**：Agent 能基于上传文档回答，并给出出处。检索质量有数字，不是感觉。

**必须做**

- 知识库：上传 PDF / Markdown / DOCX → 解析 → 切块 → embedding → Qdrant。
- 元数据：文档、版本、权限（至少按 user / agent 隔离）。
- 检索：**混合检索（dense + sparse/BM25）+ rerank**，不要停在 top-k cosine。
- Agent 侧：检索作为 Graph 中的节点或工具，上下文有 token 预算。
- 回答必须带 citation（chunk id / 文档名 / 定位）。
- 评测：20–50 条黄金问答；记录 recall@k、引用正确率、幻觉率（LLM-as-judge + 人工抽检）。
- 上传与引文以 **API 为准**。前端最多：一个文件选择框 + Chat 里把 citation JSON 打成纯文本。不学文件上传组件。

**技术约束**

- 继续用已部署的 Qdrant，不要换向量库。
- Embedding 选当前主流、官方仍推的模型（阶段开始时再确认一次），通过 Gateway 调用。
- 不要把「OpenAI 托管 file_search」当成企业知识库的唯一实现——那锁厂商，也讲不清检索。

**学习**

- chunk 策略与失败模式（切太碎 / 切太大）；
- 为什么 hybrid + rerank；
- RAG 与 Memory 的分工：文档是长期知识，会话是短期状态。

**验收**

- 上传一份「假的员工手册」，问制度类问题，答案带来源。
- 换一份无关文档，模型不能一本正经瞎编且声称来自手册。
- 有一份简短 Eval 报告（Markdown 即可）。

**简历句**：Built a hybrid RAG pipeline on Qdrant with reranking, citations, and an offline eval set.

---

### R4 — MCP 工具平台

**目标**：工具不再写死在 `ToolManager.register(CalculatorTool())`，而是可发现、可授权的能力。

**必须做**

- 定义内部 Tool 接口与 MCP 的适配：Agent 只认「工具描述 + 调用」，不关心工具在进程内还是 MCP Server。
- 实现 1 个 MCP Server（例如：知识库检索、或受控的文件系统 / 模拟订单查询）。
- Runtime 作为 MCP Client 拉取 tool schema 并调用。
- 工具注册表：名称、描述、schema、所需权限、是否需 HITL。
- Agent 配置可勾选可用工具；未授权工具不可见也不可调。
- 继续保留 calculator 作为进程内工具，证明「本地工具 + MCP 工具」可并存。

**学习**

- 为什么 2026 年岗位要 MCP：工具与 Agent 框架解耦，一套工具给多个 Runtime 用；
- schema、鉴权、超时、错误如何设计。

**验收**

- 关掉 MCP Server，Agent 降级并给出明确错误，而不是卡死。
- 两个 Agent 可配置不同工具集。

**简历句**：Integrated MCP so enterprise tools are discovered and authorized independently of the agent runtime.

---

### R5 — Multi-Agent 与 A2A

**目标**：复杂任务由专职 Agent 协作，通信走标准而不是函数互调。

**必须做**

- Supervisor + 至少两个专职 Agent（例如 Knowledge Agent、Writer Agent）。
- 在 LangGraph 里用清晰的 handoff / 子图，而不是一个巨大 prompt 假装多角色。
- 引入 **A2A**（或阶段开始时仍被推荐的 Agent 间协议）做一次跨进程/跨服务调用；若协议有 breaking change，按 4.4 替换，但必须是「协议」而不是内部 Python 调用冒充。
- 任务级状态：谁在做、做到哪、失败由谁重试。消息 / trace 里带 `agent_name`。
- 协作过程优先在 Langfuse 或 API 响应里看。前端若加，只做「按 agent 列出文本」，不学时间线组件。

**不做**：Marketplace、任意 Agent 联网发现全网。

**学习**

- Supervisor vs Swarm；
- 何时不该上多 Agent（成本、延迟、不可控）；
- A2A 要解决的是发现与消息，不是再造一个 LangGraph。

**验收**

- 演示：「根据知识库写一页简报」——检索 Agent 与写作 Agent 分工可见。
- 能讲清：如果 Writer 失败，Supervisor 如何重试或中止。

**简历句**：Implemented a supervisor multi-agent workflow with protocol-based A2A communication.

---

### R6 — 生产化与求职作品集

**目标**：让仓库看起来像能交给企业团队的系统，而不是课程作业。

**必须做**

- 可观测：Langfuse（或等价）里能看到一次 Chat 的完整轨迹；关键指标（延迟、token、工具失败率）。
- 护栏：输入注入检测（基础）、输出 PII 脱敏（基础）、工具白名单、超时与重试策略。
- 成本：按用户 / Agent 统计 token，用 API 返回数字即可；页面一行文本或 Swagger 查看。
- 安全：RBAC 角色（admin / member）；审计日志（谁改了 Agent、谁批了 HITL）。
- CI：以 **ruff + pytest** 为主；前端 type-check 有就留着，不作为学习或门槛。
- 作品包：
  - 根 README：架构图、如何 15 分钟跑起来、能力列表；
  - 3–5 分钟演示脚本 / 录屏提纲；
  - 一页「设计决策」：为何 LangGraph、为何 MCP、为何 hybrid RAG；
  - Eval 报告链接。

**选修（有时间再做）**

- 组织 / 部门；
- Kubernetes；
- Workflow 可视化编排器；
- 前端设计系统 / 管理后台美化。

**验收**

- 陌生人按 README 能跑通 R1+R3 主路径。
- 你能在面试白板上画出 Runtime / RAG / MCP，并指出对应目录。

**简历句**：Productionized an enterprise agent platform with tracing, evals, RBAC, and cost visibility.

---

## 7. 仓库演进（在现有结构上长，不推倒）

目标结构（分阶段长出来，不是一次建完）：

```text
apps/api/app/
├── api/v1/                 # 已有：users, agents, health
├── services/               # 已有
├── repositories/           # 已有
├── models/                 # 已有
├── ai/
│   ├── llm/                # 已有 Gateway；R0/R1 补 stream / tool_calls / Responses
│   ├── runtime/
│   │   ├── agent_executor.py    # 保留对照
│   │   └── graph/               # R2 新增 LangGraph
│   ├── tools/              # 已有；R4 加 MCP adapter + registry
│   ├── memory/             # 已有短期；R2 与 checkpoint 对齐
│   ├── prompts/            # 已有
│   ├── rag/                # R3 新增
│   └── eval/               # R3/R6
├── core/                   # 已有；R1 加 security
└── ...

apps/web/src/               # 演示壳，不是学习范围
├── views/                  # 最多 4 个薄页面：Login, Agents, Chat, Knowledge
├── stores/                 # 只存 token / 当前会话，不设计前端架构
└── router/                 # 接上即可
```

Qdrant / Redis / Postgres 继续用现有 Compose，不新开一套基础设施。`apps/web` 的改动应能在每个阶段用 **1–3 天** 做完；超过这个量就说明前端范围膨胀了，应砍回 API 演示。

---

## 8. 能力矩阵：现在 → 可投递 → 有竞争力

| 能力 | 现在 | R3 结束（可投递） | R6 结束（有竞争力） |
| --- | --- | --- | --- |
| FastAPI 分层与数据模型 | 有 | 有 + 鉴权隔离 | 有 + 审计 / RBAC |
| 自研 Agent loop | 有（有缺口） | 有且测通 | 作为对照保留 |
| LangGraph Runtime | 无 | 有（R2） | 有 HITL + checkpoint |
| 流式 Chat API | 无 | SSE + 鉴权（R1） | 带 trace / agent 字段 |
| 前端演示壳 | 脚手架 | 3 个薄页面或仅 Swagger | 仍保持薄，不为可视化加课 |
| RAG | 无 | 混合检索 + 引用 + eval | 权限隔离 + 回归集 |
| MCP | 无 | 无或预研 | 有 Client + Server |
| Multi-Agent / A2A | 无 | 无 | 有 |
| Observability / 成本 | 无 | 基础日志 | Langfuse + token 统计 |
| 安全 | 字段级密码 | JWT + 哈希 | 护栏 + 审计 |

---

## 9. 学习方式（为找工作服务）

每个阶段按同一循环，不要「先看完书再写代码」：

```
读当前官方文档（当天的）
    → 在 EAAP 里做最小可运行增量
    → 写 10 行以内的决策记录（为何这样）
    → 补测试或一条黄金用例
    → 用面试口吻讲一遍给自己听
```

建议你能口头回答的问题（R3 之后必须能答）：

1. 你的 Agent 和 Chatbot 差在哪？状态存在哪里？
2. 工具调用失败、模型死循环，系统怎么停？
3. 为什么不用 LangChain 旧 AgentExecutor？
4. RAG 答错时，你如何区分「检索错了」还是「模型编了」？
5. 为什么工具要走 MCP，而不是在 Agent 里写死 HTTP？
6. 多 Agent 什么时候不该用？
7. 一次请求的成本怎么算？如何降？

---

## 10. 明确不做（避免再次偏离）

在 R6 完成前，默认拒绝这些诱惑：

- 重写整个后端或换前端框架；
- 把时间花在前端组件库、设计系统、Playwright、像素级 UI 上；
- 为了「更像大厂」先拆微服务；
- 训模型、做 Agent 商店、做通用搜索引擎；
- 同时引入 LangGraph + PydanticAI + OpenAI Agents SDK 三套主 Runtime；
- 回头去补旧计划里的完整组织树、ERP 集成、K8s，除非主路径已完成；
- 修改 V1.0 历史文档来「假装计划一直没偏」。历史文档保持原样；执行以本文为准。

若某次开发又偏离本计划，先更新本文件的阶段范围，再写代码。

---

## 11. 与旧文档的使用约定

| 文件 | 本计划下的角色 |
| --- | --- |
| `Project_Master_Plan.md` 等 V1.0 | 只读历史，愿景仍有效 |
| `ADR-004 Why LangGraph` | 方向仍采纳；实现细节以本文 R2 为准（StateGraph，不用已弃用 prebuilt） |
| `EAAP_STATUS.md` | 已过期；不要在其上续写 M0。需要状态时另建新文件 |
| 本文件 | **当前执行计划** |

愿景不变：企业 AI Agent 基础设施。路径变了：先成为能被雇佣的 Agent 工程师，再用同一套代码长成平台。

---

## 12. 建议的近期执行顺序

立刻开始的只有 R0，不要并行开 RAG 和 LangGraph：

1. 修 Provider `tool_calls` 与 Tool schema；
2. 密码哈希；
3. 确认 Chat + calculator 闭环；
4. 再进入 R1：先做 JWT 与 SSE API，最后用 2–3 天接一层 Vue 壳（或先只用 Swagger）。

R0 完成之日，才算「计划和代码重新对齐」。

---

## 版本记录

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| V2.0 | 2026-08-15 | 按当前代码与 2026 Agent 工程师岗位要求重排；不修改 V1.0 文档 |
| V2.1 | 2026-08-15 | 明确学习者为前端转 Agent：前端降为演示壳，学习时间集中到后端与 Agent |
