# ADR-001 为什么用 FastAPI

| 项 | 内容 |
| --- | --- |
| 状态 | Accepted |
| 日期 | 2026-08-15 |
| 替代 | V1 ADR-002 |

## 背景

后端需要 async LLM 调用、OpenAPI、与 Python AI 生态共存。

## 决策

使用 FastAPI + Uvicorn + Pydantic v2。

## 原因

- 原生 async，适合 SSE 与并发工具调用。
- `/docs` 即演示面，符合「前端是壳」。
- Agent / LangGraph / MCP 官方示例以 Python 为主。
- 仓库已经落地分层，迁移成本为零。

## 不选

- Django：同步历史重，不适合本阶段。
- Flask：生态可以，但类型与 OpenAPI 弱于 FastAPI。
- 纯 Node 后端：与 LangGraph/MCP Python 主生态错位；你转的是 Agent 岗不是换前端栈。
