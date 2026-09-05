# MCP的三种传输方式

```
             MCP Client
                 │
      ┌──────────┼──────────┐
      │          │          │
    stdio     Streamable    SSE
                 HTTP       （Legacy）
      │          │          │
      ▼          ▼          ▼
 MCP Server   MCP Server   MCP Server
 （子进程）   （HTTP服务）  （HTTP服务）

 最核心的区别
```

可以把它简单理解成：

stdio = 我就在你电脑上，直接启动一个 MCP Server 和它通信（拉起一个 Python 进程，stdin/stdout 说话）。

EAAP
 │
 └── 启动 MCP Server 子进程
          │
       stdin/stdout

Streamable HTTP = MCP Server 是一个独立的网络服务，我通过 HTTP 调它。

EAAP
 │
 │ HTTP
 ▼
MCP Server

SSE = 老的 HTTP + SSE 通信方案，现在主要为了兼容旧 MCP Server。

Client ──HTTP──> Server
Client <──SSE── Server

所以最重要的是记住：

本地工具 → stdio

远程/企业级 MCP Server → Streamable HTTP

SSE → 了解即可，做新项目一般不用。

---

# MCP中client的连接方式


| 方式                  | 传给 `Client` 的参数         | 示例                                    | Client 如何识别                                 |
| ------------------- | ----------------------- | ------------------------------------- | ------------------------------------------- |
| **MCPServer 实例**    | `MCPServer` 对象          | `Client(mcp)`                         | 看到是 Server 对象 → **进程内连接**                   |
| **stdio**           | `StdioServerParameters` | `Client(StdioServerParameters(...))`               | 看到是 `StdioServerParameters` → 启动子进程 + stdio |
| **Streamable HTTP** | URL 字符串                 | `Client("http://localhost:8000/mcp")` | 看到是 `str` → Streamable HTTP                 |
| **SSE**             | SSE Transport           | `Client(sse_client(url))`             | 其他 Transport → 直接使用该 Transport              |



| Client 参数                            | 连接模式                       | 是否有网络 | 是否独立进程 |
| ------------------------------------ | -------------------------- | ----- | ------ |
| `Client(mcp)`                        | **In-process / In-memory** | ❌     | ❌      |
| `Client("http://...")`               | **Streamable HTTP**        | ✅     | ✅      |
| `Client(StdioServerParameters(...))` | **stdio**                  | ❌     | ✅      |
| `Client(sse_client(...))`            | **SSE**                    | ✅     | ✅      |


### client和server侧的参数设置对比

| Client 连接方式         | Client 侧                             | Server 侧         | Server 是否需要 `run()`        |
| ------------------- | ------------------------------------ | ---------------- | -------------------------- |
| **MCPServer 实例**    | `Client(mcp)`                        | `MCPServer(...)` | ❌ 不需要                      |
| **stdio**           | `Client(StdioServerParameters(...))` | `MCPServer(...)` | ✅ `run("stdio")`           |
| **Streamable HTTP** | `Client("http://.../mcp")`           | `MCPServer(...)` | ✅ `run("streamable-http")` |
| **SSE**             | `Client(sse_client(...))`            | `MCPServer(...)` | ✅ `run("sse")`             |


注意：使用mcpserver实例的时候，传输方式不是 stdio，也不是 Streamable HTTP，也不是 SSE。它使用的是：In-process / In-memory 也就是进程内直连（Client 和 Server 在同一个 API 进程里）。官方文档明确说明：没有子进程、没有端口、没有 HTTP。

---

# MCP能力

MCPServer 向 Client 提供若干能力。Tools、Resources、Prompts 是三类主要内容；Completions 和它们 **同级**（都是 Server 能力 / Client API），但用途是给 Prompt、Resource Template 的参数做自动补全，不是第四种「给模型看的内容」。


| MCPServer 提供的能力        | Server 端注册方式               | Client 调用                                       | 主要用途                   |
| ---------------------- | -------------------------- | ----------------------------------------------- | ---------------------- |
| **Tools**              | `@mcp.tool()`              | `list_tools()` / `call_tool()`                  | **让模型执行操作**            |
| **Resources**          | `@mcp.resource()`          | `list_resources()` / `read_resource()`          | **给模型/应用提供数据**         |
| **Resource Templates** | `@mcp.resource("...{id}")` | `list_resource_templates()` / `read_resource()` | **提供动态数据**             |
| **Prompts**            | `@mcp.prompt()`            | `list_prompts()` / `get_prompt()`               | **提供用户可选择的 Prompt 模板** |
| **Completions**        | `@mcp.completion()`        | `complete()`                                    | **参数自动补全**             |



```
                                    MCPServer
                                        │
         ┌──────────────┬───────────────┼───────────────┐
         │              │               │               │
       Tools        Resources        Prompts       Completions
       执行操作        提供数据         提供模板         参数补全
         │              │               │               │
         ▼              ▼               ▼               ▼
   list_tools()   list_resources()  list_prompts()  complete()
         │     list_resource_templates() │
         ▼              │               ▼
    call_tool()   read_resource()   get_prompt()
```


| 分类             | API                         | 输入                 | 输出                            | 你可以把它理解成          |
| -------------- | --------------------------- | ------------------ | ----------------------------- | ----------------- |
| **Tool**       | `list_tools()`              | `cursor`           | `ListToolsResult`             | “你有什么工具？”         |
| **Tool**       | `call_tool()`               | `name + arguments` | `CallToolResult`              | “帮我执行这个工具”        |
| **Resource**   | `list_resources()`          | `cursor`           | `ListResourcesResult`         | “你有哪些数据？”         |
| **Resource**   | `list_resource_templates()` | `cursor`           | `ListResourceTemplatesResult` | “你有哪些动态数据？”       |
| **Resource**   | `read_resource()`           | `uri`              | `ReadResourceResult`          | “把这个数据给我”         |
| **Prompt**     | `list_prompts()`            | `cursor`           | `ListPromptsResult`           | “你有哪些 Prompt？”    |
| **Prompt**     | `get_prompt()`              | `name + arguments` | `GetPromptResult`             | “把这个 Prompt 渲染出来” |
| **Completion** | `complete()`                | `ref + argument`   | `CompleteResult`              | “帮我补全参数”          |


### 在项目中的使用
                         EAAP
                          │
                     Agent Runtime
                          │
                         LLM
                          │
                    Tool Calling
                          │
                     MCP Client
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
           Tools      Resources      Prompts
             │            │            │
             └────────────┼────────────┘
                          │
                     MCP Server