# 请求与错误处理 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | 学习笔记 [04-Request_Handle.md](../05-notes/04-Request_Handle.md) |
| 补充 | Content-Type / Response / Exception：[14-R1_FastAPI_ContentType_Response.md](../05-notes/14-R1_FastAPI_ContentType_Response.md) |

---

## 1. 一次请求

1. 中间件前半段。
2. `Depends` yield 之前：打开 DB session。
3. 路由 / Service：成功则 return；失败则 `raise EAAPException`，由 `eaap_exception_handler` 变成 JSON。
4. 得到 Response 后：Depends yield 之后关 session；中间件后半段。
5. 写出 HTTP。

路由函数结束 ≠ 资源已释放。自己 `open()` 的文件必须 `with` / `finally`。

---

## 2. 分层异常

| 层 | 做法 |
| --- | --- |
| Repository | 返回数据或 None，不抛业务异常 |
| Service / Runtime | 抛 `EAAPException` 子类 |
| Router | 保持薄，少写 try/except |
| `main.py` | `add_exception_handler(EAAPException, ...)` |

已有子类：`NotFoundException`、`BusinessException`、`AgentRuntimeException`、`LLMException`、`PromptException`、`MemoryException`、`ToolException`。

---

## 3. HTTP 状态

| status | 含义 | 演示壳 |
| --- | --- | --- |
| 200 | 成功 | 用 body |
| 400 | 业务/参数 | 展示 `message` |
| 401 / 403 | 未登录 / 无权限 | 回登录或提示 |
| 404 | 不存在 | 空状态 |
| 422 | 校验失败 | 字段错误 |
| 500 | 服务器 | 「系统繁忙」 |

细业务（邮箱已存在等）放 body `code`，不要每种业务一个 HTTP 码。

当前成功响应是 FastAPI 直接返回模型，不是 `{data:{}}` 包一层。错误是 `{ code, message }`。演示壳按 status 分流即可。
