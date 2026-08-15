# EAAP 主计划 V2.1

| 项目 | 内容 |
| --- | --- |
| 产品 | Enterprise AI Agent Platform（EAAP） |
| 版本 | V2.1 |
| 状态 | Active |
| 日期 | 2026-08-15 |
| 替代 | `docs/00-master/Project_Master_Plan.md`（V1）及 `EAAP_Realignment_Plan_V2.0.md` |

---

## 1. 项目是什么

EAAP 是面向企业内部的 **AI Agent 应用平台**，不是单一聊天机器人，也不是自研大模型。

核心理念：

```
用户 → AI Agent → 理解任务 → 调用知识 / 工具 / 系统 → 完成业务目标
```

最终形态：**Enterprise AI Agent Operating Platform**——创建、管理、运行、协作、治理 Agent。

本仓库同时是：

1. 一个可演示的企业 Agent 产品；
2. 一条从前端工程师转到 Agent 开发工程师的学习与作品集路径。

---

## 2. 三重目标

| 维度 | 目标 |
| --- | --- |
| 产品 | 企业能用的 Agent 平台：对话、知识问答、工具执行、可治理 |
| 工程学习 | 掌握 2026 年可落地的 Agent 工程：Runtime、RAG、MCP、Eval、安全 |
| 职业 | 拿到 Agent / AI Application Engineer（含日本生成AIエンジニア）offer |

能力成长：

```
Frontend Engineer → AI Application Engineer → Agent Engineer → Enterprise AI Engineer
```

本阶段只要求走到 **Agent Engineer 可投递**。更后面的架构师能力不挡主路径。

---

## 3. 要解决的问题

1. 企业知识散落，员工检索成本高。
2. 报告、查询、流程类重复劳动多。
3. 各部门各接各的模型，没有统一运行与治理。

**不做**：自研/微调基础模型、通用搜索引擎、替代 ERP、早期 Agent 商店。

---

## 4. 开发原则

```
文档先行 → 架构先行 → 实现 → 测试（含 Agent Eval）→ 演示 → 再扩展
```

补充原则：

1. **官方当前推荐优先**，不以 2023–2024 教程为准。每个阶段开工做一次技术雷达评审。
2. **先协议、后框架**：Tool 走 MCP，多 Agent 走 A2A，LLM 走 Gateway。
3. **自研保留理解，框架承接生产**：现有 `AgentExecutor` 对照保留；生产路径升级到 LangGraph。
4. **前端是演示壳**：学习时间约 90% 在后端与 Agent。
5. **每阶段必须可运行、可演示、可讲清设计决策。**

---

## 5. 阶段总览（R0–R6）

旧 V1 的 M0–M5 不再使用。现行编号是 **R**。

```
R0  基线修复                 1–2 周
R1  认证 + 流式 API           3 周
R2  生产级 Agent Runtime      5 周
R3  企业 RAG                 5 周
R4  MCP 工具平台             4 周
R5  Multi-Agent + A2A        4 周
R6  生产化与作品集           3–4 周
```

合计约 **6–7 个月**。R3 结束后可以开始投递；R5/R6 拉开与教程仓库的差距。

| 阶段 | 目标 | 简历句 |
| --- | --- | --- |
| R0 | 现有 Chat + 工具循环诚实可用 | provider-agnostic tool-calling loop |
| R1 | JWT、资源隔离、SSE | authenticated FastAPI agent APIs with SSE |
| R2 | LangGraph、checkpoint、HITL | StateGraph + durable checkpoints + HITL |
| R3 | 混合检索、引用、评测 | hybrid RAG on Qdrant with eval |
| R4 | MCP Client/Server、工具授权 | MCP-discovered authorized tools |
| R5 | Supervisor + A2A | multi-agent with protocol communication |
| R6 | Trace、护栏、成本、作品包 | tracing, evals, RBAC, cost visibility |

旧计划中的组织树、Marketplace、K8s、Workflow 可视化编排器：**R6 之后选修**，不进主路径。

阶段细节、验收、禁止事项见 [Product_Roadmap.md](../01-product/Product_Roadmap.md)。

---

## 6. MVP 定义

V2 的 MVP = **R0 + R1 + R2 + R3**。

必须具备：

- 用户注册登录与资源隔离；
- Agent 创建与配置；
- 流式单 Agent 对话；
- 工具调用（至少 calculator + 检索工具）；
- 企业文档 RAG（混合检索 + 引用 + 小评测集）。

没有完整前端也可以，Swagger 能走通即算产品面成立。

---

## 7. 技术策略（摘要）

完整雷达见 [Technology_Stack.md](../02-architecture/Technology_Stack.md)。

| 层 | 采用 |
| --- | --- |
| 前端演示壳 | 现有 Vue 3 + Vite + TypeScript（不换栈、不学） |
| 后端 | Python 3.12、uv、FastAPI、SQLAlchemy 2 async、Pydantic v2 |
| Agent | 自研 loop（对照）→ LangGraph v1 StateGraph |
| 工具 | 进程内 Tool + MCP |
| 检索 | Qdrant dense + sparse + rerank |
| 数据 | PostgreSQL 16、Redis 7 |
| 可观测 | Langfuse + OpenTelemetry |
| 认证 | JWT + Argon2 |

明确不用：LangChain `AgentExecutor`、`create_react_agent`、OpenAI Assistants API、Naive RAG 当最终方案、AutoGPT 式失控自治。

---

## 8. 文档治理

- 唯一现行集：`docs/v2/`。
- 状态：`docs/v2/00-master/STATUS.md`。
- 架构决策：`docs/v2/03-development/ADR/`。
- 变更：先改 STATUS 和对应 V2 文档，再写代码。
- 不回写 V1 文件。

---

## 9. 长期愿景（不挡当前路径）

企业可以：创建 Agent、管理 Agent、运行 Agent、协作 Agent、治理 Agent。

当前 7 个月只交付愿景中「能运行、能检索、能治理到可面试」的那一段。
