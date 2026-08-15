# Git 工作流 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/03-development/GitWorkflow.md`、根目录 `GIT_WORKFLOW.md` |

---

## 1. 模型

简化 Git Flow，单人项目够用：

```
main          可演示的稳定点
feature/*     日常开发
```

需要时再加 `develop`。不要为仪式开一堆长期分支。

功能分支按阶段命名：

```
feature/r0-runtime-hardening
feature/r1-auth-sse
feature/r2-langgraph
feature/r3-rag
```

---

## 2. 约定

- 从最新 `main` 拉功能分支。
- 提交：`type(scope): message`（见 CodingStyle）。
- 不把 `.env`、密钥、`__pycache__`、`node_modules` 提交进去。
- 不强制 `--no-verify`。
- 文档只改 `docs/v2/` 与根 `DOCUMENTATION.md`，不回写 V1。

---

## 3. 与计划同步

一个功能分支应对一个 R 阶段内的故事，不要一个 PR 里同时上 LangGraph 和 RAG。

合并前：`uv run pytest` 通过；`STATUS.md` 如阶段完成则更新。
