---
title: Enterprise AI Agent Platform Technology Stack
version: V1.0
status: Draft
owner: EAAP Team
created: 2026-07
---

# Enterprise AI Agent Platform

# 技术栈设计文档（Technology Stack）V1.0


---

# 1. 文档说明


## 1.1 文档目的


本文档定义 EAAP 的技术选型方案。


目标：

- 明确技术方向；
- 保证系统一致性；
- 降低技术风险；
- 支撑企业级扩展。


---

# 2. 技术选型原则


EAAP 遵循以下原则：


## 2.1 企业可靠性


优先选择：

- 成熟生态；
- 长期维护；
- 企业应用广泛。


---

## 2.2 AI生态兼容


技术必须支持：

- LLM
- RAG
- Agent
- Workflow
- Multi-Agent


---

## 2.3 开发效率


考虑：

- 学习成本；
- 开发效率；
- 社区资源。


---

## 2.4 可扩展性


支持未来：

- 微服务
- 云部署
- Kubernetes
- 多模型


---

# 3. 技术栈总览


|领域|技术选择|
|-|-|
|Frontend|Vue3 + TypeScript|
|Build Tool|Vite|
|Package Manager|pnpm|
|Backend|FastAPI|
|Language|Python|
|Python Package Manager|uv|
|Database|PostgreSQL|
|Cache|Redis|
|Vector Database|Qdrant|
|Agent Framework|LangGraph|
|LLM Integration|OpenAI Compatible API|
|Container|Docker|
|Deployment|Kubernetes|
|Testing|Playwright + Pytest|
|Code Quality|ESLint + Ruff|


---

# 4. Frontend 技术栈


# 4.1 Vue3


## 选择原因


EAAP 前端采用：

```
Vue3
```


原因：

### 1. 用户已有前端开发经验


当前开发者背景：

- 前端工程师


Vue3 可以最大化已有能力。


---

### 2. 企业应用生态成熟


Vue 在企业后台系统：

- 管理平台；
- 数据平台；
- SaaS系统；

应用广泛。


---

### 3. AI应用开发适合


EAAP前端主要需求：

- Chat UI
- Dashboard
- Workflow Designer
- Agent Builder


Vue3完全满足。


---

# 4.2 TypeScript


## 作用


提高大型项目：

- 类型安全；
- 可维护性；
- 重构能力。


---

# 4.3 Vite


## 作用


负责：

- 开发服务器；
- 构建；
- 热更新。


选择原因：

- 速度快；
- Vue官方生态；
- 配置简单。


---

# 4.4 pnpm


## 作用


管理前端依赖。


选择原因：

- 高性能；
- 节省磁盘；
- 支持Monorepo。


---

# 5. Backend 技术栈


# 5.1 Python


## 选择原因


AI领域主要生态：

```
Python

↓

LLM

↓

RAG

↓

Agent

```


优势：

- 丰富AI库；
- 快速开发；
- 社区成熟。


---

# 5.2 FastAPI


## 作用


提供后端API服务。


---

## 选择原因


### 高性能


基于：

- ASGI
- asyncio


---

### AI生态友好


容易集成：

- LangChain
- LangGraph
- OpenAI SDK


---

### 开发效率高


支持：

- 自动API文档；
- 类型检查；
- 异步。


---

# 5.3 uv


## 作用


Python项目管理工具。


负责：

- Python版本管理；
- 依赖管理；
- 虚拟环境。


---

## 为什么不用传统pip


pip：

- 依赖解析较慢；
- 项目管理能力较弱。


uv：

- 更快；
- 现代Python项目管理方案。


---

# 6. AI技术栈


# 6.1 LLM Gateway


## 目标


统一管理大模型访问。


架构：

```
Application

↓

LLM Gateway

↓

Model Provider

```


---

支持：

- OpenAI
- Claude
- Gemini
- 国产大模型


例如：

- 通义千问
- DeepSeek
- 智谱


---

# 6.2 LangGraph


## 作用


Agent流程编排框架。


---

## 选择原因


支持：

- State管理；
- Agent Workflow；
- Multi-Agent。


---

架构：

```
State

↓

Graph

↓

Node

↓

Edge

```


---

# 7. 数据层


# 7.1 PostgreSQL


## 作用


关系型核心数据库。


保存：

- 用户；
- 权限；
- Agent配置；
- 会话；
- 系统数据。


---

## 选择原因


- 成熟稳定；
- 企业广泛使用；
- 支持复杂查询。


---

# 7.2 Redis


## 作用


高速缓存和状态管理。


保存：

- Session；
- Token；
- 临时任务状态。


---

选择原因：

- 高性能；
- 生态成熟。


---

# 7.3 Qdrant


## 作用


向量数据库。


用于：

- Embedding存储；
- 相似度搜索；
- RAG。


---

选择原因：

- 专为向量搜索设计；
- 开源；
- Python生态友好。


---

# 8. 工程化工具


# 8.1 Docker


## 作用


统一开发和部署环境。


例如：

```
Frontend Container

Backend Container

Database Container

Vector DB Container

```


---

# 8.2 Kubernetes


## 使用阶段


不是第一阶段必须。


用于：

生产环境：

- 服务扩展；
- 自动部署；
- 高可用。


---

# 8.3 Git


## 代码管理


采用：

Git Flow 简化版。


分支：

```
main

develop

feature/*
```


---

# 9. 测试体系


# 9.1 Frontend Testing


## Playwright


用于：

End-to-End测试。


测试：

- 登录流程；
- Chat流程；
- Agent操作。


---

## 为什么选择Playwright


相比Cypress：

优势：

- 多浏览器支持；
- 自动等待；
- 更适合企业E2E。


---

# 9.2 Backend Testing


## Pytest


用于：

- 单元测试；
- API测试。


---

# 10. 代码质量体系


# Frontend


工具：

```
ESLint

TypeScript

```


负责：

- 代码规范；
- 类型检查。


---

# Backend


工具：

```
Ruff

Pytest

```


负责：

- Python代码检查；
- 自动测试。


---

# 11. 开发环境


## Frontend


```
Node.js

pnpm

Vue3

TypeScript

```


---

## Backend


```
Python

uv

FastAPI

```


---

## Infrastructure


```
Docker

PostgreSQL

Redis

Qdrant

```


---

# 12. Monorepo设计


EAAP采用：

```
enterprise-ai-agent-platform


├── apps

│   ├── web

│   └── api


├── packages

│
├── docs

└── docker

```


---

优势：

- 统一管理；
- 方便部署；
- 适合企业项目。


---

# 13. 技术演进路线


## MVP阶段


```
Vue3

+

FastAPI

+

PostgreSQL

+

LLM API

```


---

## RAG阶段


增加：

```
Qdrant

Embedding Pipeline

```


---

## Agent阶段


增加：

```
LangGraph

Tool System

Memory

```


---

## Enterprise阶段


增加：

```
Kubernetes

Observability

Multi-Agent

A2A

```


---

# 14. 技术风险


## 风险1：AI技术变化快


解决：

保持模块化：

```
LLM Gateway

Agent Layer

Tool Layer

```


---

## 风险2：Agent复杂度


解决：

分阶段：

```
Chat

↓

RAG

↓

Agent

↓

Multi-Agent

```


---

# 15. 技术栈总结


```
Frontend

Vue3 + TypeScript


Backend

FastAPI + Python


AI

LangGraph + LLM


Knowledge

RAG + Qdrant


Data

PostgreSQL + Redis


DevOps

Docker + Kubernetes


Testing

Playwright + Pytest

```


---

# 16. 后续文档


下一步：

```
ADR/

Environment.md

GitWorkflow.md

CodingStyle.md
```


---

# 版本记录


|版本|日期|说明|
|-|-|-|
|V1.0|2026-07|初始技术栈设计文档|
