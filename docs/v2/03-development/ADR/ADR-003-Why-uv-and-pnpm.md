# ADR-003 为什么用 uv 与 pnpm

| 项 | 内容 |
| --- | --- |
| 状态 | Accepted |
| 日期 | 2026-08-15 |
| 替代 | V1 ADR-003 |

## 决策

- Python：uv（`pyproject.toml` + `uv.lock`）。
- JS：pnpm（演示壳）。

## 原因

二者都已在仓库运行；2026 年仍是当前推荐的包管理，不是过时工具。不改回 pip/venv 或 npm。
