---
title: ADR-003 Why Choose uv and pnpm
version: V1.0
status: Accepted
created: 2026-07
---

# ADR-003

# 为什么 EAAP 使用 uv 和 pnpm


---

# 1. 状态


Accepted


---

# 2. 背景


EAAP同时包含：

Frontend:

- Vue3
- TypeScript


Backend:

- Python
- FastAPI


需要统一依赖管理方案。


---

# 3. 前端依赖管理


选择：

pnpm


原因：

- 快速
- 节省磁盘
- 支持Monorepo


---

# 4. Python依赖管理


选择：

uv


原因：

- 现代Python工具链
- 高性能依赖解析
- 虚拟环境管理方便


---

# 5. 决策


项目统一：

```
Frontend

pnpm


Backend

uv

```


---

# 6. 影响


优势：

- 环境一致
- 安装速度提升
- 方便CI/CD


---

# 7. 相关文档


- Environment.md
- Technology_Stack.md
