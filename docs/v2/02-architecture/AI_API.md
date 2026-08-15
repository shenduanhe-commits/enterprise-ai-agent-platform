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
- R1 起：`Authorization: Bearer <access_token>`。
- 成功：多数端点直接返回资源（现有 FastAPI `response_model`）。若将来包一层 `{ code, message, data }`，必须全站统一；**不要混用两套**。当前代码是直接返回模型，V2 维持这一点。
- 错误：`EAAPException` → JSON `{ "code", "message" }`，HTTP 状态见 [Request_Handle.md](../03-development/Request_Handle.md)。
- 业务细分用 body `code`，不发明一堆 HTTP 码。

---

## 2. 已落地

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| GET | `/`（应用根） | 服务名与状态 | 无 |
| GET | `/api/v1/health` | 健康检查 | 无 |
| POST | `/api/v1/users` | 创建用户 | 无（R0 改密码字段；R1 迁到 /auth） |
| GET | `/api/v1/users` | 列表 | 无 |
| GET | `/api/v1/users/{id}` | 详情 | 无 |
| POST | `/api/v1/agents` | 创建 | 无 |
| GET | `/api/v1/agents` | 列表 | 无 |
| GET | `/api/v1/agents/{id}` | 详情 | 无 |
| POST | `/api/v1/agents/{id}/chat` | 非流式对话 | 无 |

### 创建用户（将改）

现状 `UserCreate`：`email`、`password_hash`。R0 改为 `password`，服务端哈希。

### 创建 Agent

```json
{
  "name": "ops-bot",
  "description": "optional",
  "provider": "qwen",
  "model_name": "qwen-plus",
  "system_prompt": "You are a helpful agent.",
  "created_by": 1
}
```

R1 起去掉 `created_by`，改从 JWT 取。

### Chat

请求：

```json
{
  "agent_id": 1,
  "user_id": 1,
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

`conversation_id` 为空则按 `user_message` 建会话。R1 起去掉 body 里的 `user_id`。

---

## 3. 计划中的端点

### R1 Auth

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/auth/register` | email + password |
| POST | `/auth/login` | 返回 access、refresh、user |
| POST | `/auth/refresh` | |
| GET | `/auth/me` | |

现有 `/users` 列表在 R1 后仅 admin 或删除。

### R1 流式与会话

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/agents/{id}/chat/stream` | SSE；事件含 token / tool / done / error |
| GET | `/conversations` | 当前用户会话 |
| GET | `/conversations/{id}/messages` | 历史 |

SSE 示例：

```text
event: token
data: {"text":"你"}

event: done
data: {"conversation_id":10}
```

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

前缀 `/api/v1`。破坏性变更（如去掉 `user_id`）在 R1 一次性做完，不长期双字段。
