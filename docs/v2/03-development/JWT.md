# JWT 学习笔记（R1）

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 日期 | 2026-08-20 |
| 对照代码 | `apps/api/app/core/security.py`、`dependencies.py`、`services/user_service.py` |
| 接口约定 | [AI_API.md](../02-architecture/AI_API.md) |

本文只讲 **本仓库已经落地的签发 / 传递 / 校验**。不是 JWT 百科。读完应能对着代码讲清：登录返回什么、请求怎么带 token、`CurrentUser` 从哪来。

---

## 1. 要解决什么

HTTP 是无状态的。登录成功后，服务端不能靠「刚才那个浏览器」记住你是谁。

做法：登录时签发一枚 **JWT**（JSON Web Token）。之后每次请求在 HTTP 头里带上它，服务端验签、读出用户 id。

身份只来自 token，不信 body 里的 `user_id` / `created_by`。见 [Security.md](../04-operations/Security.md)。

密码只在登录那一次用；**token 里没有密码**。

---

## 2. 一枚 JWT 长什么样

登录返回的 `access_token` 是三段 Base64url，用点连接：

```text
header.payload.signature
```

例如：

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidHlwIjoiYWNjZXNzIiwiZXhwIjox...
```

| 段 | 谁写的 | 能不能随便看 | 作用 |
| --- | --- | --- | --- |
| header | `jwt.encode` 自动加 | 能 | 声明算法 |
| payload | 我们传入的 dict | 能 | 用户 id、类型、过期时间 |
| signature | 密钥算出来的 | 不能伪造 | 防篡改 |

header、payload 只是编码，不是加密。任何人都能解码看到内容。防伪造靠第三段：改了前两段而不用 `JWT_SECRET` 重签，`decode_token` 会失败。

把三段贴到 [jwt.io](https://jwt.io) 可以对照。不要把生产 token 贴上去。

---

## 3. Header

代码里没有手写 header。`jwt.encode(..., algorithm="HS256")` 会生成：

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

- `alg`：用 HMAC-SHA256，密钥是 `.env` 里的 `JWT_SECRET`。
- `typ`：这是一枚 JWT（JOSE 标准字段）。

这和 payload 里的 `typ` **不是同一个东西**：

| 位置 | `typ` |
| --- | --- |
| header | 固定 `"JWT"` |
| payload | 我们自己加的 `"access"` 或 `"refresh"` |

---

## 4. Payload（我们真正签发的内容）

签发入口：`_encode`。

```23:33:apps/api/app/core/security.py
def _encode(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    return jwt.encode(
        {
            "sub": str(user_id),
            "typ": token_type,
            "exp": expire,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
```

| 字段 | 含义 | 注意 |
| --- | --- | --- |
| `sub` | subject，用户 id | JWT 惯例用字符串，校验时再 `int()` |
| `typ` | `access` 或 `refresh` | 自定义 claim，用来禁止两种 token 混用 |
| `exp` | 过期的那一刻 | 必须是时间点，不能是「15 分钟」这种时长 |

两个包装函数只是过期时间和 `typ` 不同：

| 函数 | `typ` | 默认有效期 | 配置 |
| --- | --- | --- | --- |
| `create_access_token` | `access` | 15 分钟 | `JWT_EXPIRES_IN`（分钟） |
| `create_refresh_token` | `refresh` | 7 天 | `JWT_REFRESH_EXPIRES_IN`（天） |

刷新也会再调 `_tokens_for`，所以会换一枚**新的** 7 天 refresh（滑动续期，见第 9 节）。7 天是「从这次签发起算」，不是「账号总共只能登录 7 天」。

登录、刷新都走 `UserService._tokens_for`，一次发一对：

```63:69:apps/api/app/services/user_service.py
    def _tokens_for(self, user) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
```

响应里的 `token_type: "bearer"` 是 HTTP 约定（头里写 `Bearer <token>`），不是 JWT header 里的 `typ`。

---

## 5. 请求时怎么带过来

受保护接口不收 token 作为 JSON 字段。客户端放在 HTTP 头：

```http
Authorization: Bearer <access_token>
```

FastAPI 的 `HTTPBearer` 按**第一个空格**切开：

| 对象 | 字段 | 值 |
| --- | --- | --- |
| `HTTPAuthorizationCredentials` | `scheme` | `"Bearer"` |
| 同上 | `credentials` | 空格后面整段 JWT 原文 |

`credentials` 就是登录返回的那串 `access_token`，**此时还没有解码**。

`auto_error=False`：没有这个头时返回 `None`，由我们抛 `UnauthorizedException("未登录")`，错误体仍是 `{ code, message }`。

---

## 6. FastAPI 怎么把 token 注入到函数参数

没有人手动调用 `get_current_user(creds=...)`。路由写了 `current_user: CurrentUser`，FastAPI 会沿 `Depends` 链解析。

```
路由参数 current_user: CurrentUser
  → Depends(get_current_user)
      → db: DbSession          → Depends(get_db) 开数据库会话
      → creds: BearerCreds     → Depends(_bearer) 读 Authorization
          → 取出 credentials（JWT 字符串）
          → UserService.get_user_by_token
```

`BearerCreds` / `CurrentUser` 是 `Annotated[类型, Depends(...)]` 别名，和写成

```python
creds: HTTPAuthorizationCredentials | None = Depends(_bearer)
```

等价，只是 Depends 不放在默认参数里。

---

## 7. 校验：字符串变回用户

`get_user_by_token`：

1. `decode_token`：用同一把 `JWT_SECRET` 验签，并检查 `exp`。
2. `typ` 必须是 `access`。refresh 不能当 access 用。
3. `sub` 转成 int，按 id 查库。用户不存在则 401。
4. 过期 → `Token 过期`；签不对、格式坏 → `Token 无效`。

刷新接口反过来：只接受 `typ == "refresh"`，再签发**新的一对** access + refresh。access 拿去刷新会 401。

单测见 `apps/api/tests/test_user_service.py`。

---

## 8. 接口对照

| 路径 | token 角色 |
| --- | --- |
| `POST /api/v1/auth/login` | 验密码，签发一对 |
| `POST /api/v1/auth/refresh` | body 里带 `refresh_token`，再签发一对 |
| `GET /api/v1/auth/me` 以及 Agent / Chat / 会话 | 头里带 **access** |

Swagger：先 login，把 `access_token` 填进 Authorize。不要填 refresh。

---

## 9. 为什么要有 refresh

核心就一句话：**尽量让 refresh 少露面。** 不是「有两枚就绝对安全」，也不是「有 refresh 的人待不久」。

日常 Chat 只带 15 分钟的 access。Refresh 尽量少出现在网上、日志、插件能抄到的 Header 里。抄到一次业务请求，通常只能用十几分钟，换不来长票。

| | access | refresh |
| --- | --- | --- |
| 有效期 | 15 分钟 | 7 天（见下方滑动续期） |
| 放哪 | 每次请求的 `Authorization` 头 | 只在过期时打 `/auth/refresh` |
| 能调业务接口吗 | 能 | 不能（`typ` 不是 `access`） |

`typ` 互斥：refresh 不能当 Bearer 调 `/agents`；access 不能拿去刷新。

### 滑动续期：有 refresh 就能一直换

`/auth/refresh` 每次都会再签发**一对新的** access + refresh。7 天不是「总共只能登录 7 天」，而是「**连续 7 天不用 refresh 才会断**」。常用的人可以一直留在登录态。

和「只用一枚 7 天 access」的差别不在「能不能一直用」，而在漏哪一枚：

| 漏的是 | 能干什么 |
| --- | --- |
| 某次 Chat 头里的 access | 调接口，最多约 15 分钟，不能换新票 |
| refresh | 换 access，按当前实现可以一直续 |

所以更要保护 refresh 少出现在每一次 Chat 上。若不想「用着就能永远续」，生产上可：刷新时不换新 refresh、加绝对登录上限、refresh 用一次作废、存 Redis 以便登出。R1 没做这些。

### 为什么不把 access 放进 Cookie、只用一枚

可以，很多传统站就是一张登录 Cookie。R1 不用，是因为 SPA（5173 调 8000）、Swagger/curl，以及 Cookie 会自动附带（CSRF 压力大）。Bearer 必须前端自己写 Header，别的站默认加不上。

只留一枚 access Cookie 时，有效期只能二选一：15 分钟就得反复登录，或拉成 7 天又变成长票满天飞。要短票跑业务、长票少露面，仍然是两枚（可以都是 Cookie，也可以像现在这样 JSON）。

**若两枚都放进 localStorage，XSS 或电脑被拿走时会一起丢。** 拆开并不自动多一层防护。真正变强靠分开放：access 放内存或 Header，refresh 放 `HttpOnly` + `Secure` Cookie / Redis。

### HttpOnly 与 XSS：Cookie 不会带给任意网站

Cookie 只带给种下它的那台主机（还要匹配 Path）。XSS 不能 `fetch('https://evil.com')` 就把登录 Cookie 寄走。

XSS 仍能害你，是因为脚本跑在**你的页面**里，可以 `fetch` **正确的 FastAPI**（Cookie 会带上），再把返回的 JSON（对话、新 access）发到外部。挡的是「把长期票字符串拷到另一台机器」，不是「本页内不能冒充你调接口」。正道是输出转义 / CSP。

传输见 [HTTPS.md](HTTPS.md)。跨源、预检、curl 见 [CORS.md](CORS.md)。

---

## 10. 前端怎么用 refresh

用户不用每 15 分钟点一次刷新。日常请求只带 access。

Access 过期后（正在聊天也一样）：

```text
用户点发送
  → POST /agents/1/chat   Authorization: 旧 access
  → 401 Token 过期
  → 拦截器：POST /auth/refresh  { "refresh_token": "..." }
     （token 在 JSON body，不在 Authorization）
  → 存下新的一对，丢掉旧的
  → 用新 access 把刚才那次 Chat 再发一遍
```

注意：

- 多个 401 只刷新一次，其它请求排队等新 token。
- refresh 也 401 才跳登录页。
- `/auth/refresh` 不要走「带 access 的拦截器」，否则会循环。
- 本仓库还没有前端；Swagger 要手动调 `/auth/refresh`，再把新 access 填进 Authorize。

---

## 11. 面试时能讲的点

1. JWT 是签名，不是加密；别把秘密放进 payload。
2. `exp` 是时间点；access 短、refresh 长。当前实现每次刷新会换新的 7 天 refresh（滑动续期），有 refresh 就能一直用。拆两枚是为了让长票少出现在 Chat 头里。
3. 自定义 `typ` 防止两种 token 互用。
4. 身份从 JWT 来，创建 Agent 时 `created_by` 取 `current_user.id`。
5. 本实现 refresh 也是 JWT，服务端不存会话。无法主动作废某一枚（除非改 `JWT_SECRET` 或以后加黑名单）。R1 够用，生产常会把 refresh 存 Redis 以便登出。
6. 两枚都放 localStorage 时，能偷 access 往往也能偷 refresh。Cookie 只带给种它的主机，XSS 不能把 Cookie 寄到任意网站，但仍可在本页 `fetch` 你家接口。
7. HTTPS 加密的是 TLS 里的 HTTP（路径、Header、Body）；IP 和通常还有 SNI 主机名对旁路可见。见 [HTTPS.md](HTTPS.md)。
8. CORS / 预检只约束浏览器里的网页 JS，不是 FastAPI 的登录门禁。见 [CORS.md](CORS.md)。
9. 不把唯一一枚长期 access 放进 Cookie，是为了少 CSRF、方便 Swagger/curl；要短票 + 少露面的长票，仍然是两枚。

---

## 12. 自己走一遍

本机开发库可用演示账号（**不要**拿到公网）：邮箱 `user@eaap.com`，密码 `user`。登录字段是 email，没有单独的用户名。PowerShell 请用 `curl.exe`，不要用被别名成 `Invoke-WebRequest` 的 `curl`。

R1 验收链：登录 → 建 Mock Agent → 两轮对话 → 拉历史。Chat 请求体见 [AI_API.md](../02-architecture/AI_API.md)。

```bash
# 登录，记下 access_token 和 refresh_token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"user@eaap.com\",\"password\":\"user\"}"

# 带 access 访问
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# 建 Agent（created_by 从 JWT 取，不要放 body）
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"name\":\"ops-bot\",\"provider\":\"mock\",\"model_name\":\"mock-model\",\"system_prompt\":\"You are a helpful agent.\"}"

# 第一轮：不带 conversation_id，Mock 会调 calculator
curl -X POST http://localhost:8000/api/v1/agents/<agent_id>/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"conversation_id\":null,\"user_message\":\"12*7+5\"}"

# 第二轮：带上返回的 conversation_id
curl -X POST http://localhost:8000/api/v1/agents/<agent_id>/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"conversation_id\":<conversation_id>,\"user_message\":\"hello\"}"

# 拉历史
curl http://localhost:8000/api/v1/conversations/<conversation_id>/messages \
  -H "Authorization: Bearer <access_token>"

# access 过期后换票（body 里带 refresh，不要放 Authorization）
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"<refresh_token>\"}"
```

没有账号时先 `POST /auth/register`。把 access 贴进 jwt.io（只用于本地假数据），对照 header 的 `alg` 和 payload 的 `sub` / `typ` / `exp`。
