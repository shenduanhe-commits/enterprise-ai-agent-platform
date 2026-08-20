# CORS / 预检学习笔记

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 日期 | 2026-08-20 |
| 对照代码 | 本仓库 **尚未** 加 `CORSMiddleware`；接 Vue 演示壳时再加 |
| Token | [JWT.md](JWT.md) |
| 传输 | [HTTPS.md](HTTPS.md) |

跨源时容易把 CORS 想成 FastAPI 的门禁（像验 JWT）。它不是。本文只讲浏览器、预检、curl 各干什么。

---

## 1. 源是什么

**源（origin）** = 协议 + 主机名 + 端口。

| 地址 | 源 |
| --- | --- |
| `http://localhost:5173`（Vite） | `http://localhost:5173` |
| `http://localhost:8000`（FastAPI） | `http://localhost:8000` |

端口不同就是**不同源**。Cookie 跟的是「谁 `Set-Cookie`」的那台主机（一般是接口），不是网页文件存在哪。网页里的 JS 去 `fetch` 8000 时，带的是 8000 的 Cookie（若会带的话）。

5173 和 8000 跨源，但都是 `http://localhost`，算**同站**。SameSite=`Lax` 的 Cookie 在 `credentials: 'include'` 时有可能带上。`evil.com` 调你的 API 是跨**站**，Lax 默认不带。

---

## 2. CORS 头只对浏览器有用

标准头是 `Access-Control-Allow-Origin`（没有单独的 `Allow-Origin`），以及 `Allow-Credentials`、`Allow-Methods`、`Allow-Headers`。

它们只回答：**这个网页源里的 JS，能不能读取这次跨源响应。** 不是验证 Cookie，也不是登录。

| | 谁在拦 | 没过会怎样 |
| --- | --- | --- |
| JWT | **接口**（`get_current_user`） | 真正 401，curl 也拿不到数据 |
| CORS | **浏览器**（只拦网页 JS） | 接口可能已经 200；Vue 读不到。curl 不受影响 |

`Origin` 可以伪造（curl 随便写），不能当身份。本仓库不读 Origin，也不读 Cookie；认用户只靠 Bearer。

curl、Postman、服务端脚本**没有网页源**，不执行 CORS。不带 `Origin` 也会正常响应（有 token 时）。响应里即使写着 `Allow-Origin: http://localhost:5173`，curl 也不看。

---

## 3. 预检是浏览器发的

跨源且不像普通表单的请求（`Content-Type: application/json`、带 `Authorization` 等）会先自动发 OPTIONS：

```http
OPTIONS /api/v1/agents/1/chat
Origin: http://localhost:5173
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization, content-type
```

- 谁决定先问一声、谁拦住 JS：浏览器  
- 谁给 OPTIONS 回 `Access-Control-*`：接口或 CORS 中间件（本仓库还没有，演示壳跨源会踩坑）  
- 谁验 JWT、谁做 Chat：后面那次 POST，和预检是两次请求  

curl 直接 POST，不发 OPTIONS。Swagger 同源（页面和接口都是 8000）也不走跨源预检。

接口回答预检，不是「FastAPI 用 Allow-Methods 先验业务再响应」。浏览器拿着这张表，自己决定这个网页准不准发。

---

## 4. Cookie 带不带 vs JS 读不读

跨源 `fetch` 默认 `credentials: 'omit'`，不带 Cookie。要带须 `credentials: 'include'`，且还要过 SameSite（见第 1 节）。`include` 是必要条件，不是充分条件。

CORS 不合格时：

| 情况 | 真正的业务请求会不会打到服务器 | JS |
| --- | --- | --- |
| 预检 OPTIONS 失败 | 往往不会发 POST | CORS 报错 |
| 请求已发出，但响应头不对（例如 `Allow-Origin: *` 又带凭证） | 会发，接口可能已 200 | 仍报错，`response.json()` 失败 |

开发者工具 Network 里有时能看到 body，那是浏览器自己看得见；**页面代码拿不到**。不是把 JSON 封装成另一种格式，只是不交给 `fetch().then()`。

谁表态、谁执行：

| 谁 | 干什么 |
| --- | --- |
| 网页服务器 | 提供 HTML/JS，不决定 CORS |
| 页面 JS | 发起跨源请求，可选 `credentials: 'include'` |
| 接口 | 用响应头声明允许哪个源、是否允许带 Cookie |
| 浏览器 | 带不带 Cookie、给不给 JS 读响应 |

带凭证时 `Allow-Origin` 必须是具体源，不能是 `*`，并配 `Allow-Credentials: true`。

---

## 5. HttpOnly Cookie 和 XSS（和 CORS 相邻）

HttpOnly 表示 JS 读不到 `document.cookie`，XSS 不能把 refresh **字符串**拷到另一台机器。

Cookie **只会带给种下它的那台主机**（还要匹配 Path）。`fetch('https://evil.com')` **不会**带上你接口的登录 Cookie。XSS 仍能害你，是因为脚本在**你的页面**里，可以 `fetch` **正确的 FastAPI**（这时才会带 Cookie），再把返回的 JSON 发到外部。

挡的是「长期票被拷走换设备用」，不是「本页内不能冒充你调接口」。正道仍是输出转义 / CSP。设计取舍见 [JWT.md](JWT.md) 第 9 节。

---

## 6. 和本仓库的关系

- R1 验收用 Swagger / curl，不依赖 CORS。
- 演示壳在 5173 调 8000 时，必须在 FastAPI 加 CORS：允许 `http://localhost:5173`，允许 `Authorization` 头，JSON POST 才能过预检。
- 身份永远是 JWT，不要用 Origin 白名单代替鉴权。
