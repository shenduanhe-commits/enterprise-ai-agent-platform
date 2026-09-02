# 一次请求的执行过程

请求用哪种 `Content-Type`、成功返回哪种 Response、异常如何变成 JSON：见 [14-R1_FastAPI_ContentType_Response.md](14-R1_FastAPI_ContentType_Response.md)。


1. 中间件前半段（请求进入）
2. Depends：yield 之前 → 打开 db session
3. 执行路由 / Service
   - 成功：return 数据 → FastAPI 做成 Response
   - 失败：raise EAAPException
     - 找到 eaap_exception_handler
     - handler 返回 JSONResponse
4. 已得到最终 Response
5. 请求收尾（返回路径）
   - Depends：yield 之后 → 关闭 db session
   - 中间件后半段（await call_next 之后）  
6. 响应写入 HTTP，客户端收到 → 这次请求结束

- 路由函数：raise 时就结束
- 整个请求：写出响应、收尾做完才结束

## 注意

- 路由函数局部变量：函数结束就按 Python 规则回收，和 HTTP 无关。抛异常 = 该路由函数结束，raise 会立刻离开当前函数，和 return 一样都会结束这次函数调用。
- 数据库连接 / session / 文件 这类靠 Depends(yield) 或上下文管理器管理的，在请求收尾释放
- 若自己在路由里 open() 却没关，不会自动因请求结束而可靠释放，要自己 with 或 finally

一句话：路由逻辑结束 ≠ 资源已释放；像 db 这种依赖资源，是在 Response 生成后的收尾里释放的。

# 异常处理

- Repository → 返回数据 / None，不抛业务异常
- Service → 抛 EAAPException（NotFoundException / BusinessException）
- 路由 → 尽量不写 try/except，保持薄
- main → add_exception_handler 统一转成 HTTP JSON

# 状态码处理

| status | 含义 | 前端统一层可以怎么做 |
| --- | --- | --- |
| 200 | 成功 | 把 data 交给页面 |
| 400 | 业务/参数问题 | 读 body.code / message，可提示或交给页面 |
| 401/403 | 登录/权限 | 跳登录、提示无权限 |
| 404 | 资源不存在 | 提示或进空状态页 |
| 422 | 校验失败 | 展示字段错误 |
| 500 | 服务器错误 | 统一“系统繁忙” |

细逻辑（邮箱已存在、余额不足、状态不允许）→ body.code，不要为每种业务都发明一个 HTTP 码。

## 前端统一拦截可以这样

- if status === 200 → 成功，交给页面
- if status === 401 → 跳登录
- if status === 403 → 无权限提示
- if status === 500 → 通用错误提示
- if status === 400/404 →
  - 默认 toast(body.message)
  - 或若页面声明了要自己处理的 code，再交给页面

页面只对少数特殊 code 写分支，其它走统一提示。
