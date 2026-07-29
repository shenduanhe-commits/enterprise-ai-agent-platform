---
title: Enterprise AI Agent Platform Coding Style
version: V1.0
status: Draft
owner: EAAP Team
created: 2026-07
---

# Enterprise AI Agent Platform

# 代码规范文档（Coding Style）V1.0


---

# 1. 文档说明


## 1.1 文档目的


定义 EAAP 项目的代码开发规范。


目标：

- 提高代码可读性；
- 保证代码质量；
- 降低维护成本；
- 方便多人协作。


---

# 2. 通用原则


## 2.1 可读性优先


代码应该：

容易理解

优先于：

极致优化。


---

## 2.2 简单优先


避免：

- 过度设计；
- 无意义抽象；
- 复杂继承。


---

## 2.3 单一职责


一个模块：

只负责一类事情。


例如：


不好：

```
user_service.py

包含：

用户管理
邮件发送
AI调用
文件处理
```


好：

```
user_service.py

email_service.py

ai_service.py

```


---

# 3. Frontend代码规范


技术：

```
Vue3

+

TypeScript

+

Composition API

```


---

# 3.1 Vue组件规范


组件命名：

使用：

PascalCase


正确：

```
ChatWindow.vue

AgentCard.vue

KnowledgeList.vue
```


错误：

```
chatwindow.vue

chat-window.vue
```


---

# 3.2 组件结构


推荐：


```vue
<script setup lang="ts">

</script>


<template>

</template>


<style scoped>

</style>
```


---

# 3.3 Component职责


一个组件：

只处理一种UI职责。


例如：


```
ChatMessage.vue


负责：

显示消息


不负责：

调用API

处理权限

```


---

# 3.4 状态管理


使用：

```
Pinia
```


管理：

- 用户状态
- 会话状态
- Agent状态


---

# 3.5 API调用规范


禁止：

组件内直接请求。


错误：

```ts
axios.get("/api/chat")
```


推荐：

```
component

↓

service

↓

api

```


例如：

```
src/api/chat.ts

```


---

# 4. TypeScript规范


---

# 4.1 类型必须明确


避免：

```ts
let data:any
```


推荐：

```ts
interface User {
 name:string
 age:number
}
```


---

# 4.2 命名规范


变量：

camelCase


例如：

```ts
userName
agentList
```


类型：

PascalCase


例如：

```ts
AgentConfig
UserInfo
```


---

# 5. Backend代码规范


技术：

```
Python

+

FastAPI

```


---

# 5.1 项目结构


推荐：


```
app


├── api

├── services

├── models

├── schemas

├── repositories

├── agents

├── tools

└── core

```


---

# 5.2 分层原则


API层：

负责：

请求处理。


Service层：

负责：

业务逻辑。


Repository层：

负责：

数据访问。


例如：

```
API

↓

Service

↓

Repository

↓

Database

```


---

# 5.3 Python命名规范


变量：

snake_case


例如：

```python
user_name
agent_config
```


类：

PascalCase


例如：

```python
AgentRuntime
ChatService
```


函数：

snake_case


例如：

```python
create_agent()
```


---

# 5.4 类型提示


必须使用：

Type Hint


例如：


```python
def create_agent(
    name: str
) -> Agent:
    pass
```


---

# 6. FastAPI规范


## Router


只处理：

HTTP。


例如：

```
routers/chat.py

```


---

## Service


处理：

业务。


例如：

```
services/chat_service.py

```


---

## Schema


定义：

请求响应。


例如：

```
schemas/chat.py

```


---

# 7. AI代码规范


EAAP特殊规范。


---

# 7.1 Prompt不能写死


错误：

```python
prompt="你是一个助手"
```


推荐：


```
prompts/

├── chat.md

├── analyst.md

└── researcher.md

```


---

# 7.2 Agent配置数据化


不要：

```python
if agent=="sales":
```


推荐：

数据库配置：

```
Agent

|

Prompt

|

Tools

|

Memory

```


---

# 7.3 Tool必须独立


例如：

```
tools/


├── search.py

├── database.py

└── email.py

```


---

# 7.4 Agent执行必须可追踪


记录：

- 输入
- 思考步骤状态
- Tool调用
- 输出


用于：

- Debug
- Evaluation


---

# 8. API设计规范


采用：

REST API。


---

# URL规范


正确：

```
GET /api/v1/agents

POST /api/v1/chat

```


错误：

```
GET /getAgents
```


---

# 返回格式


统一：


```json
{
 "success": true,
 "data": {},
 "message": ""
}
```


---

# 错误处理


统一错误码。


例如：

```
AUTH_001

AGENT_001

RAG_001

```


---

# 9. 数据库规范


表名：

snake_case


例如：

```
user_accounts

agent_configs

chat_messages

```


---

字段：

snake_case


例如：

```
created_at

updated_at

```


---

# 10. Git提交规范


遵循：

Conventional Commits


格式：


```
type(scope): message
```


例如：


```
feat(agent): add tool calling

fix(chat): fix streaming bug

```


---

# 11. AI辅助开发规范


EAAP允许使用：

- Cursor
- ChatGPT
- Codex


但是：


AI生成代码必须：

经过：

```
Review

↓

Test

↓

Commit

```


---

# 12. 测试要求


新增功能必须包含：


Backend:

```
pytest

```


Frontend:

```
Playwright

```


---

# 13. Code Review检查项


检查：

## 架构

是否符合：

- System Architecture
- ADR


## 代码

是否：

- 易读
- 可维护
- 有测试


## AI模块

是否：

- Prompt可管理
- Agent行为可追踪


---

# 14. 总结


EAAP代码原则：


```
Readable

Maintainable

Testable

Scalable

AI-Native

```


---

# 15. 后续文档


下一步：

```
TestingStrategy.md

Deployment.md

SecurityDesign.md

```

---

# Revision


|版本|日期|说明|
|-|-|-|
|V1.0|2026-07|初始代码规范|