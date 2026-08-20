# API 设计 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| Base URL | `http://localhost:8000/api/v1` |
| 替代 | `docs/AI接口设计文档 V1.0.md` |

V1 规划了独立 `/chat`、`/tasks`、`/admin`。V2 把对话挂在 Agent 下，与现有代码一致：`/agents/{id}/chat`。

---

## 1. 约定

- JSON；`Content-Type: application/json`。
- 需登录的接口：`Authorization: Bearer <access_token>`。签发与校验见 [JWT.md](../03-development/JWT.md)。
- 成功：直接返回资源（FastAPI `response_model`）。不要混用 `{ code, message, data }` 包一层。
- 错误：`EAAPException` → JSON `{ "code", "message" }`，HTTP 状态见 [Request_Handle.md](../03-development/Request_Handle.md)。

---

## 2. 已落地

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| GET | `/`（应用根） | 服务名与状态 | 无 |
| GET | `/api/v1/health` | 健康检查 | 无 |
| POST | `/api/v1/auth/register` | 注册（email + password） | 无 |
| POST | `/api/v1/auth/login` | 返回 access、refresh、user | 无 |
| POST | `/api/v1/auth/refresh` | body：`{ "refresh_token" }` | 无（凭 refresh） |
| GET | `/api/v1/auth/me` | 当前用户 | Bearer |
| POST | `/api/v1/users` | 注册别名，同 `/auth/register` | 无 |
| GET | `/api/v1/users/me` | 当前用户 | Bearer |
| GET | `/api/v1/users/{id}` | 仅能读自己，否则 404 | Bearer |
| POST | `/api/v1/agents` | 创建；`created_by` 取 JWT | Bearer |
| GET | `/api/v1/agents` | 当前用户的 Agent | Bearer |
| GET | `/api/v1/agents/{id}` | 详情；非所有者 404 | Bearer |
| POST | `/api/v1/agents/{id}/chat` | 非流式对话 | Bearer |
| POST | `/api/v1/agents/{id}/chat/stream` | SSE：token / tool / done / error | Bearer |
| GET | `/api/v1/conversations` | 当前用户会话；可选 `?agent_id=` | Bearer |
| GET | `/api/v1/conversations/{id}/messages` | 历史；非所有者 404 | Bearer |

### 创建 Agent

```json
{
  "name": "ops-bot",
  "description": "optional",
  "provider": "mock",
  "model_name": "mock-model",
  "system_prompt": "You are a helpful agent."
}
```

`created_by` 从 JWT 取，不要放进 body。

### Chat

请求：

```json
{
  "conversation_id": null,
  "variables": { "dept": "sales" },
  "user_message": "12*7+5 等于多少"
}
```

响应：

```json
{
  "conversation_id": 10,
  "role": "assistant",
  "content": "89",
  "created_at": "2026-08-15T00:00:00Z"
}
```

`conversation_id` 为空则按 `user_message` 建会话。

SSE 示例：

```text
event: token
data: {"text":"你"}

event: done
data: {"conversation_id":10}
```

登录失败：HTTP 401，`{ "code": 401, "message": "邮箱或密码错误" }`。

本机演示账号与完整 curl（含登录、建 Agent、两轮 Chat、拉历史）见 [JWT.md](../03-development/JWT.md) 第 12 节。

---

## 3. 计划中的端点

### R2

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/runs/{run_id}` | 图执行状态 |
| POST | `/runs/{run_id}/resume` | HITL 批准或拒绝 |

### R3

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/knowledge/documents` | multipart 上传 |
| GET | `/knowledge/documents` | 列表与状态 |
| DELETE | `/knowledge/documents/{id}` | 同步删向量 |

Chat 响应增加 `citations: [{ document_id, title, chunk_id }]`。

### R4

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/tools` | 注册表 |
| PUT | `/agents/{id}/tools` | 绑定工具 ID 列表 |

### R5–R6

- 协作过程通过 run trace 或消息上的 `agent_name` 暴露，不另造一套聊天协议。
- `GET /usage`、`GET /audit` 仅 admin。

---

## 4. 错误示例

```json
{ "code": 404, "message": "Agent not found" }
```

HTTP 404。前端（若有）按状态码分流，页面只处理少数业务 code。

---

## 5. 版本

前缀 `/api/v1`。
