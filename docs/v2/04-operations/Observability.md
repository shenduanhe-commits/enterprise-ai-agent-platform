# 可观测性 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/04-deployment/Observability.md` |

---

## 1. 目标

一次 Chat 必须能回答：调了哪个模型、哪些工具、每步多久、花了多少 token、在哪失败。

没有轨迹的 Agent 在面试里等于无法调试的黑盒。

---

## 2. 按阶段

| 阶段 | 做法 |
| --- | --- |
| 现在 | 应用日志；缺结构化 trace |
| R2 | 每个 node 的输入输出与耗时（表或先写日志）；run_id 关联 conversation |
| R3 | 检索 query、命中 chunk、rerank 分数写入同一 run |
| R6 | Langfuse（或等价）+ OpenTelemetry；指标：延迟、token、工具失败率 |

V1 的全套 Metrics/Tracing/Logging 平台一次上齐不现实。先保证 **应用级 run trace**，再接专用产品。

---

## 3. 与评测的关系

- 在线：trace 用于排障。
- 离线：黄金集与 trajectory eval（见 TestingStrategy）。
- 数据飞轮：失败 trace 可变成新的黄金用例。这是 R6 的加分项，不是 R0 的范围。

---

## 4. 日志红线

禁止打印 API Key、密码、完整证件号。必要时对 user message 做截断。
