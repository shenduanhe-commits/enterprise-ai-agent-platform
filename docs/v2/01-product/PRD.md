# 产品需求文档 V2.1

| 项目 | 内容 |
| --- | --- |
| 产品 | Enterprise AI Agent Platform（EAAP） |
| 中文名 | 企业智能业务助手平台 |
| 版本 | V2.1 |
| 状态 | Active |
| 替代 | `docs/01-product/PRD.md`、`docs/产品需求设计 V1.0.md` |

---

## 1. 定位

EAAP 是企业内部的 Agent 运行与管理平台。员工用自然语言完成查询、分析和受控的任务执行；平台统一管理模型、知识、工具和审计。

```
传统：用户 → 业务系统 → 人工操作
EAAP：用户 → Agent → 理解任务 → 知识 / 工具 / 系统 → 业务结果
```

不是 Chatbot 产品，核心是 **AI Agent Runtime**。

---

## 2. 背景与痛点

- 制度、产品、项目资料分散，查询慢。
- 报告、对账、信息整理等重复劳动多。
- 部门各自接模型，权限和数据割裂。

成功标准：能解决真实（可模拟）企业场景，并且代码能作为 Agent 工程师作品集。

---

## 3. 用户角色（V2 范围）

| 角色 | 需求 | 何时做 |
| --- | --- | --- |
| 员工 | 对话、查知识、看引用 | R1–R3 |
| Agent 开发者（你自己） | 配置 Agent、工具、Prompt | R1–R4 |
| 管理员 | 用户、基础 RBAC、审计 | R1 最小鉴权，R6 补齐 |
| 知识管理员 | 上传文档、看处理状态 | R3 |
| 部门主管 | 团队用量、审核输出 | R6 选修，不做完整组织树 |

V1 的完整组织 / 部门体系不在 MVP。

---

## 4. 使用场景

### 场景 A：企业知识助手（MVP）

问「报销流程是什么？」→ Knowledge 检索 → 带出处回答。

### 场景 B：带工具的单 Agent（MVP）

问计算或查询类问题 → 模型调工具 → 用工具结果作答。

### 场景 C：需审批的操作（R2）

Agent 要「发送 / 写入」前暂停，人确认后继续。

### 场景 D：协作出简报（R5）

Supervisor 拆给 Knowledge Agent 与 Writer Agent，过程可追踪。

V1 里的销售/HR/财务专用 Agent 用同一 Runtime 配置，不各写一套系统。

---

## 5. 功能范围

### 5.1 做（按 R 阶段）

| 模块 | 能力 | 阶段 |
| --- | --- | --- |
| 认证 | 注册、登录、JWT、本人资源隔离 | R1 |
| Agent 管理 | 创建、配置 provider/model/prompt/status | 已有 CRUD，R1 加鉴权 |
| Chat | 多轮、历史、SSE 流式 | Chat 已有非流式；R1 流式 |
| Memory | 短期会话；长期=知识库 | 短期已有；R3 知识 |
| Tools | 进程内工具 + MCP + 权限 + HITL | R0 calculator 修通；R2 HITL；R4 MCP |
| RAG | 上传、解析、混合检索、rerank、citation、eval | R3 |
| Multi-Agent | Supervisor、A2A | R5 |
| 治理 | Trace、护栏、成本、审计、RBAC | R6 |

### 5.2 不做（直到选修）

- 自研大模型、通用搜索、ERP 替代。
- Agent Marketplace、完整 IAM/组织树、Workflow 可视化设计器、K8s 多集群。
- 精致前端：管理后台设计系统、移动端、E2E 作为产品目标。

前端只要能录屏：登录、选 Agent、对话、确认 HITL、看见引文。其余用 Swagger。

---

## 6. Agent 能力（产品语言）

| 能力 | 含义 |
| --- | --- |
| Reasoning | 理解用户目标（由模型 + 状态完成，不单独造模块神话） |
| Planning | 复杂任务用图/Supervisor 拆步，不靠一个万能 prompt |
| Tool Calling | 调 API / DB / MCP；有 schema、超时、权限 |
| Memory | 会话上下文 + 企业知识，两者分开 |
| HITL | 危险动作可暂停 |
| Evaluation | 质量可量化 |

---

## 7. 非功能

| 项 | V2 要求 |
| --- | --- |
| 性能 | 首 token 尽快；流式；普通对话可交互 |
| 安全 | 认证、最小权限、工具白名单、基础注入/PII 护栏 |
| 可维护 | 模块化单体；pytest；文档与代码同步 |
| 可扩展 | 新模型走 Gateway；新工具走注册表/MCP |
| 部署 | 本地 Docker Compose 一键；K8s 选修 |
| 可观测 | R2 起有执行轨迹；R6 接 Langfuse |

---

## 8. 成功指标

**技术**：LLM 多 Provider、流式、LangGraph Runtime、混合 RAG、MCP、基础治理。

**产品**：手册问答带来源；工具题能算/能查；危险操作能拦住。

**职业**：仓库 + 演示 + 设计决策页，够投 Agent Engineer。
