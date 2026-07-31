# Enterprise AI Agent Platform (EAAP)

# Milestone 0 Completed Steps

Version: V1.1

Date: 2026-07-31


---

# 1. Document Purpose

本文档记录 EAAP（Enterprise AI Agent Platform）项目 Milestone 0 阶段完整初始化过程。

目标：

建立企业级 AI Agent 平台的基础工程环境，为后续 Agent 平台核心能力开发提供稳定基础。


Milestone 0 完成内容：

- Monorepo 项目结构
- 前端 Vue 开发环境
- 后端 Python + uv + FastAPI 开发环境
- Docker 容器化环境
- PostgreSQL 数据库环境
- Redis 缓存环境
- Qdrant 向量数据库环境
- 本地开发验证流程


完成 Milestone 0 后：

项目具备进入业务功能开发阶段的基础能力。


---

# 2. Development Environment


## Operating System

Windows 10 / Windows 11


## Development Tools


| 工具 | 用途 |
|---|---|
| VS Code / Cursor | 代码编辑 |
| Git | 版本管理 |
| PNPM | JavaScript 包管理 |
| uv | Python 项目管理 |
| Docker Desktop | 容器运行环境 |
| PostgreSQL | 关系型数据库 |
| Redis | 缓存数据库 |
| Qdrant | 向量数据库 |


---

# 3. Project Initialization


## 3.1 Create Project Directory


创建项目目录：

```bash
enterprise-ai-agent-platform
进入项目：

cd enterprise-ai-agent-platform

4. Monorepo Architecture Setup

EAAP 使用 Monorepo 架构管理前后端及公共模块。

最终目录结构：

enterprise-ai-agent-platform

├── apps
│   ├── web
│   └── api
│
├── packages
│
├── scripts
│
├── docker
│
├── docs
│
├── docker-compose.yml
│
├── package.json
│
└── pnpm-workspace.yaml
4.1 Directory Responsibility
apps

存放主要应用。

apps

├── web

└── api
web

Vue 前端应用。

负责：

用户界面
Agent交互界面
管理后台
api

FastAPI 后端应用。

负责：

API接口
Agent服务
数据处理
业务逻辑
packages

存放共享代码。

未来：

packages

├── ui

├── types

└── utils

用途：

公共组件
类型定义
工具函数
scripts

存放自动化脚本。

例如：

初始化脚本
数据库脚本
部署脚本
docs

存放项目文档。

结构：

docs

├── architecture

├── api

├── database

├── deployment

└── development
5. PNPM Workspace Initialization
5.1 Initialize Root Project

在项目根目录执行：

pnpm init

生成：

package.json

作用：

创建 Node.js 项目入口。

5.2 Create pnpm Workspace

创建：

pnpm-workspace.yaml

内容：

packages:
  - apps/*
  - packages/*

作用：

告诉 pnpm：

哪些目录属于当前 Monorepo。

5.3 Install Workspace Dependencies

根目录执行：

pnpm install

作用：

扫描 workspace
安装所有项目依赖
创建依赖链接
生成 lock 文件

生成：

pnpm-lock.yaml

说明：

根目录 install 会管理整个 Monorepo 的依赖版本。

6. Frontend Initialization
6.1 Technology Stack

Frontend:

Vue 3
Vite
TypeScript
PNPM

目录：

apps/web
6.2 Create Vue Project

进入：

cd apps

执行：

pnpm create vite web

选择：

Vue

TypeScript
6.3 Install Dependencies

进入：

cd apps/web

执行：

pnpm install
6.4 Run Frontend

启动：

pnpm dev

访问：

http://localhost:5173

验证：

Vue 页面正常显示。

Frontend 初始化完成。

7. Backend Initialization
Python Backend Technology Stack

Backend:

Python
FastAPI
uv
Uvicorn

目录：

apps/api
7.1 Install uv

uv 是 Python 新一代项目管理工具。

用途：

Python版本管理
虚拟环境管理
依赖管理
快速安装包

安装：

pip install uv

验证：

uv --version
7.2 Initialize Python Project

进入后端目录：

cd apps/api

执行：

uv init

生成：

apps/api

├── pyproject.toml
├── README.md
└── .python-version
7.3 Create Virtual Environment

执行：

uv venv

生成：

apps/api

├── .venv
├── pyproject.toml
└── README.md

说明：

.venv

是当前 FastAPI 项目的独立 Python 环境。

作用：

避免不同项目之间 Python 依赖冲突。

# 7.4 Activate Virtual Environment


Windows PowerShell:

```powershell
.venv\Scripts\activate
成功后：

(.venv)

PS C:\enterprise-ai-agent-platform\apps\api>

说明：

当前终端已经进入项目 Python 虚拟环境。

7.5 Install FastAPI Dependencies

使用 uv 添加依赖。

安装 FastAPI：

uv add fastapi

安装 Uvicorn：

uv add uvicorn

生成：

pyproject.toml

包含：

dependencies = [
    "fastapi",
    "uvicorn"
]
7.6 Create FastAPI Application

创建目录：

apps/api

├── app
│
│   ├── main.py
│   ├── api
│   ├── models
│   ├── services
│   └── core
│
├── .venv
│
├── pyproject.toml
│
└── README.md

创建：

app/main.py

内容：

from fastapi import FastAPI


app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "EAAP API Running"
    }
7.7 Run FastAPI

使用 uv 运行：

uv run uvicorn app.main:app --reload

启动成功：

Uvicorn running on http://127.0.0.1:8000

访问：

http://localhost:8000

返回：

{
    "message": "EAAP API Running"
}

访问 Swagger:

http://localhost:8000/docs

看到 FastAPI API 文档。

Backend 初始化完成。

8. Docker Environment Setup
8.1 Install Docker Desktop

安装：

Docker Desktop
WSL2
Hyper-V（Windows环境）

验证：

docker --version

验证 Compose：

docker compose version
8.2 Docker Concepts
Image

镜像（Image）：

应用运行模板。

例如：

postgres:16

redis:7

qdrant/qdrant

Image 不是真正运行的服务。

Container

容器（Container）：

Image 的运行实例。

关系：

Image

  |

  ↓

Container

例如：

postgres image

        |

        ↓

postgres container
Volume

Volume：

用于保存持久化数据。

例如：

PostgreSQL Container

        |

        ↓

postgres_data Volume

作用：

即使删除 Container：

数据仍然存在。

Network

Docker Network：

用于容器之间通信。

例如：

web

 |

api

 |

postgres

 |

redis

 |

qdrant
9. Docker Compose Setup

创建：

docker-compose.yml

作用：

统一管理多个 Container。

包含：

PostgreSQL
Redis
Qdrant

启动：

docker compose up -d

含义：

根据 compose 文件创建 Container
如果没有 Image，则拉取 Image
创建 Network
创建 Volume
后台启动服务

查看状态：

docker compose ps

停止：

docker compose down

说明：

删除 Container：

不会删除 Volume。

10. PostgreSQL Setup
10.1 PostgreSQL Service

版本：

PostgreSQL 16

用途：

存储：

用户数据
企业组织数据
Agent配置
工作流数据
系统数据
10.2 Connect PostgreSQL

执行：

docker compose exec postgres psql -U eaap

进入：

# eaap=#


表示：

成功进入 PostgreSQL CLI。

10.3 Check Database

执行：

\l

查看数据库。

结果：

eaap

postgres

template0

template1

说明：

PostgreSQL 初始化成功。

10.4 PostgreSQL CRUD Verification

验证：

创建表：

CREATE TABLE test_table(
    id SERIAL PRIMARY KEY,
    name VARCHAR(50)
);

插入：

INSERT INTO test_table(name)
VALUES('EAAP');

查询：

SELECT * FROM test_table;

验证数据库读写正常。

10.5 PostgreSQL Persistence

查看 Volume：

docker volume ls

确认：

postgres_data

说明：

数据库数据已经持久化。

即使：

docker compose down

重新启动：

docker compose up -d

数据仍然存在。

11. Redis Setup
11.1 Redis Service

版本：

Redis 7

用途：

Session
Cache
Agent状态
临时任务数据
11.2 Connect Redis

执行：

docker compose exec redis redis-cli

进入：

127.0.0.1:6379>
11.3 Redis Verification

测试连接：

ping

返回：

PONG

写入：

set eaap_status running

读取：

get eaap_status

返回：

running

TTL测试：

set temp_key hello EX 10

10秒后自动删除。

Redis验证完成。

# 12. Qdrant Setup


## 12.1 Qdrant Service


版本：

```text
Qdrant Latest

用途：

Qdrant 是 EAAP 的向量数据库。

主要用于：

企业知识库
RAG 检索
Agent Memory
Semantic Search
12.2 Qdrant API Verification

Qdrant 默认端口：

6333

访问：

http://localhost:6333

健康检查：

http://localhost:6333/healthz

返回：

healthz check passed

说明：

Qdrant 服务正常。

12.3 Create Test Collection

创建测试 Collection：

eaap_test_collection

使用 API：

Invoke-RestMethod `
-Method Put `
-Uri "http://localhost:6333/collections/eaap_test_collection" `
-Headers @{
    "Content-Type"="application/json"
} `
-Body '
{
    "vectors":{
        "size":4,
        "distance":"Cosine"
    }
}'

返回：

{
    "result":true,
    "status":"ok"
}

说明：

Collection 创建成功。

12.4 Verify Collection Configuration

查询：

Invoke-RestMethod `
-Method Get `
-Uri "http://localhost:6333/collections/eaap_test_collection" |
ConvertTo-Json -Depth 10

确认：

{
    "vectors":{
        "size":4,
        "distance":"Cosine"
    }
}

说明：

当前 Collection 支持：

4维向量
Cosine Similarity
12.5 Insert Vector Point

Qdrant 数据结构：

一个 Point 包含：

{
    "id":1,

    "vector":[
        0.1,
        0.2,
        0.3,
        0.4
    ],

    "payload":{
        "text":"EAAP AI Agent Platform"
    }
}

字段说明：

字段	说明
id	唯一编号
vector	Embedding向量
payload	附加数据

插入：

Invoke-RestMethod `
-Method Put `
-Uri "http://localhost:6333/collections/eaap_test_collection/points" `
-Headers @{
    "Content-Type"="application/json"
} `
-Body '
{
    "points":[
        {
            "id":1,
            "vector":[0.1,0.2,0.3,0.4],
            "payload":{
                "text":"EAAP AI Agent Platform"
            }
        }
    ]
}'

返回：

{
    "result":true,
    "status":"ok"
}

说明：

Vector 保存成功。

12.6 Verify Vector Storage

查看 Collection：

Invoke-RestMethod `
-Method Get `
-Uri "http://localhost:6333/collections/eaap_test_collection" |
ConvertTo-Json -Depth 10

结果：

{
    "points_count":1
}

说明：

Collection 已保存一个 Point。

12.7 Understanding indexed_vectors_count

查询结果：

{
    "points_count":1,

    "indexed_vectors_count":0
}

原因：

Qdrant 默认：

indexing_threshold = 10000

当前：

1 vector < 10000

因此：

Qdrant 暂时不会建立 HNSW 索引。

这是正常行为。

points_count

表示：

数据库中保存的数据数量。

例如：

points_count = 1

代表：

存在一个 Point。

indexed_vectors_count

表示：

已经进入向量索引的数据数量。

大型生产环境：

例如：

1000000 vectors

indexed_vectors_count:

1000000
12.8 Vector Similarity Search

测试搜索：

Invoke-RestMethod `
-Method Post `
-Uri "http://localhost:6333/collections/eaap_test_collection/points/search" `
-Headers @{
    "Content-Type"="application/json"
} `
-Body '
{
    "vector":[0.1,0.2,0.3,0.4],
    "limit":3
}' |
ConvertTo-Json -Depth 10

返回：

{
    "result":[
        {
            "id":1,
            "score":1,
            "payload":{
                "text":"EAAP AI Agent Platform"
            }
        }
    ]
}

说明：

Qdrant 向量搜索能力正常。

12.9 Qdrant RAG Flow Explanation

未来 EAAP 知识库流程：

用户上传文档

        |

        ↓

Document Parser

        |

        ↓

Text Chunk

        |

        ↓

Embedding Model

        |

        ↓

Vector

        |

        ↓

Qdrant


-------------------


用户问题

        |

        ↓

Question Embedding

        |

        ↓

Qdrant Similarity Search

        |

        ↓

相关知识

        |

        ↓

LLM

        |

        ↓

最终回答
12.10 Cleanup Test Data

删除测试 Collection：

Invoke-RestMethod `
-Method Delete `
-Uri "http://localhost:6333/collections/eaap_test_collection"

返回：

{
    "result":true,
    "status":"ok"
}

确认：

Invoke-RestMethod `
-Method Get `
-Uri "http://localhost:6333/collections"

结果：

{
    "collections":[]
}

测试环境清理完成。

13. Infrastructure Final Verification

查看 Docker 服务：

docker compose ps

应该包含：

服务	状态
PostgreSQL	Running
Redis	Running
Qdrant	Running

查看 Volume：

docker volume ls

确认：

postgres_data

qdrant_data

存在。

14. Milestone 0 Final Status
Milestone 0

Engineering Foundation

Status:

Completed

Completed Items
模块	状态
Repository Initialization	✅
Monorepo Architecture	✅
PNPM Workspace	✅
Vue Frontend	✅
Python Backend	✅
uv Environment	✅
FastAPI Setup	✅
Docker Environment	✅
Docker Compose	✅
PostgreSQL	✅
Redis	✅
Qdrant	✅
Persistence	✅
Infrastructure Verification	✅
15. Current EAAP Architecture
Enterprise AI Agent Platform


                Frontend

                  Vue3

                    |

                    |

                FastAPI API

                    |

        ----------------------------

        |             |            |

   PostgreSQL      Redis       Qdrant


    Business      Cache       Vector

     Data                    Database

16. Next Milestone
Milestone 0.6

Development Workflow Setup

目标：

建立企业级开发流程。

计划：

根目录统一启动脚本
pnpm scripts
FastAPI开发规范
环境变量管理
Git Workflow
Development Documentation

最终目标：

pnpm dev

启动：

Vue Web

+

FastAPI API

+

Docker Infrastructure

EAAP Milestone 0 Completed.


第三部分完成。

这版文档已经覆盖了之前遗漏的：

✅ uv 安装  
✅ uv init  
✅ uv venv  
✅ FastAPI 初始化  
✅ Docker概念  
✅ Docker Compose  
✅ PostgreSQL  
✅ Redis  
✅ Qdrant  
✅ RAG流程  
✅ 验收状态  

下一步进入 **Milestone 0.6 Development Workflow Setup**。