# EAAP 文档 V2

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 状态 | **现行唯一文档集** |
| 日期 | 2026-08-15 |
| 读者 | 以本目录为准，不再阅读 V1 |

---

## 1. 文档地位

从 V2.1 起，**只使用 `docs/v2/`**。

| 路径 | 地位 |
| --- | --- |
| `docs/v2/` | 现行文档，了解项目只看这里 |
| `docs/00-master/`、`docs/01-product/` 等 V1 | 归档，不再更新、不再作为依据 |
| 根目录 `EAAP_STATUS.md`、`PROJECT_CHANGELOG.md` 等 V1 操作记录 | 归档 |
| `docs/00-master/EAAP_Realignment_Plan_V2.0.md` | 起草稿，内容已并入本目录 |

V1 可以对照历史，但执行、学习、面试准备都以 V2 为准。两套冲突时，以 V2 为准。

---

## 2. 怎么读

按角色选入口，不必按目录逐份读完。

| 你想知道 | 先读 |
| --- | --- |
| 项目是什么、做到哪、下一步做什么 | [00-master/STATUS.md](00-master/STATUS.md) → [00-master/Project_Master_Plan.md](00-master/Project_Master_Plan.md) |
| 怎么学才能转到 Agent 工程师 | [00-master/LEARNING_ROADMAP.md](00-master/LEARNING_ROADMAP.md) |
| 产品要做成什么样 | [01-product/PRD.md](01-product/PRD.md) |
| 阶段顺序与交付 | [01-product/Product_Roadmap.md](01-product/Product_Roadmap.md) |
| 具体用户故事 | [01-product/UserStory.md](01-product/UserStory.md) |
| 系统怎么分层、代码在哪 | [02-architecture/System_Architecture.md](02-architecture/System_Architecture.md) |
| Agent 怎么跑 | [02-architecture/Agent_Architecture.md](02-architecture/Agent_Architecture.md) |
| 用什么技术、不用什么 | [02-architecture/Technology_Stack.md](02-architecture/Technology_Stack.md) |
| 表和向量库 | [02-architecture/Database.md](02-architecture/Database.md) |
| HTTP / SSE 接口 | [02-architecture/AI_API.md](02-architecture/AI_API.md) |
| 如何把环境跑起来 | [03-development/Environment.md](03-development/Environment.md) |
| 代码与测试约定 | [03-development/CodingStyle.md](03-development/CodingStyle.md)、[TestingStrategy.md](03-development/TestingStrategy.md) |
| 安全 / 可观测 / 部署 | [04-operations/](04-operations/) |

---

## 3. 目录

```text
docs/v2/
├── README.md                          ← 你在这里
├── 00-master/
│   ├── Project_Master_Plan.md         愿景、阶段、职业目标
│   ├── LEARNING_ROADMAP.md            学习路线（后端 + Agent）
│   └── STATUS.md                      当前进度与下一步
├── 01-product/
│   ├── PRD.md
│   ├── Product_Roadmap.md
│   └── UserStory.md
├── 02-architecture/
│   ├── System_Architecture.md
│   ├── Agent_Architecture.md
│   ├── Technology_Stack.md
│   ├── Database.md
│   └── AI_API.md
├── 03-development/
│   ├── Environment.md
│   ├── CodingStyle.md
│   ├── TestingStrategy.md
│   ├── GitWorkflow.md
│   ├── Request_Handle.md
│   └── ADR/
└── 04-operations/
    ├── Deployment.md
    ├── Security.md
    ├── Observability.md
    └── Cost_and_Governance.md
```

---

## 4. 和代码的关系

文档描述两层事实，必须写清楚：

- **已落地**：仓库里已经有的（以代码为准）。
- **目标态**：R0–R6 计划中要做的。

`STATUS.md` 负责对齐这两层。阶段完成时先改 STATUS，再改对应设计文档里的「已落地」段落。

---

## 5. V1 → V2 对照（只为找历史，不读 V1 执行）

| V1 | V2 |
| --- | --- |
| `docs/00-master/Project_Master_Plan.md`、`EAAP_Realignment_Plan_V2.0.md` | `00-master/Project_Master_Plan.md` |
| `docs/00-master/LEARNING_ROADMAP.md` | `00-master/LEARNING_ROADMAP.md` |
| `EAAP_STATUS.md`、`PROJECT_CHANGELOG.md` | `00-master/STATUS.md` |
| `docs/01-product/*`、`docs/产品需求设计 V1.0.md` | `01-product/` |
| `docs/02-architecture/*`、`docs/系统架构设计文档 V1.0.md`、`docs/Agent设计文档 V1.0.md` | `02-architecture/` |
| `docs/数据库设计文档 V1.0.md` | `02-architecture/Database.md` |
| `docs/AI接口设计文档 V1.0.md` | `02-architecture/AI_API.md` |
| `DEVELOPMENT.md`、`EAAP_DOCKER-USE.md`、`EAAP_PNPM-UV-USE.md`、`EAAP_DATABASE_USE.md`、`Environment.md` | `03-development/Environment.md` |
| `CodingStyle.md` / `TestingStrategy.md` / `GitWorkflow.md` | `03-development/` 同名 |
| `EAAP_Request_Handle.md` | `03-development/Request_Handle.md` |
| `docs/03-development/ADR/*` | `03-development/ADR/`（重新编号） |
| `docs/04-deployment/*` | `04-operations/` |
| Milestone Completed Steps | 已消化进 `STATUS.md`，不另写一份 |

---

## 6. 学习者约定

作者是前端开发人员，目标是成为 **Agent 开发工程师**。

- 学习重点：后端、Agent Runtime、RAG、MCP、评测与治理。
- 前端：演示壳，只接线，不作为学习主线。
- 日常验收：FastAPI `/docs`、curl、pytest；浏览器页面只为录屏。
