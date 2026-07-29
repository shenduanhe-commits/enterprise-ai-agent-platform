---
title: ADR-005 Why Choose Playwright
version: V1.0
status: Accepted
created: 2026-07
---

# ADR-005

# 为什么 EAAP 选择 Playwright 作为 E2E 测试框架


---

# 1. 状态


Accepted


---

# 2. 背景


EAAP 是企业级 Web 应用。


需要测试：

- 登录流程
- AI Chat流程
- 知识库操作
- Agent配置
- Workflow操作


需要可靠的端到端测试方案。


---

# 3. 候选方案


## Option A

Cypress


优势：

- 使用简单
- 社区成熟


不足：

- 浏览器支持方式有限
- 多页面场景能力较弱


---

## Option B

Playwright


优势：

- 多浏览器支持
- 支持 Chromium / Firefox / WebKit
- 自动等待机制
- 企业应用使用广泛


不足：

- 配置复杂度略高


---

# 4. 决策


选择：

Playwright


作为 EAAP E2E 测试框架。


---

# 5. 原因


## 5.1 企业级测试需求


EAAP需要保证：

```
用户操作

↓

前端

↓

API

↓

AI服务

↓

数据库

```


完整链路正确。


---

## 5.2 多浏览器支持


支持：

- Chrome
- Firefox
- Safari


满足企业环境。


---

## 5.3 适合CI/CD


未来支持：

```
Code Push

↓

GitHub Actions

↓

Playwright Test

↓

Deploy

```


---

# 6. 影响


测试体系：

```
Frontend

↓

Playwright


Backend

↓

Pytest

```


---

# 7. 相关文档


- Technology_Stack.md
- Testing_Strategy.md


---

# Revision


|版本|日期|说明|
|-|-|-|
|V1.0|2026-07|初始决策|
