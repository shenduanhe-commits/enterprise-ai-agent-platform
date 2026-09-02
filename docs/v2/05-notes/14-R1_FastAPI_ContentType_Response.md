# FastAPI：Content-Type、Response、Exception


| 项目   | 内容                                                                                                                        |
| ---- | ------------------------------------------------------------------------------------------------------------------------- |
| 版本   | V2.1                                                                                                                      |
| 日期   | 2026-09-01                                                                                                                |
| 阶段   | R1                                                                                                                        |
| 对照代码 | `apps/api/app/api/v1/`、`app/handlers/exception_handler.py`、`app/core/exceptions.py`、`app/core/sse.py`                     |
| 相关   | [04-Request_Handle.md](04-Request_Handle.md)（一次请求生命周期）、[10-CORS.md](10-CORS.md)、[AI_API.md](../02-architecture/AI_API.md) |


请求体、响应体在网上都是 **字节**。`Content-Type` 约定怎么解这些字节；FastAPI 再把路由的 `return` / `raise` 变成某种 `Response` 写回客户端。流式只决定 **分几块写**，和是不是二进制、是不是 UTF-8 无关。

---

## 1. 总流程

```text
前端选编码（JSON / FormData / ...）
    → HTTP 请求：Header 里 Content-Type + Body 字节
        → FastAPI 按参数声明解析（JSON 模型 / Form / File / Query）
            → 路由 return 数据 或 raise 异常
                → 成功：JSONResponse / StreamingResponse / ...
                → 失败：exception handler 再造一个 Response
                    → Uvicorn 写出 HTTP
                        → 前端按响应 Content-Type 去读
```

请求和响应都可以带 `Content-Type`：

- **请求**：告诉后端 body 怎么解析。
- **响应**：告诉前端怎么读回来。

---



## 2. 前端会用到的 Content-Type

`Content-Type` 是 MIME：`类型/子类型`，IANA 里有几千种，API 不必记全。本仓库实际会碰到的：


| Content-Type                        | 谁用                     | Body 长什么样                   | 能不能带文件     |
| ----------------------------------- | ---------------------- | --------------------------- | ---------- |
| `application/json`                  | 登录、建 Agent、Chat        | `{"email":"..."}`（UTF-8 文本） | 否          |
| `multipart/form-data; boundary=...` | 知识库上传                  | 按 boundary 切成多段，每段可以是字段或文件  | **是**      |
| `application/x-www-form-urlencoded` | HTML `<form>` 默认       | `a=1&b=hello`               | 否（不能好好传文件） |
| `text/plain`                        | 少见                     | 纯文本                         | 否          |
| `application/octet-stream`          | 通用二进制                  | 原始字节                        | 本身就是文件     |
| `text/event-stream`                 | **响应**（`/chat/stream`） | SSE 文本帧                     | —          |


浏览器上传文件时，请求头类似：

```text
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryXYZ
```

`boundary` 用来切开每一段，没有它服务端不知道字段从哪开始、到哪结束。

### 2.1 FormData 和 multipart 不是两种格式


|     | FormData                               | multipart/form-data           |
| --- | -------------------------------------- | ----------------------------- |
| 是什么 | JS 里的对象 / API                          | HTTP 的编码方式                    |
| 在哪  | 浏览器内存                                  | 请求头 + 请求体                     |
| 关系  | `fetch` 发 `FormData` 时，浏览器编成 multipart | 服务端只看见这种编码，看不见 `FormData` 这个类 |


带文件必须走 FormData / multipart。不要自己设 `Content-Type`（会丢掉 boundary）；让浏览器自动带。

只有文本、没有文件时，也可能发 `application/x-www-form-urlencoded`。那也是「表单」，但 `File()` 解析不了。

### 2.2 文本、UTF-8、二进制

网上传的永远是字节。「文本」= 这些字节要用字符编码还原。JSON / SSE 默认 **UTF-8**。

```text
字符 --UTF-8--> 字节 --网络--> 字节 --UTF-8--> 字符
像素 --PNG----> 字节 --网络--> 字节 --PNG----> 像素
```

UTF-8 是「字符 ↔ 字节」的规则，不是和二进制并列的另一种介质。口语里的「二进制」= **不要当字符解**（图片、zip）。Python：`str` 是字符，`bytes` 是原始字节；`encode("utf-8")` / `decode("utf-8")` 在两边转换。

### 2.3 流式 ≠ 二进制


|           | 文本              | 二进制                 |
| --------- | --------------- | ------------------- |
| **整包发完**  | JSON            | 一张完整 PNG            |
| **边生成边发** | SSE（本仓库 Chat 流） | 大文件下载 `yield bytes` |


流式描述 **怎么传**；二进制描述 **按什么协议解**。`/chat/stream` 是流式 **文本**。

---



## 3. 前端怎么传给后端



### 3.1 JSON（本仓库大多数接口）

```javascript
fetch("/api/v1/agents/1/chat", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ user_message: "你好", conversation_id: 10 }),
});
```

对应 FastAPI：参数类型是 Pydantic 模型（如 `ChatRequest`），**不要** 写 `Form()`。

### 3.2 文件 + 字段（知识库上传）

```javascript
const form = new FormData();
form.append("agent_id", "1");
form.append("title", "产品手册");
form.append("file", fileInput.files[0]);

fetch("/api/v1/knowledge/documents", {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: form,
});
```

对应：

```python
agent_id: int = Form()
file: UploadFile = File()
title: str | None = Form(None)
```


| 前端                        | FastAPI               |
| ------------------------- | --------------------- |
| `append("agent_id", "1")` | `Form()` → `int`      |
| `append("title", "...")`  | `Form(None)` 可选       |
| `append("file", File)`    | `UploadFile = File()` |


依赖包 `python-multipart`：Starlette/FastAPI 解析 `multipart/form-data` 用。缺了它，`Form()` / `File()` 会直接报错。JSON 接口不需要这个包。

`UploadFile` 是文件对象（`filename`、`content_type`、`await file.read()`），`File()` 只是告诉 FastAPI「从 multipart 的文件部分取值」。也可以 `content: bytes = File()`，大文件更适合 `UploadFile`。

GET 只有 query（如 `agent_id=1`），没有 body，也就没有请求 `Content-Type`。

---



## 4. 后端怎么处理并 Response

路由 `return` 之后 FastAPI 大约三步：看返回值 → 用 `response_model` 校验/裁剪 → 变成 Starlette `Response`，交给 Uvicorn。

### 4.1 常用 Response 类（`fastapi.responses`）

种类是开放的（可自己子类化），日常就这些：

```text
Response
├── JSONResponse              # 普通 API 默认
├── PlainTextResponse
├── HTMLResponse
├── RedirectResponse
├── FileResponse              # 读磁盘文件发给客户端
├── StreamingResponse         # yield 一块发一块
│     └── EventSourceResponse # SSE 标记，media_type=text/event-stream
└── UJSONResponse / ORJSONResponse  # 已弃用
```


| 路由 `return`                | 变成             | 怎么传给前端            |
| -------------------------- | -------------- | ----------------- |
| Pydantic / dict / list     | `JSONResponse` | **整份 JSON 算完再发**  |
| 已是 `Response` 子类           | 原样用            | 看你用的类             |
| `StreamingResponse(gen())` | 流式             | `yield` **一块发一块** |


`return current_user` 时你看不见 `JSONResponse`，框架会建：`Content-Type: application/json`，UTF-8，通常带 `Content-Length`。底层 TCP 可能 chunked，那是传输切包，**不是**业务流式。

### 4.2 本仓库对照


| 接口                              | 请求           | 响应                                                     |
| ------------------------------- | ------------ | ------------------------------------------------------ |
| `POST /users`、`GET /users/me`   | JSON 或无 body | `JSONResponse`（`UserResponse`）                         |
| `POST /knowledge/documents`     | multipart    | 成功仍是 **一份 JSON**（`KnowledgeDocumentResponse`），不是把文件流回去 |
| `POST /agents/{id}/chat`        | JSON         | 一份 `ChatResponse`                                      |
| `POST /agents/{id}/chat/stream` | JSON         | `StreamingResponse`，`text/event-stream`                |


流式实现（`agents.py`）：鉴权、找 Agent **必须在** `StreamingResponse` 之前完成，这样 401/404 仍是普通 JSON 错误。之后：

```python
async def generate():
    async for event, data in executor.execute_stream(...):
        yield format_sse(event, data)

return StreamingResponse(
    generate(),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "Connection": "keep-alive", ...},
)
```

`format_sse` 产出文本帧（UTF-8）：

```text
event: token
data: {"text":"你"}

event: done
data: {"conversation_id":10,"status":"completed"}
```

帧末尾必须空行 `\n\n`，客户端才知道一帧结束。

新版 FastAPI 也可用 `response_class=EventSourceResponse` 再 `yield`；本仓库是手写 SSE 字符串 + `StreamingResponse`。

---



## 5. Exception 怎么变成 Response

异常 **不走** `return UserResponse`。`raise` 之后由 **exception handler** 再造 Response，默认仍是 `JSONResponse`，只是 status 不是 200。没有单独的 `ExceptionResponse` 类。

#### **统一捕获**

Starlette 把应用包在 `try/except Exception` 里。路由 `raise`、依赖校验失败，**只要还没开始写响应，都会进这里**。抛出的`Exception`会被框架中间件统一 `except` 住，再按 **异常类型** 去登记表里找 handler（**一张 handler 表，框架预填几项，你再往上加**。处理时按类型从精确到宽泛匹配。）；找到就用它造 Response，找不到再变成 500。

#### **按类型找 handler**

*lookup*exception_handler：沿着 type(exc).__mro__ 查表

`raise NotFoundException(...)` 时查找顺序类似：

NotFoundException  → 表里没有

EAAPException      → 你们 add_exception_handler 登记了  → 用这个

Exception          → 一般不登记

所以子类不用每个都注册，挂在 `EAAPException` 上就能接住整棵树。

#### **表里一开始就有的（算「内置 handler」）**

创建 `FastAPI()` 时已经登记了，不是空表：


| **异常**                   | **谁登记**             | **结果**                     |
| ------------------------ | ------------------- | -------------------------- |
| `HTTPException`          | Starlette / FastAPI | `{"detail": ...}` + status |
| `RequestValidationError` | FastAPI             | **422**                    |
| `WebSocketException` 等   | 框架                  | 关 WS                       |


你们又加了：

app.add_exception_handler(EAAPException, eaap_exception_handler)

于是：

raise HTTPException(404)         → 内置

body 对不上 schema               → 内置 422

raise BusinessException("...")   → 自定义 {"code","message"}

raise ValueError("...")          → 表里没有 → 再往上抛

表里没有时 **不是** 再交给「另一个 FastAPI 业务 handler」，而是 `raise` 出去，由更外层的 `ServerErrorMiddleware` 接住，变成 **500**（debug 时带 traceback）。

也可以按 **status_code** 登记（`add_exception_handler(404, ...)`），`HTTPException` 会优先看这个。此项目没用这种方式。

#### **统一捕获也有边界**

FastAPI / Starlette 只抓`Exception`


| **情况**                                              | **会不会进这套 handler**                                                              |
| --------------------------------------------------- | ------------------------------------------------------------------------------- |
| 路由 / Depends 里 `raise Exception` 且响应还没发出            | 会                                                                               |
| 已经 `return StreamingResponse`，生成器里再 raise           | **不会**改成 JSON；响应已开始，框架会报 `response already started`。所以你们自己 `yield event: error` |
| `KeyboardInterrupt` / `SystemExit`/ `GeneratorExit` | 挂载在`BaseException下，`不是 `Exception` 子类，这层 `except Exception` 抓不住                 |


一句话：**统一捕获 → 按异常类（MRO）查 handler 表（内置 + 自定义）→ 没有则 500；响应一旦开写就改不了 HTTP 状态。**

### 5.1 本仓库自定义的Exception 处理

`main.py`：

```python
app.add_exception_handler(EAAPException, eaap_exception_handler)
```

handler：

```python
return JSONResponse(
    status_code=exc.status_code,
    content={"code": exc.code, "message": exc.message},
)
```

成功 vs 失败：

```text
return 模型                 → JSONResponse 200，body 是业务字段
raise NotFoundException     → handler → JSON 404  {"code":404,"message":"..."}
```

**本仓库业务**

```text
EAAPException
├── NotFoundException        404
├── BusinessException        400
├── UnauthorizedException    401
└── AgentRuntimeException    500
      ├── LLMException / PromptException / MemoryException / ToolException
```

分层：Repository 返回数据或 `None`；Service `raise EAAPException`；路由尽量不 `try/except`。

### 5.2 会碰到哪些系统自带的异常

**FastAPI / Starlette**


| 异常                        | 谁抛                                 | 默认                              |
| ------------------------- | ---------------------------------- | ------------------------------- |
| `HTTPException`           | 你或依赖                               | `{"detail": "..."}` + 对应 status |
| `RequestValidationError`  | JSON / Query / `Form` / `File` 对不上 | **422**                         |
| `ResponseValidationError` | 返回值对不上 `response_model`            | **500**                         |
| `WebSocketException` 等    | WebSocket                          | 关连接，不是 HTTP JSON                |


缺表单字段、类型不对 → 422，**不会**变成 `BusinessException`。

**未注册的 Python 异常**（`ValueError`、驱动错误等）→ **500**。`except Exception` 抓不住 `KeyboardInterrupt` / `SystemExit`。

Python 没有和 Java 平级的 `Error` 基类。`TypeError`、`MemoryError` 名字带 Error，仍是 `Exception` 子类。SSE 里的 `event: error` 只是 **事件名**，不是 Python 类型。

### 5.3 请求进来怎么分流

```text
raise HTTPException(404)            → FastAPI 默认  {"detail": ...}
raise NotFoundException("...")      → 本仓库 handler  {"code","message"}
body 对不上 schema                  → RequestValidationError → 422
return 对不上 response_model        → ResponseValidationError → 500
raise ValueError                    → 未处理 → 500
```

前端可按 status 分流：200 用业务 body；401 跳登录；422 展示校验；400/404 展示 `message`；500 统一「系统繁忙」。细业务用 body `code`，不要每种业务一个 HTTP 码。

### 5.4 流式是例外

`return StreamingResponse` 之后 HTTP 状态已经是 **200**。生成器里再 `raise` **改不成** 404 JSON。所以 `generate()` 里接住 `EAAPException`，改成：

```text
event: error
data: {"code":...,"message":...}
```

---



## 6. 和「一次请求」笔记的衔接

[04-Request_Handle.md](04-Request_Handle.md) 讲生命周期：中间件 → Depends 开 session → 路由 → 得到 Response → 关 session → 写出 HTTP。

本文补三块：body 用哪种 Content-Type 进来、成功时选哪种 Response、失败时哪一种 Exception 变成哪种 JSON。路由函数结束 ≠ 资源已释放；流已开始则不能再改 HTTP 状态码。

---



## 7. 面试口吻

- 浏览器 `FormData` 发出去就是 `multipart/form-data`；JSON 接口不要混用 `Form()`。
- FastAPI 对 `return user` 会包 `JSONResponse`；只有 `StreamingResponse` 才是业务流式。
- 异常也是 Response，由 handler 构造；校验失败是 422，不是我们的 `EAAPException`。
- Chat 流必须先做完鉴权再进入 SSE；流内错误只能再 yield 一帧 `error`。
- UTF-8 是文本的字节编码；流式是传输方式；两者正交。

