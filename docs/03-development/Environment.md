---
title: Enterprise AI Agent Platform Development Environment
version: V1.0
status: Draft
owner: EAAP Team
created: 2026-07
---

# Enterprise AI Agent Platform

# 开发环境规范（Development Environment）V1.0


---

# 1. 文档说明


## 1.1 文档目的


本文档定义 EAAP 项目统一开发环境。


目标：

- 保证开发环境一致；
- 降低环境问题；
- 支撑团队协作；
- 支持后续 CI/CD。


---

# 2. 开发环境总览


EAAP 采用前后端分离架构。


整体环境：


```
Developer Machine


├── Frontend

│
├── Backend

│
├── Database

│
├── AI Services

│
└── Infrastructure

```


---

# 3. 操作系统


## 推荐环境


开发阶段：

```
Windows 11

+
WSL2

```


或者：

```
macOS

```


---

# 4. 编辑器


## 推荐


```
Cursor

或

VS Code

```


---

# 4.1 VS Code


适合：

- 企业开发
- 插件生态
- 稳定性


---

# 4.2 Cursor


适合：

- AI辅助开发
- 代码生成
- 项目理解


EAAP 推荐：

```
Cursor作为主编辑器

VS Code作为兼容环境

```


原因：

项目目标本身就是 AI 应用开发。

需要充分利用 AI Coding。


---

# 5. Frontend环境


## 5.1 Node.js


版本：

```
Node.js >= 22
```


检查：

```bash
node -v
```


---

## 5.2 pnpm


安装：


```bash
npm install -g pnpm
```


检查：

```bash
pnpm -v
```


---

## 5.3 Vue环境


技术：

```
Vue3

+

TypeScript

+

Vite

```


---

# 6. Backend环境


## 6.1 Python


版本：

```
Python >= 3.12
```


检查：

```bash
python --version
```


---

# 6.2 uv


EAAP使用：

```
uv
```


作为Python项目管理工具。


检查：

```bash
uv --version
```


示例：

```
uv 0.11.30
```


---

# 6.3 创建Python环境


进入：

```
apps/api
```


执行：


```bash
uv sync
```


生成：

```
.venv

```


---

# 7. Docker环境


## 作用


管理：

- PostgreSQL
- Redis
- Qdrant


---

检查：

```bash
docker --version
```


---

Docker Compose：

```bash
docker compose version
```


---

# 8. 数据库环境


## PostgreSQL


用途：

业务数据。


保存：

- 用户
- 权限
- Agent配置
- 会话


---

## Redis


用途：

缓存和状态。


保存：

- Session
- Agent状态


---

## Qdrant


用途：

向量数据库。


保存：

- Embedding
- Knowledge


---

# 9. Git环境


## Git版本


要求：

```
Git >= 2.40
```


检查：

```bash
git --version
```


---

# 10. Git配置


设置用户名：

```bash
git config --global user.name "your-name"
```


设置邮箱：

```bash
git config --global user.email "your-email"
```


---

# 11. 项目目录结构


EAAP采用：


```
enterprise-ai-agent-platform


├── apps

│
│── web

│
└── api


├── packages


├── docs


├── docker


├── scripts


└── README.md

```


---

# 12. Frontend启动流程


进入：

```bash
cd apps/web
```


安装：

```bash
pnpm install
```


启动：

```bash
pnpm dev
```


---

# 13. Backend启动流程


进入：

```bash
cd apps/api
```


安装：

```bash
uv sync
```


启动：

```bash
uv run fastapi dev
```


---

# 14. Docker服务启动


启动基础设施：


```bash
docker compose up -d
```


启动：

```
PostgreSQL

Redis

Qdrant

```


---

# 15. 推荐开发插件


## Cursor / VS Code


推荐：


### Frontend


```
Vue Language Features

ESLint

Prettier

TypeScript Vue Plugin

```


---

### Backend


```
Python

Pylance

Ruff

```


---

### Docker


```
Docker

```


---

### Git


```
GitLens

```


---

# 16. 环境检查


项目提供：


```
scripts/check-env

```


检查：


```
Node

pnpm

Python

uv

Docker

Git

```


---

# 17. 开发规范


## 不直接修改main


流程：

```
main

↓

develop

↓

feature branch

```


---

## 提交代码前


必须：

- 格式检查
- 测试通过


---

# 18. CI/CD准备


未来：

```
Git Push

↓

CI

↓

Test

↓

Build

↓

Deploy

```


---

# 19. 当前开发环境总结


|类别|工具|
|-|-|
|Editor|Cursor / VS Code|
|Frontend|Vue3 + TypeScript|
|Package|pnpm|
|Backend|Python|
|Python Manager|uv|
|Framework|FastAPI|
|Database|PostgreSQL|
|Cache|Redis|
|Vector DB|Qdrant|
|Container|Docker|
|Testing|Playwright + Pytest|


---

# 20. 后续文档


下一步：

```
GitWorkflow.md

CodingStyle.md

TestingStrategy.md

```


---

# 版本记录


|版本|日期|说明|
|-|-|-|
|V1.0|2026-07|初始开发环境规范|
