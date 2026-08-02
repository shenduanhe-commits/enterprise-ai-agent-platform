# EAAP Development Guide

## 1. Project Structure


enterprise-ai-agent-platform

├── apps
│ ├── api
│ └── web
│
├── packages
│
├── scripts
│
├── docker
│
└── docs


---

# 2. Requirements

## Frontend

- Node.js
- pnpm


## Backend

- Python
- uv


## Infrastructure

- Docker Desktop


---

# 3. Install Dependencies

## Root

```bash
pnpm install
Backend
cd apps/api

uv sync
4. Start Development
Start Infrastructure
docker compose up -d
Start Frontend + Backend
pnpm dev

Backend:

http://localhost:8000

Frontend:

http://localhost:5173
5. Environment

Copy:

.env.example

to:

.env

Frontend:

apps/web/.env.example

to:

apps/web/.env.development
6. Git Workflow

Branches:

main

develop

feature/*

Feature example:

feature/auth

feature/agent-runtime

feature/rag
7. Commit Convention

Format:

type(scope): message

Examples:

Feature:

feat(agent): add agent executor

Bug fix:

fix(api): fix database connection

Documentation:

docs: update development guide
8. Development Rule

Never commit:

.env

node_modules

.venv

Always commit:

.env.example

package.json

pnpm-lock.yaml

uv.lock

---

## Step 0.6.3.4 创建 Git Workflow 文档

新增：

```text
docs/01-development/GIT_WORKFLOW.md

内容：

# Git Workflow

## Branch Strategy


main

Production stable branch


develop

Development integration branch


feature/*

Feature development


---

## Feature Process


Create:

```bash
git checkout develop

git checkout -b feature/name

Develop:

Commit:

git commit -m "feat(scope): message"

Merge:

feature/*
    |
    v
develop
    |
    v
main
Commit Types

feat

New feature

fix

Bug fix

docs

Documentation

chore

Maintenance

refactor

Code refactoring


---

完成后：

执行：

```powershell
git status

确认新增：

docs/01-development/DEVELOPMENT.md

docs/01-development/GIT_WORKFLOW.md

然后提交：

git add .

git commit -m "docs(workflow): add development and git workflow guides"

