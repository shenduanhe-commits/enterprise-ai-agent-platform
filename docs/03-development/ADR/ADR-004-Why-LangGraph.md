---
title: ADR-004 Why Choose LangGraph
version: V1.0
status: Accepted
created: 2026-07
---

# ADR-004

# 为什么 EAAP 选择 LangGraph 作为 Agent Framework


---

# 1. 状态


Status:

Accepted


---

# 2. 背景


EAAP 的核心能力是：

Enterprise AI Agent Platform


未来需要支持：

- Agent Runtime
- Tool Calling
- Memory
- Workflow
- Multi-Agent
- A2A


因此需要选择合适的 Agent Framework。


---

# 3. 候选方案


## Option A

LangChain Agent


优势：

- 生态成熟
- 社区规模大
- 快速开发


不足：

- 复杂流程控制能力有限


---

## Option B

LangGraph


优势：

- 基于状态图设计
- 支持复杂 Agent Workflow
- 支持 Multi-Agent
- 可控性强


不足：

- 学习成本高于简单 Agent


---

## Option C

自研 Agent Framework


优势：

- 完全控制


不足：

- 开发成本高
- 维护成本高
- 不适合初期项目


---

# 4. 决策


选择：

LangGraph


作为 EAAP Agent Runtime 基础框架。


---

# 5. 决策原因


## 5.1 企业场景需要可控性


企业 Agent 不只是聊天。


例如：

```
客户分析报告生成


步骤：

1. 获取客户数据

2. 分析数据

3. 生成报告

4. 人工审核

5. 发布结果

```


这种流程天然适合 Graph。


---

## 5.2 支持状态管理


Agent需要保存：

- 当前任务状态
- 已完成步骤
- 下一步行动


LangGraph：

```
State

↓

Node

↓

Edge

```


非常适合。


---

## 5.3 支持 Multi-Agent


未来：

```
Supervisor Agent

        |

----------------

Research Agent

Data Agent

Report Agent

```


LangGraph适合这种架构。


---

# 6. 影响


EAAP Agent层设计：


```
Agent Runtime

↓

LangGraph

↓

Tools

↓

LLM

```


---

# 7. 后续规划


Phase 3:

单Agent


Phase 4:

Workflow Agent


Phase 5:

Multi-Agent + A2A


---

# 8. 相关文档


- Agent_Architecture.md
- Technology_Stack.md


---

# Revision


|版本|日期|说明|
|-|-|-|
|V1.0|2026-07|初始决策|
