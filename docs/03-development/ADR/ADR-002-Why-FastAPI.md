---
title: ADR-002 Why Choose FastAPI
version: V1.0
status: Accepted
created: 2026-07
---

# ADR-002

# 为什么 EAAP 选择 FastAPI 作为后端框架


---

# 1. 状态


Accepted


---

# 2. 背景


EAAP 后端需要支持：

- AI API
- Agent Runtime
- RAG Pipeline
- Workflow Engine
- Enterprise Integration


需要一个适合AI应用开发的后端框架。


---

# 3. 候选方案


## Option A

Django


优势：

- 成熟
- 企业应用广泛


不足：

- AI生态结合稍弱
- 重量较高


---

## Option B

FastAPI


优势：

- 高性能
- 异步支持
- AI生态丰富
- API开发效率高


不足：

- 部分企业后台能力需要自行搭建


---

# 4. 决策


选择：

FastAPI


---

# 5. 原因


## AI生态优势


Python是AI主要生态。


FastAPI天然适合：

- LangChain
- LangGraph
- OpenAI SDK


---

## 异步能力


Agent任务：

可能包含：

- LLM调用
- API调用
- 数据查询


异步模型更加适合。


---

## 开发效率


支持：

- 自动API文档
- 类型提示
- 快速开发


---

# 6. 影响


采用：

```
FastAPI

+

Pydantic

+

SQLAlchemy

```


---

# 7. 相关文档


- Technology_Stack.md
- System_Architecture.md
