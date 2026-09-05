# 安全设计 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/04-deployment/SecurityDesign.md`（V1 完整企业安全清单） |

V1 覆盖 SSO、完整 RBAC、数据分级。V2 按阶段长，先达到「能当企业作业讲」的最小集。

---

## 1. 原则

- 最小权限：用户、Agent、Tool 默认什么都不能做，再授权。
- 默认拒绝：未绑定的工具对模型不可见。
- 不信任客户端：R1 起身份只来自 JWT，不信 body 里的 `user_id` / `created_by`。机制见 [JWT.md](../05-notes/08-JWT.md)。
- 可审计：改 Agent、HITL 批准、上传文档要留下谁做了什么（R6）。

---

## 2. 按阶段

| 阶段 | 必须有 |
| --- | --- |
| R0 | 密码服务端 Argon2/bcrypt；禁止收 `password_hash` |
| R1 | JWT access + refresh；资源按 `user_id` 隔离；HTTPS 仅生产再谈（机制见 [HTTPS.md](../05-notes/09-HTTPS.md)） |
| R2 | 危险工具 HITL；工具超时 |
| R3 | 文档按 owner 隔离；检索带 filter |
| R4 | 工具注册表 + Agent 绑定；HTTP MCP 可配 `headers`（静态 Bearer）；OAuth 未做 |
| R6 | admin/member；审计日志；基础提示注入与 PII 脱敏；工具白名单 |

SSO、完整 permission 矩阵、字段级加密：Hold。

---

## 3. Agent 特有风险

| 风险 | 对策 |
| --- | --- |
| 提示注入（文档/用户让模型乱调工具） | 工具白名单；写操作 HITL；R6 基础检测 |
| 工具乱写生产系统 | 先用假工具；真副作用必须 HITL |
| 密钥进 Prompt | Gateway 与日志脱敏；永远不把 Key 放进 messages |
| 越权读知识库 | Qdrant payload filter + DB owner 检查 |
| 死循环烧钱 | max iterations；R6 token 配额 |

---

## 4. 传输与存储

- 本地 HTTP 可接受；演示不要暴露到公网。HTTPS 加密了什么、私钥干什么、地址会不会被看见：见 [HTTPS.md](../05-notes/09-HTTPS.md)。
- 密钥：`.env`，不入库。
- 密码：只存哈希。
- 会话内容视为企业数据，列表/详情必须鉴权（R1）。
- Access 走 `Authorization`；refresh 只出现在 `/auth/refresh` 的 JSON，核心是让长票少露面。当前每次刷新会换新的 7 天 refresh（滑动续期）。两枚都塞进 localStorage 时 XSS 可以一起偷走。Cookie 只带给种它的主机，不会随请求寄到任意网站。详见 [JWT.md](../05-notes/08-JWT.md) 第 9–10 节。
- CORS 不是接口验身份：预检和 `Allow-Origin` 只对浏览器有用；curl 不带 Origin 也会通。见 [CORS.md](../05-notes/10-CORS.md)。
