# ADR-002 为什么生产 Runtime 用 LangGraph

| 项 | 内容 |
| --- | --- |
| 状态 | Accepted |
| 日期 | 2026-08-15 |
| 替代 | V1 ADR-004 |

## 背景

已有自研 `AgentExecutor` 循环。企业还需要分支、HITL、持久状态、可追踪。2026 年岗位高频要求 LangGraph。

## 决策

- R2 起生产路径：LangGraph v1 **手写 `StateGraph`** + Checkpointer。
- 自研 loop 保留为对照与教学。
- 可用 `langchain.agents.create_agent` 作薄封装，复杂边仍手写。
- **不用** `AgentExecutor`、`initialize_agent`、`create_react_agent`。

## 原因

- 图模型对应企业流程（含暂停、恢复、重试）。
- Checkpoint 是产品能力，不是框架彩蛋。
- 面试可讲，生态成熟。

## 不选作主 Runtime

- 只留自研 loop：缺 HITL/恢复，岗位匹配弱。
- PydanticAI / OpenAI Agents SDK：可 Trial 对照，不替换主路径（避免三套并行）。
- CrewAI：演示向。
