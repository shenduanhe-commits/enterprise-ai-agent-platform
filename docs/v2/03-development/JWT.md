# JWT 学习笔记（R1）

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 日期 | 2026-08-18 |
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
2. `typ` 必须是 `access`（或旧 token 没有 `typ`）。refresh 不能当 access 用。
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

## 9. 面试时能讲的点

1. JWT 是签名，不是加密；别把秘密放进 payload。
2. `exp` 是时间点；access 短、refresh 长，丢了 access 不必马上重新输密码。
3. 自定义 `typ` 防止两种 token 互用。
4. 身份从 JWT 来，创建 Agent 时 `created_by` 取 `current_user.id`。
5. 本实现 refresh 也是 JWT，服务端不存会话。无法主动作废某一枚（除非改 `JWT_SECRET` 或以后加黑名单）。R1 够用，生产常会把 refresh 存 Redis 以便登出。

---

## 10. 自己走一遍

```bash
# 注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"you@eaap.com\",\"password\":\"secret12\"}"

# 登录，记下 access_token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"you@eaap.com\",\"password\":\"secret12\"}"

# 带 access 访问
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

把 access 贴进 jwt.io（只用于本地假数据），对照 header 的 `alg` 和 payload 的 `sub` / `typ` / `exp`。
