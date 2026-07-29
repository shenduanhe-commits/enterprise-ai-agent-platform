Enterprise AI Agent Platform
API接口设计文档 V1.0

版本：V1.0

技术：

REST API
WebSocket / SSE Streaming
JSON

后端：

FastAPI

1. API整体架构

系统 API 分为：

/api

├── auth              用户认证

├── users             用户管理

├── chat              AI聊天

├── conversations     对话管理

├── knowledge         知识库

├── agents            Agent管理

├── tasks             任务管理

├── tools             工具调用

└── admin             管理后台

2. API基础规范
Base URL

开发环境：

http://localhost:8000/api/v1

生产环境：

https://ai.company.com/api/v1
2.1 请求格式

Header：

Content-Type: application/json

Authorization: Bearer token
2.2 返回格式

统一：

{
    "code":0,
    "message":"success",
    "data":{}
}

错误：

{
    "code":40001,
    "message":"permission denied",
    "data":null
}
3. 用户认证 API
3.1 用户登录
POST
/auth/login

请求：

{
    "email":"user@test.com",
    "password":"123456"
}

返回：

{
    "token":"xxxxx",
    "user":{
        "id":1,
        "name":"张三",
        "role":"employee"
    }
}
3.2 获取当前用户
GET
/auth/me

返回：

{
    "id":1,
    "name":"张三",
    "department":"销售部"
}
4. AI Chat API ⭐

这是系统第一阶段核心。

4.1 创建聊天
POST
/chat/completions

请求：

{
    "conversation_id":null,
    "message":"查询A100产品信息"
}

后端流程：

用户输入

↓

FastAPI

↓

Supervisor Agent

↓

LLM

↓

返回结果


返回：

{
    "answer":
    "A100产品交付周期为4周"
}
4.2 Streaming流式输出

企业 AI 产品必须支持。

接口：

POST /chat/stream

方式：

SSE

流程：

用户

↓

AI开始思考

↓

逐字返回

↓

完成


返回：

data:
正在查询知识库...


data:
找到相关资料...


data:
A100交付周期为4周

4.3 上传文件聊天

接口：

POST /chat/file

场景：

用户：

上传 PDF

询问：

总结这个文件

请求：

multipart/form-data

参数：

file

question

5. 会话管理 API
5.1 获取历史会话

GET

/conversations

返回：

[
 {
  "id":1,
  "title":"产品查询"
 }
]
5.2 获取会话详情

GET

/conversations/{id}

返回：

{
"id":1,

"messages":[

{
"role":"user",
"content":"查询产品"
},

{
"role":"assistant",
"content":"结果..."
}

]

}
5.3 删除会话

DELETE

/conversations/{id}
6. 知识库 API（RAG）
6.1 上传知识文档

POST

/knowledge/documents

请求：

文件上传：

manual.pdf

返回：

{
"id":100,

"status":"processing"
}
6.2 获取文档列表

GET

/knowledge/documents

返回：

[
{
"id":1,
"name":"产品说明书.pdf",
"status":"completed"
}
]
6.3 删除文档

DELETE

/knowledge/documents/{id}
6.4 查询知识库状态

GET

/knowledge/status

返回：

{
"documents":100,

"chunks":5000,

"status":"healthy"
}
7. Agent API ⭐⭐⭐

用于管理 Agent。

7.1 创建 Agent任务

POST

/agents/tasks

请求：

{
"message":
"生成客户拜访报告"
}

返回：

{
"task_id":1001,

"status":"running"
}
7.2 查询任务状态

GET

/agents/tasks/{task_id}

返回：

{
"id":1001,

"status":"completed",

"steps":[

{
"agent":"KnowledgeAgent",
"status":"success"
},

{
"agent":"DocumentAgent",
"status":"success"
}

]

}
7.3 获取 Agent 执行轨迹

GET

/agents/tasks/{id}/trace

返回：

[
{
"agent":"Supervisor",

"action":
"select KnowledgeAgent"
},

{
"agent":"KnowledgeAgent",

"action":
"search vector database"
}

]
8. Tool Calling API

Agent调用企业能力。

8.1 获取工具列表

GET

/tools

返回：

[
{
"name":"order_query",

"description":
"查询订单"
}
]
8.2 执行工具

POST

/tools/{tool_name}/execute

例如：

/tools/order_query/execute

请求：

{
"order_id":"10001"
}

返回：

{
"status":"shipped",

"date":"2026-08-01"
}
9. 管理后台 API
9.1 用户管理

GET

/admin/users

POST

/admin/users

DELETE

/admin/users/{id}
9.2 权限管理

GET

/admin/roles

返回：

[
"admin",

"manager",

"employee"
]
10. Agent内部接口设计

内部服务：

backend

↓

agent-service

↓

agents


接口：

Agent执行
execute(
    task,
    context
)

输入：

{
"task":
"查询产品信息",

"context":
{
"user_id":1
}
}

输出：

{
"result":
"产品信息",

"trace":[]
}
11. Phase 1实际开发 API

第一阶段只实现：

用户
POST /auth/login
Chat
POST /chat/completions

POST /chat/stream
会话
GET /conversations

GET /conversations/{id}

数据库：

只需要：

users

conversations

messages

12. 后续扩展路线
Phase 2

增加：

knowledge/*

实现：

RAG知识库。

Phase 3

增加：

agents/*

实现：

Agent Workflow。

Phase 4

增加：

tools/*

实现：

企业系统连接。

Phase 5

增加：

a2a/*

实现：

Multi-Agent通信。