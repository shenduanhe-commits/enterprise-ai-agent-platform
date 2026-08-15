# 成本与治理 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/04-deployment/CostManagement.md`、`AIGovernance.md` |

两份 V1 都很「企业完整版」。V2 只保留作品集和岗位需要讲清的部分。

---

## 1. 成本

驱动因素：输入/输出 token、工具轮次、embedding、rerank。

R6 最低要求：

- 每次 run 记录 `tokens_in` / `tokens_out` / provider / model。
- `GET /usage` 或日志能按 user、agent 汇总。
- 能口头回答：怎么降（更小上下文、更少轮次、便宜模型做分类、缓存检索）。

R0–R5：先有 max iterations 和 Mock，避免本地开发烧钱。Live 测试显式标记。

不做：自动模型路由、复杂 FinOps 看板。

---

## 2. 治理

治理 = 谁能创建 Agent、谁能调哪些工具、知识谁能看、一次执行能否复盘。

| 对象 | V2 做法 |
| --- | --- |
| Agent | 所有者 + status；R6 admin 可禁用 |
| Prompt | `prompt.version` 已有；不要静默改线上模板 |
| Tool | R4 注册表 + 绑定；写操作 HITL |
| Model | Agent 上的 provider/model 字段，不在代码写死一家 |
| 知识 | R3 owner 隔离 |
| 执行 | R2+ run/trace；R6 审计 |

V1 的模型评审委员会、合规员角色：不建组织，用文档+审计字段表达同样思想。

---

## 3. 面试怎么讲

「我们没有上完整 AI 治理平台，但默认拒绝未授权工具、危险动作 HITL、知识按用户过滤、每次 run 可追溯、token 可加总。这些是治理的工程内核。」
