# ADR-005 前端只做演示壳

| 项 | 内容 |
| --- | --- |
| 状态 | Accepted |
| 日期 | 2026-08-15 |
| 替代 | V1 ADR-001（Why Vue3）、V1 ADR-005（Why Playwright） |

## 背景

作者是前端开发人员，目标是 Agent 工程师岗位。V1 把 Vue 企业架构和 Playwright 当学习主线，会稀释后端与 Agent 时间。

## 决策

- 保留现有 Vue 3 脚手架，不换 React。
- 前端不作为学习目标；每阶段最多 1–3 天接线。
- 验收以 Swagger / curl / pytest 为准。
- Playwright 不作门禁、不作学习任务。
- 不引入新组件库、不建设计系统。

## 后果

作品集的 UI 会偏朴素。用 README 和录屏证明能力在 Runtime / RAG / MCP，不在仪表盘。
