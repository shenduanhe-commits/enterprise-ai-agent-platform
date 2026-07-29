---
title: Enterprise AI Agent Platform Git Workflow
version: V1.0
status: Draft
owner: EAAP Team
created: 2026-07
---

# Enterprise AI Agent Platform

# Git 工作流规范（Git Workflow）V1.0


---

# 1. 文档说明


## 1.1 文档目的


定义 EAAP 项目的 Git 使用规范。


目标：

- 保证代码质量；
- 支持多人协作；
- 保持提交历史清晰；
- 接近企业研发流程。


---

# 2. Git工作流选择


EAAP采用：

```
Simplified Git Flow
```


原因：

传统 Git Flow：

```
develop

release

hotfix

feature
```

对于早期项目较复杂。


EAAP采用简化版本：

```
main

↓

develop

↓

feature/*
```

---

# 3. 分支设计


## 3.1 main


用途：

生产稳定版本。


规则：

禁止直接提交。


只接受：

```
develop merge

release merge

```


---

示例：

```
main

|

v1.0.0

```


---

# 3.2 develop


用途：

开发集成分支。


所有功能完成后：

合并到：

```
develop
```


---

# 3.3 feature


用途：

开发新功能。


命名：

```
feature/<name>
```


例如：


```
feature/chat-ui

feature/rag-service

feature/agent-runtime

```


---

# 3.4 bugfix


修复普通问题。


命名：

```
bugfix/<name>
```


例如：

```
bugfix/login-error

```


---

# 3.5 hotfix


生产紧急修复。


命名：

```
hotfix/<name>
```


---

# 4. Feature开发流程


标准流程：


```
Create Issue


↓

Create Branch


↓

Development


↓

Test


↓

Commit


↓

Pull Request


↓

Review


↓

Merge

```


---

# 5. 示例流程


需求：

增加AI Chat Streaming功能。


---

创建Issue：

```
ISSUE-001

Implement Chat Streaming

```


---

创建分支：

```bash
git checkout develop

git checkout -b feature/chat-streaming
```


---

开发完成：


提交：

```bash
git add .

git commit -m "feat(chat): add streaming response"
```


---

推送：

```bash
git push origin feature/chat-streaming
```


---

创建：

Pull Request


目标：

```
feature/chat-streaming

↓

develop

```


---

# 6. Commit规范


EAAP采用：

Conventional Commits


格式：


```
type(scope): description
```


---

# 7. Commit类型


## feat


新增功能。


例如：

```
feat(agent): add tool calling
```


---

## fix


修复Bug。


例如：

```
fix(auth): fix token expired issue
```


---

## docs


文档修改。


例如：

```
docs(prd): update user story
```


---

## refactor


重构。


例如：

```
refactor(api): simplify service layer
```


---

## test


测试。


例如：

```
test(chat): add api tests
```


---

## chore


工程配置。


例如：

```
chore: update dependencies
```


---

# 8. Commit原则


## 一个Commit只做一件事


不好：

```
update files
```


好：

```
feat(rag): add document parser
```


---

## Commit保持可回滚


每次提交：

应该：

- 可以理解；
- 可以撤销。


---

# 9. Pull Request规范


PR必须包含：


## 标题


格式：

```
[type]: description
```


例如：

```
feat: implement knowledge upload
```


---

## 内容


包括：


### 变更内容


```
Added document upload API
```


### 测试方式


```
uv run pytest

```


### 截图


UI修改需要。


---

# 10. Code Review规范


Review关注：


## 代码质量


检查：

- 命名
- 结构
- 可维护性


---

## 架构一致性


确认：

是否符合：

- System Architecture
- ADR


---

## 安全


检查：

- 权限
- 数据泄露
- API安全


---

# 11. Tag规范


版本使用：

Semantic Versioning


格式：

```
MAJOR.MINOR.PATCH
```


例如：

```
v0.1.0

v0.2.0

v1.0.0

```


---

# 12. Release流程


流程：


```
develop

↓

Release Candidate

↓

Test

↓

main

↓

Tag

↓

Deploy

```


---

# 13. EAAP版本规划


## v0.1.0


工程初始化。


包含：

- Monorepo
- Docker
- CI基础


---

## v0.2.0


AI Chat。


包含：

- Chat UI
- LLM API


---

## v0.3.0


RAG。


包含：

- Knowledge Base
- Vector Search


---

## v0.4.0


Agent。


包含：

- Agent Runtime
- Tool Calling


---

## v1.0.0


Enterprise AI Agent Platform。


包含：

- Multi-Agent
- Workflow
- A2A


---

# 14. Git目录规范


项目：

```
enterprise-ai-agent-platform

```


Git管理：

```
.git

.github

.gitignore

```


---

# 15. 后续自动化


未来增加：


## CI


自动执行：

```
Lint

Test

Build

```


---

## CD


自动部署：

```
Docker Image

↓

Environment

↓

Production

```


---

# 16. 总结


EAAP Git流程：


```
Issue

↓

Feature Branch

↓

Commit

↓

Pull Request

↓

Review

↓

Develop

↓

Release

↓

Main

```


---

# 17. 后续文档


下一步：

```
CodingStyle.md

TestingStrategy.md

Deployment.md

```

---

# Revision


|版本|日期|说明|
|-|-|-|
|V1.0|2026-07|初始Git工作流规范|
