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

sqlalchemy asyncpg alembic psycopg2-binary的详细使用说明请参考：[03-Database.md](03-Database.md)

Step 1.2 创建 Pydantic Schema Layer
目标

建立：

apps/api/app/schemas
│
└── user.py

Schema 层负责：

Request JSON
      |
      ↓
Pydantic Schema
      |
      ↓
Service
      |
      ↓
SQLAlchemy Model
      |
      ↓
Database

不要让 API 直接暴露数据库 Model。

-Pydantic Schema:用 Pydantic 的 BaseModel 定义的数据结构，用来描述、校验和转换 API 的请求/响应 JSON。
Request JSON → Pydantic Schema → Service → SQLAlchemy Model → Database

Step 1.3 创建 Repository Layer
目标

实现数据库访问层。

apps/api/app

├── core
│   ├── config.py
│   ├── database.py
│   └── dependencies.py        ← 新增
├── repositories              ← 新增
│   ├── __init__.py
│   └── user_repository.py


架构：

API Router
    |
    ↓
Service Layer
    |
    ↓
Repository Layer
    |
    ↓
SQLAlchemy
    |
    ↓
PostgreSQL


Repository 专门负责：

"怎么从数据库拿数据"

Service 专门负责：

"业务逻辑是什么"

Step 1.4 Service Layer

目标：

建立：

API
 |
 ↓
Service Layer
 |
 ↓
Repository Layer
 |
 ↓
Database

cd apps/api/app
创建：
services/__init__.py

services/user_service.py

Step 1.5：API Router
把内部代码暴露成真正 HTTP API。
目标：

实现：

POST /api/v1/users

GET /api/v1/users/{id}

最终：

打开：

http://localhost:8000/docs

看到：

Users

POST /api/v1/users

GET /api/v1/users/{user_id}

并可以直接测试。


进入：

cd apps/api/app

创建routers/users.py

结构：

app

├── routers
│   ├── __init__.py
│   └── users.py