# 代码规范 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/03-development/CodingStyle.md`（V1） |

重点在 **Python / Agent**。前端沿用现有 ESLint/Oxlint/Prettier，不单列学习规范。

---

## 1. 通用

- 可读性优先于炫技。
- 一个模块一类职责。
- 先复用现有分层，不先抽象「未来框架」。
- 公开函数用类型注解。
- 不要提交 `.env`、密钥、大数据夹具。

---

## 2. 后端分层

```
Router（薄）→ Service（业务、抛 EAAPException）→ Repository（存取、返回实体或 None）
```

- Router 不写业务 try/except，不直接打 SQLAlchemy。
- Repository 不抛「找不到」业务异常。
- Schema（Pydantic）与 Model（SQLAlchemy）分开；API 不直接暴露 Model。
- AI 组件（Gateway、Tool、Runtime）用依赖注入，便于测试时 Mock。

---

## 3. Python

- 3.12；async 到底，不要在 async 路由里用同步阻塞 HTTP。
- 格式与静态检查：`ruff`。
- 命名：模块/函数 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE`。
- 异常：用 `app.core.exceptions` 里的类型，不要 `raise HTTPException` 散落（现有 users/agents 路由里的 HTTPException 在 R1 收掉）。
- 日志：用现有 logging，不 print 密钥；`main.py` 里 print URL 应在 R0/R1 去掉。

Agent 代码：

- Provider 必须解析 `tool_calls`，与 Qwen 实现对齐。
- Tool `schema` 必须含真实 `properties`。
- 循环必须有硬上限。
- 不要引入已 Avoid 的 LangChain 旧 API。

---

## 4. 前端（仅约束，不学习）

- `<script setup lang="ts">`。
- 页面保持薄：调 API、展示文本。
- 状态只存 token 与当前会话。
- 不新增组件库。

---

## 5. 提交信息

```
type(scope): message
```

`feat` / `fix` / `docs` / `test` / `refactor` / `chore`

示例：`feat(runtime): parse tool_calls in OpenAI provider`
