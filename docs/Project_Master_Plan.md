# Enterprise AI Agent Platform（EAAP）
# 项目总体规划（Master Plan）V1.0

> Version: V1.0
>
> Author: 申一 & ChatGPT
>
> Status: Planning
>
> Goal: 打造一个符合企业级标准、可持续迭代、支持 AI Agent、RAG、Multi-Agent、A2A、MCP 的 AI 应用平台。

---

# 一、项目愿景（Vision）

Enterprise AI Agent Platform（EAAP）是一个面向企业办公场景的 AI Agent 平台。

项目不仅是一个学习项目，而是按照真实企业研发流程打造的可持续迭代产品。

项目目标包括：

- 学习企业级 AI Agent 开发流程
- 掌握现代 AI Application 技术栈
- 掌握完整的软件工程能力
- 建立能够展示个人技术能力的开源项目
- 支撑国内 AI 岗位及日本企业求职

---

# 二、项目定位

EAAP 定位为：

> 企业 AI Agent 工作平台（Enterprise AI Workspace）

系统帮助企业员工：

- 查询企业知识
- 调用企业业务能力
- 自动生成文档
- 执行业务流程
- 多 Agent 协同工作

最终支持：

- Chat
- RAG
- Tool Calling
- Workflow
- Multi-Agent
- A2A
- MCP

---

# 三、项目目标

## 第一阶段目标（3~4个月）

目标：

完成企业 AI Chat 平台。

包括：

- AI Chat
- Streaming
- 会话管理
- 用户系统
- Vue + FastAPI

完成后：

能够胜任 AI 应用开发岗位。

---

## 第二阶段目标（5~8个月）

增加：

- RAG
- 企业知识库
- Tool Calling
- LangGraph
- Workflow

完成后：

能够胜任 Agent 开发岗位。

---

## 第三阶段目标（9~12个月）

增加：

- Multi-Agent
- A2A
- MCP
- 企业后台
- 权限系统
- Docker
- CI/CD

完成后：

达到企业级 AI 平台标准。

---

# 四、项目核心能力

## AI能力

- Chat
- Prompt Engineering
- Structured Output
- Function Calling
- Tool Calling
- RAG
- Workflow
- Agent Memory
- Multi-Agent
- A2A
- MCP

---

## 工程能力

- Vue3
- TypeScript
- FastAPI
- Python
- PostgreSQL
- Redis
- Qdrant
- Docker
- GitHub Actions
- Playwright
- Vitest
- Ruff
- Pytest

---

## 产品能力

学习：

- 产品需求分析
- PRD
- 信息架构
- API设计
- 数据库设计
- Agent设计
- 架构设计

---

# 五、技术架构

```
Vue3

↓

FastAPI

↓

LLM Service

↓

Supervisor Agent

↓

Knowledge Agent

Business Agent

Document Agent

↓

RAG

↓

Vector Database

↓

Enterprise Tools
```

---

# 六、项目目录（最终形态）

```
enterprise-ai-agent-platform

apps/
├── web
└── api

packages/
├── agent-core
├── rag-core
├── shared
├── ui
└── observer

docs/
├── prd
├── architecture
├── api
├── database
├── adr
└── roadmap

docker/

scripts/

tests/

.github/

README.md
```

---

# 七、开发原则

## 原则一

先理解，再编码。

---

## 原则二

每一个阶段都必须可运行。

---

## 原则三

先实现底层原理，再引入框架。

---

## 原则四

所有模块可扩展。

---

## 原则五

所有代码都有文档。

---

# 八、Milestone 规划

## Milestone 1

项目初始化

内容：

- Monorepo
- Vue
- FastAPI
- Docker
- Git

交付：

可运行项目。

---

## Milestone 2

AI Chat

内容：

- Chat
- Streaming
- Markdown
- History

---

## Milestone 3

用户系统

内容：

- 登录
- JWT
- 权限

---

## Milestone 4

RAG

内容：

- 上传
- 切片
- Embedding
- 检索

---

## Milestone 5

Knowledge Agent

---

## Milestone 6

LangGraph Workflow

---

## Milestone 7

Business Agent

---

## Milestone 8

Tool Calling

---

## Milestone 9

Document Agent

---

## Milestone 10

企业后台

---

## Milestone 11

Multi-Agent

---

## Milestone 12

A2A

---

## Milestone 13

MCP

---

## Milestone 14

Observability

---

## Milestone 15

企业部署

包括：

- Docker Compose
- Nginx
- HTTPS
- CI/CD

---

# 九、每个 Milestone 的固定交付物

每完成一个阶段，必须提交：

- 功能代码
- 单元测试
- API 文档
- 架构图
- 数据库变更
- Git Tag
- Release Note

---

# 十、文档体系

项目开发过程中持续维护：

## 产品

- PRD
- Roadmap

---

## 技术

- 架构设计
- 数据库设计
- API设计
- Agent设计

---

## 工程

- ADR
- Coding Style
- Git Workflow
- Commit Convention

---

## 学习

- 每周总结
- 技术博客
- 面试题总结

---

# 十一、Git 规范

分支：

```
main

develop

feature/*

release/*

hotfix/*
```

Commit：

```
feat:

fix:

docs:

refactor:

test:

chore:
```

---

# 十二、质量保障

测试：

- Vitest
- Playwright
- Pytest

代码质量：

- ESLint
- Oxlint
- Ruff
- Pyright

CI：

GitHub Actions

---

# 十三、最终成果

完成项目后，将拥有：

## 产品成果

- 企业 AI Agent 平台

---

## 技术成果

- 完整企业级代码

---

## 工程成果

- 企业研发流程实践

---

## 文档成果

- 完整设计文档

---

## GitHub成果

- 企业级开源项目

---

## 求职成果

可用于：

- 国内 AI Agent 工程师岗位
- 日本 AI 应用工程师岗位
- 企业 AI 平台开发岗位

---

# 十四、项目成功标准（Definition of Success）

当满足以下条件时，认为项目达到目标：

## 产品

- 完整 AI Agent 平台可运行

## 技术

- 支持 Chat、RAG、Tool Calling、Workflow、Multi-Agent、A2A、MCP

## 工程

- Docker 化部署
- CI/CD 自动化
- 完整测试体系
- 完整文档体系

## 个人成长

具备：

- 产品设计能力
- 架构设计能力
- 企业级开发能力
- AI Agent 开发能力
- 独立完成企业 AI 项目的能力

---

> Build like an engineer.
>
> Think like an architect.
>
> Deliver like a product team.