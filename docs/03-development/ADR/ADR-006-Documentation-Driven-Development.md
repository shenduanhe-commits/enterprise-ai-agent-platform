---
title: ADR-006 Documentation Driven Development
version: V1.0
status: Accepted
created: 2026-07
---

# ADR-006

# 为什么 EAAP 采用 Documentation Driven Development


---

# 1. 状态


Accepted


---

# 2. 背景


EAAP目标不是简单Demo。


目标：

构建：

企业级 AI Agent 平台


因此需要：

- 产品文档
- 架构文档
- 技术文档
- 开发规范


---

# 3. 问题


没有文档驱动时：

容易出现：

```
想到什么做什么

↓

代码越来越乱

↓

无法维护

↓

无法扩展

```


---

# 4. 决策


采用：

Documentation Driven Development


即：

先设计，再开发。


---

# 5. 开发流程


```
Idea

↓

PRD

↓

User Story

↓

Architecture

↓

ADR

↓

Implementation

↓

Testing

↓

Release

```


---

# 6. 原因


## 6.1 接近真实企业研发流程


大型企业通常：

需求评审

↓

技术评审

↓

开发

↓

测试

↓

发布


---

## 6.2 适合作品展示


求职时可以展示：

不仅有代码：

还有：

- 产品能力
- 架构能力
- 工程能力


---

## 6.3 降低复杂度


EAAP涉及：

- LLM
- RAG
- Agent
- Workflow
- Multi-Agent


必须通过文档控制复杂度。


---

# 7. 影响


项目目录：

```
docs

├── product

├── architecture

├── development

└── deployment

```


---

# 8. 后续规范


所有重要技术决策：

必须新增ADR。


---

# 9. 相关文档


- PRD.md
- System_Architecture.md


---

# Revision


|版本|日期|说明|
|-|-|-|
|V1.0|2026-07|初始决策|
