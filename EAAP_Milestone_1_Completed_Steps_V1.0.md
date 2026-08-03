# Enterprise AI Agent Platform (EAAP)

# Milestone 1 Completed Steps

Version: V1.0

Date: 2026-07-31

---

# 1. Document Purpose

本文档记录 EAAP（Enterprise AI Agent Platform）项目 Milestone 1 阶段完整初始化过程。

目标：

完成一个 最小可运行的企业级 AI Agent 平台核心版本（MVP Core）。

最终效果：

用户可以：

注册登录
创建 Agent
配置 Agent 使用的模型
给 Agent 分配工具
发起任务
Agent 调用模型和工具完成任务
保存执行记录和上下文

最终形成：

```text

                 User
                  |
                  |
              Web Console
                  |
                  |
              FastAPI API
                  |
                  |
          Agent Runtime Core
                  |
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼

    Model     Tool      Memory
   Gateway   System    System

        │
        │
        ▼

 PostgreSQL
 Redis
 Qdrant

 ```


Step 1.1 Backend Architecture Refinement
目标

把当前 FastAPI 改造成企业后端架构。

学习：

FastAPI 项目架构
分层设计
Dependency Injection

具体操作顺序：

1.1.1 安装依赖

uv add sqlalchemy asyncpg alembic psycopg2-binary

-SQLAlchemy ：数据库工具库，用 Python 对象和 API 管理数据库，定义模型、读写数据

-asyncpg： Python 里连接 PostgreSQL 的异步驱动。

-alembic：SQLAlchemy 配套的 数据库迁移工具。用版本化脚本 管理表结构变化——记录并应用 schema 变更。

asyncpg 负责异步访问 PostgreSQL；SQLAlchemy 用模型定义表结构，用 Session 做增删改查。Alembic 记录并应用 schema 变更。

-psycopg2-binary:Postgres 的同步驱动，搭配alembic使用

1.1.2调整 apps/api/app 目录结构

py文件的代码此处就不展示了

apps/api

└── app

    ├── main.py

    │
    ├── core
    │   ├── __init__.py
    │   ├── config.py +
    │   ├── database.py +
    │   ├── logging.py +
    │   └── lifespan.py +
    │
    ├── api
    │   ├── __init__.py
    │   └── v1
    │       ├── __init__.py
    │       └── health.py
    │
    ├── models
    │   ├── __init__.py
    │   ├── base.py +
    │   └── user.py +
    │
    ├── schemas
    │   └── __init__.py
    │
    ├── services
    │   └── __init__.py
    │
    ├── repositories
    │   └── __init__.py
    │
    └── agents
        └── __init__.py


1.1.3 Alembic 数据库迁移初始化

cd apps/api

uv run alembic init alembic

成功后：
apps/api

├── alembic
│
├── alembic.ini
│
└── app

sqlalchemy asyncpg alembic psycopg2-binary的详细使用说明请参考：EAAP_DATABASE_USE.md


Step 1.2 Database Foundation
目标

建立企业数据层。

技术：

PostgreSQL
SQLAlchemy 2.0
Alembic

完成：

数据库连接：

FastAPI

↓

SQLAlchemy

↓

PostgreSQL

建立基础表：

User

用户

users

id
email
password_hash
created_at
Agent

Agent定义

agents

id
name
description
model
config
created_by
Conversation

对话记录

conversations

id
user_id
agent_id
messages
created_at
Step 1.3 Authentication System
目标

让平台有用户体系。

完成：

注册
POST /auth/register
登录
POST /auth/login

返回：

{
 "access_token":"xxx"
}

实现：

JWT
Password Hash
User Session

学习：

企业 SaaS 基础能力。

Step 1.4 Model Gateway
目标

建立统一模型访问层。

为什么需要？

错误设计：

Agent

↓

OpenAI API

以后换 Claude：

全部修改。

正确：

Agent

↓

Model Gateway

↓

Provider Adapter

↓

OpenAI
Claude
Gemini
Local Model

完成：

统一接口：

class LLMClient:

    async def chat(
        messages
    ):
        pass

支持：

第一阶段：

OpenAI Compatible API

后续：

Claude
Gemini
Ollama
Step 1.5 Agent Runtime Core
目标

实现真正 Agent 执行。

核心：

Agent Runtime

包含：

Agent Definition

例如：

{
"name":"Research Agent",

"role":"分析师",

"tools":[
 "search"
]
}
Task Execution

流程：

Request

↓

Agent Runtime

↓

Planning

↓

Tool Calling

↓

LLM

↓

Response

第一版不追求复杂。

先实现：

Input

↓

LLM

↓

Output

然后逐步增加：

Planning
Reflection
Memory
Step 1.6 Tool System
目标

让 Agent 使用工具。

架构：

Agent

↓

Tool Registry

↓

Tools

├── Search Tool
├── Calculator Tool
├── File Tool
└── API Tool

完成：

Tool接口：

class Tool:

    name:str

    async execute():
        pass

实现第一个：

Calculator Tool

原因：

简单验证 Agent → Tool 调用链。

Step 1.7 Memory System
目标

让 Agent 有上下文。

三层：

Memory

├── Conversation Memory
│
├── User Memory
│
└── Vector Memory

使用：

Redis:

短期状态

PostgreSQL:

历史记录

Qdrant:

语义记忆
Step 1.8 RAG Foundation
目标

让 Agent 可以使用企业知识。

完成：

基础 RAG：

Document

↓

Chunk

↓

Embedding

↓

Qdrant

↓

Retrieve

↓

LLM

支持：

上传：

PDF
Markdown
TXT
Step 1.9 Agent API

最终提供：

创建 Agent
POST /api/v1/agents
执行 Agent
POST /api/v1/agents/{id}/run

请求：

{
"message":
"帮我分析这个文档"
}

返回：

{
"result":
"..."
}
Milestone 1 完成后的能力

完成后 EAAP 将具备：

能力	状态
用户系统	✅
数据库	✅
模型抽象层	✅
Agent运行引擎	✅
工具调用	✅
记忆系统	✅
基础RAG	✅
Agent API	✅