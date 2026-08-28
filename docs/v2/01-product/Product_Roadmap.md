# 产品与执行路线 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/01-product/Product_Roadmap.md`（V1 Phase 1–5）及旧 Milestone M0–M5 |

V1 的产品 Phase（Chat → Knowledge → Agent → Workflow → Multi-Agent）仍然是能力递进顺序，但执行编号改为 **R0–R6**，并承认代码已经预支了部分 Agent Runtime。

---

## 1. 总览

```
R0 基线 → R1 鉴权与流式 → R2 LangGraph → R3 RAG → R4 MCP → R5 多 Agent → R6 作品集
```

原则：小步、可演示、真实场景；前端不单独占阶段。

---

## 2. R0 — 基线修复（1–2 周）

**目标**：现有 Runtime 在至少一个真实模型或 Mock 上，工具循环是通的。

必须做：

- 所有 Provider 解析并回传 `tool_calls`。
- `BaseTool.schema` 带 JSON Schema；calculator 有真实参数。
- 服务端 Argon2（或 bcrypt）哈希；禁止客户端传 `password_hash`。
- Mock Provider 默认可测。
- 测试覆盖无工具 / 有工具 / 超轮次；修正测试文件命名。

不做：新框架、新功能、前端。

验收：`POST /api/v1/agents/{id}/chat` 能完成「计算题 → calculator → 答案」；pytest 绿。

---

## 3. R1 — 认证 + 流式 API（3 周）

**目标**：企业最低产品面。学习全在后端。前端 2–3 天接线或只用 Swagger。

必须做（后端）：

- 注册 / 登录 / JWT access + refresh。
- Chat、Agent、Conversation 鉴权；只能碰自己的资源。
- SSE 流式；非流式留给测试。
- 统一错误体。

前端（非学习）：登录、Agent 列表/创建、Chat 三页即可。

不做：LangGraph、知识库、组件库。

验收：Swagger/curl 独立走通 注册 → 建 Agent → 两轮对话 → 拉历史。

---

## 4. R2 — 生产级 Agent Runtime（5 周）

**目标**：可恢复、可审批、可追踪的状态图。本项目能力分水岭。

必须做：

- LangGraph v1 手写 `StateGraph`，行为对齐现有 loop。
- 显式状态：`messages`、`tool_calls`、`iteration`、`error`。
- Checkpointer → PostgreSQL 或 Redis。
- 危险工具 `interrupt`；`resume` API；页面最多一个按钮。
- 最终答案 Structured output。
- 自研 `AgentExecutor` 保留对照；生产切 Graph。
- 每步 node 可查（表或 Langfuse）。

禁止：`AgentExecutor`（LangChain）、`initialize_agent`、`create_react_agent`。

验收：对照测试通过；杀进程后可恢复；发送类工具必须先 resume。

**2026-08-28 后端验收**：上表除「最终答案 Structured output」「页面批准按钮」外已落地。Structured output 与前端明确不做；Langfuse 属 R6。

---

## 5. R3 — 企业 RAG（5 周）

**目标**：基于上传文档回答并给出处，质量有数字。

必须做：

- 上传 PDF / Markdown / DOCX → 解析 → chunk → embedding → Qdrant。
- 元数据与至少 user/agent 隔离。
- 混合检索 + rerank；上下文 token 预算。
- citation。
- 20–50 条黄金集：recall@k、引用正确率、幻觉率。
- 上传/引文以 API 为准。

不要把 OpenAI 托管 file_search 当企业知识库唯一实现。

验收：员工手册问答带来源；无关文档不能冒充手册；有 Eval 短报告。

---

## 6. R4 — MCP 工具平台（4 周）

**目标**：工具可发现、可授权，不写死在 `register(CalculatorTool())`。

必须做：

- 内部 Tool 接口适配 MCP。
- 1 个 MCP Server（检索或模拟订单）。
- Runtime 作 Client。
- 注册表：schema、权限、是否 HITL。
- Agent 勾选工具集；calculator 仍作进程内对照。

验收：MCP Server 挂掉时明确降级；两 Agent 工具集可不同。

---

## 7. R5 — Multi-Agent 与 A2A（4 周）

必须做：

- Supervisor + 至少两个专职 Agent。
- LangGraph 子图/handoff，不用一个 prompt 扮多角色。
- A2A（或当时仍推荐的 Agent 间协议）做一次跨进程调用。
- 任务级状态；响应带 `agent_name`。
- 过程优先看 Langfuse/API。

不做：Marketplace、全网 Agent 发现。

验收：「按知识库写简报」能看出分工；能讲清 Writer 失败时如何中止/重试。

---

## 8. R6 — 生产化与作品集（3–4 周）

必须做：

- Langfuse（或等价）看完整轨迹；延迟 / token / 工具失败率。
- 护栏：基础注入检测、PII 脱敏、工具白名单、超时重试。
- Token 按用户/Agent 统计（API 返回即可）。
- RBAC（admin / member）+ 审计日志。
- CI：ruff + pytest。
- 作品包：README（15 分钟跑起来）、3–5 分钟演示提纲、一页设计决策、Eval 报告。

选修：组织树、K8s、可视化编排、前端美化。

---

## 9. 版本对照

| V2 阶段 | 约等于 V1 | 代码现状 |
| --- | --- | --- |
| 已完成的工程基础 | M0 | 已完成 |
| 部分 Agent CRUD + 自研 loop | M1/M2 碎片 | 已预支 |
| R0–R1 | M1 认证 + V1 Phase1 Chat | 后端完成；前端选修 |
| R2 | M2 Runtime（框架级） | 后端完成 |
| R3 | V1 Phase2 Knowledge | 未做 |
| R4–R5 | V1 Phase3–5 的工具与协作 | 未做 |
| R6 | M4 的薄切片 | 未做 |

---

## 10. 偏离控制

R6 完成前默认拒绝：换前端框架、拆微服务、训模、三套 Runtime 并行、回写 V1 文档假装没偏。若范围变了，先改本文和 `STATUS.md`，再改代码。
