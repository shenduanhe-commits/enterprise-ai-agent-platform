# R2 Runtime 学习笔记

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 日期 | 2026-08-28 |
| 对照代码 | `apps/api/app/ai/runtime/agent_graph.py`、`agent_executor.py`、`checkpointer.py` |
| 接口 | [AI_API.md](../02-architecture/AI_API.md) |
| 决策 | [ADR-002](../03-development/ADR/ADR-002-Why-LangGraph.md) |
| 进度 | [STATUS.md](../00-master/STATUS.md)（R2 后端已验收） |

只看 **[12-R2_Langgraph_Runtime_Flow.md](12-R2_Langgraph_Runtime_Flow.md)** 即可按一次「发邮件 → 暂停 → 批准 → 完成」看清每个节点改了哪些数据、结构是什么。`aget_state` 各字段见 **[13-R2_Langgraph_Snapshot.md](13-R2_Langgraph_Snapshot.md)**。本文其余部分是概念与问答。

前端批准按钮、Chat Structured output、Langfuse 明确不做。

---

## 1. 要解决什么

R0/R1 的 Chat 已经能调工具，但是一个 `for` 循环：进程一死就没了，也不能在「发邮件」前停住等人批。

企业 Agent 要的是：**可恢复、可审批、可追踪**。R2 把生产路径换成手写 `StateGraph`，loop 留下对照。

禁止：`create_react_agent`、LangChain 的 `AgentExecutor`、`initialize_agent`。

---

## 2. 一次 Chat 怎么走

```text
JWT
  → POST /api/v1/agents/{id}/chat  或  /chat/stream
  → AgentExecutor（只走图，不走 run_loop）
  → PromptManager + Memory（近 10 条）+ 本轮 user
  → AgentGraph.ainvoke / astream
        thread_id = conversation_id
  → 节点成功结束才写 run_span（interrupt 中断的节点不写）
  → 完成：存 user + assistant，ChatResponse.content 为最终文本
    暂停：只存 user，ChatResponse.content 为 null，pending 有值
  → SSE 最后一帧 done 与非流式同形
```

`run_id` 就是 `conversation_id`。`GET /runs/{id}`、`POST /runs/{id}/resume`、`GET /runs/{id}/spans` 都用这个 id。

---

## 3. 图长什么样

状态只有两样：

```text
messages: list[AIMessage]   # `app.ai.type.AIMessage`（四种 role），operator.add 追加
iteration: int              # 单次 Chat 的 ainvoke 内最多 5 次 call_model
```

节点与边：

```text
START → call_model ─┬─ 无 tool_calls → END
                    └─ 有 tool_calls → execute_tools → call_model
```

| 节点 | 干什么 |
| --- | --- |
| `call_model` | `LLMGateway.chat`（始终带 tools）。无工具则把最终文本写入 `content`，SSE 按 8 字切块。 |
| `execute_tools` | 跑工具。`send_email` 先 `interrupt()`，批准前不执行。 |

第一轮把 Memory 拼好的 messages（含 system）整段喂进去。同一 `thread_id` 再聊时，若 checkpoint 里已有 `messages`，只追加本轮新增消息（通常是 user；有检索命中则是知识库 system + user），避免和 Memory 拼重复。新一轮 Chat 走 `_input_for_turn`，input 会把 `iteration` 写成 `0`（无 reducer，会覆盖），所以上限 5 是**这一次 Chat 的 ainvoke 里**最多进 5 次 `call_model`，不是整个会话累计。`resume` 走 `Command(resume=...)`，**不会**再走 `_input_for_turn`，`iteration` 从 checkpoint 接着加。

对照：`AgentExecutor.run_loop` / `stream_loop` 仍是 `for i in 1..5`，Chat **不再调用**。面试时能指出每一步和图节点的对应即可。

---

## 4. 三套存储，不要混

| 存什么 | 哪里 | 给人看吗 |
| --- | --- | --- |
| 对话历史 | `conversation_message` | 是。`GET /conversations/{id}/messages` |
| 图执行状态 | LangGraph checkpointer 自己的表 | 否。含 tool 消息、`iteration`、interrupt |
| 节点耗时 | `run_span` | 是。`GET /runs/{id}/spans` |

Memory 是「聊过什么」；checkpoint 是「图停在哪、工具消息是什么」。杀 API 再 resume，靠的是后者。`lifespan` 优先开 Postgres checkpointer，连不上则 `InMemorySaver`（重启丢失）。

Windows 上 psycopg 异步需要 Selector 事件循环，所以 `main.py` 在建循环前会切策略。这和业务无关。

---

## 5. HITL

危险工具（当前 `send_email`）`requires_approval=True`。`execute_tools` 里若有待批调用：

1. `interrupt(pending)` 第一次在节点里抛 `GraphInterrupt`（`GraphBubbleUp` 的子类）。LangGraph 运行时接住它、存 checkpoint；`ainvoke` 对 `AgentGraph.run` **仍是正常返回**，只是 dict 里多了 `__interrupt__`。
2. Chat 返回 `status=interrupted`。`ChatResponse.pending` 就是 `interrupt()` 的入参，形状是 `{ pending: [ {id, name, arguments}, ... ] }`（外层字段名和内层 key 都叫 `pending`）。
3. `POST /runs/{id}/resume`，body 为每个 pending `id` 一条 `approved`。漏选 400。
4. LangGraph **从该节点开头重跑**。第二次 `interrupt()` **返回** resume 值，不再抛，然后才执行或拒绝工具。

### 为什么重跑节点

checkpoint 记的是「停在哪个节点」，不是「停在节点第几行」。resume 等于把 `execute_tools` 再执行一遍。因此：**interrupt 之前不能先跑安全工具**，否则重跑会再跑一次。

### LangGraph 怎么知道这次 interrupt 已经有值

不是按 `pending` JSON 去匹配。同一次 node task 里，每次 `interrupt()` 有一个下标；checkpoint 存一份 `resume` **列表**。有值就返回，没值就暂停。

你们现在 **整个节点只 `interrupt()` 一次**，所有待批工具打成一个 payload；`Command(resume={"decisions": {call_id: bool}})` 也是一个 resume 值。`call_send_email_1` 这种 id 是自己拆的，跟 LangGraph 下标不是一回事。

若改成循环里每个工具一次 `interrupt()`，一次 resume 只填一个空位，节点会暂停多次。

### `_emit("interrupt")` 在重跑时还会执行

会执行到那一行，但第二次 `interrupt()` 不抛错。非流式 resume 没有 SSE writer，`_emit` 里的 `RuntimeError` 被吃掉。若以后给 resume 接 stream，应删掉节点里的 interrupt emit，改在 `astream` 结束后看 `snapshot.next` 再推一帧。

### `aget_state` 的 snapshot 长什么样

`snapshot = await self._graph.aget_state(config)` 是 LangGraph 的 `StateSnapshot`。完整 8 个字段见 [13-R2_Langgraph_Snapshot.md](13-R2_Langgraph_Snapshot.md)。代码里真正用到的只有三块：

| 字段 | 类型 | 本仓库怎么用 |
| --- | --- | --- |
| `values` | `dict` | `_input_for_turn`：有没有已有 `messages` |
| `next` | `tuple[str, ...]` | 有真实 checkpoint 时：空 = 已经跑完；`("execute_tools",)` = 还要跑这个节点（HITL 停住） |
| `interrupts` | `tuple[Interrupt, ...]` | `interrupts[0].value` 就是给前端的 `pending` |

`Interrupt` 只有 `value`（你们传入 `interrupt(pending)` 的那个 dict）和框架生成的 `id`（对这次 node task 的 namespace 做 xxHash）。本仓库一次只 `interrupt()` 一次，所以 `snapshot.interrupts` 通常只有 1 条，resume 走单值，**用不到**这个 id；`snapshot.interrupts` ≥ 2 时才用它当 `Command(resume={id: value})` 的键。它不是 `call_send_email_1`，也不是内层待批工具列表的长度。

下面是 Mock 实际跑出来的几种形态。

**A. 这个 thread 从未跑过**（checkpointer 里没有 checkpoint）

```text
values:     {}
next:       ()          # 占位，不是图算出来的「下一步为空」
interrupts: ()
metadata:   None
created_at: None
```

`aget_state` 找不到存档时会**造**这样一个空 Snapshot。`next` 的本意是「这个 checkpoint 上还要跑哪些节点」；没存档就谈不上调度，不要把它和 B/C 的「已经结束」当成同一种含义。`_input_for_turn` 看的是有没有 `messages`，因此会把 Memory 拼好的整段喂进去。

**B. 纯文本 Chat 已结束**（「你好」）

```text
values: {
  "messages": [
    AIMessage(role="user", content="你好"),
    AIMessage(role="assistant", content="Mock AI Response: ..."),
  ],
  "iteration": 1,
}
next:       ()
interrupts: ()
```

这里的 `next=()` 才是图跑完：有真实 checkpoint、`values` 里有 messages。`get_status` 用 `if snapshot.next` 判断，没存档和已结束都会得到 `idle`，那是接口方便，不是说两种 `next` 语义一样。再发一轮只追加新的 user。第一轮 input 含 system，checkpoint 里也会留下 system；下面示例有时省略。

**C. 计算器跑完**（call_model → execute_tools → call_model）

```text
values: {
  "messages": [
    AIMessage(role="user", content="12*7+5"),
    AIMessage(role="assistant", tool_calls=[{calculator...}]),
    AIMessage(role="tool", tool_call_id="call_calculator_1", content="89"),
    AIMessage(role="assistant", content="计算结果是 89"),
  ],
  "iteration": 2,          # 两次 call_model
}
next:       ()
interrupts: ()
```

checkpoint 里 **有 tool 消息**；`conversation_message` 表里通常只有 user + 最终 assistant。

**D. HITL 暂停中**（发邮件，尚未 resume）

```text
values: {
  "messages": [
    AIMessage(role="user", content="请发邮件给老板"),
    AIMessage(role="assistant", tool_calls=[{send_email...}]),
  ],
  "iteration": 1,          # execute_tools 还没跑完，没有 tool 消息
}
next:       ("execute_tools",)
interrupts: (
  Interrupt(
    id="aef2b739fd90b2d8...",          # LangGraph 生成，不是 call_send_email_1
    value={
      "pending": [
        {
          "id": "call_send_email_1",   # 你们的 tool call id
          "name": "send_email",
          "arguments": {"to": "ops@eaap.com", "subject": "...", "body": "..."},
        }
      ]
    },
  ),
)
```

`snapshot.next` 为真 → 拒绝新 Chat、`get_status` = `interrupted`。本仓库正常路径里这就是 HITL；`next` 本身只表示「还有节点要跑」，不是 HITL 专用标志。  
`resume` 用 `interrupts[0].value` 去对 `decisions` 里的 `id`。

**E. HITL resume 且批准之后**

```text
values: {
  "messages": [
    user,
    assistant(tool_calls=send_email),
    AIMessage(role="tool", tool_call_id="call_send_email_1", content="已发送 ..."),
    AIMessage(role="assistant", content="已发送 ..."),
  ],
  "iteration": 2,
}
next:       ()
interrupts: ()
```

形态与 C 相同：空闲、有完整 tool 轨迹。拒绝则 tool 的 content 是 `user denied`。

---

和 snapshot **不是同一个对象**：`ainvoke` 暂停时的返回值是普通 dict，多一个 `__interrupt__`：

```python
{
  "messages": [...],
  "iteration": 1,
  "__interrupt__": (
    Interrupt(value={"pending": [...]}, id="..."),
  ),
}
```

`_result_from_output` 读的是这个。空闲结束时没有 `__interrupt__`，最后一条 messages 就是最终 assistant。

`_config` 在没 checkpointer **或** 没 `thread_id` 时返回 `None`，这时根本不去 `aget_state`，`get_status` 直接当 `idle`。


---

## 6. 节点轨迹

`_call_model` / `_execute_tools` 用 `async with self._node_span(...)` 包起来：

- 进入：记下 `started_at`
- 正常结束 / `return`：写 `ok`（`return` 仍会先跑上下文收尾）
- 普通异常：写 `error`，再 `raise`
- `GraphBubbleUp`：不写 span，原样上抛（所以 HITL 暂停时通常只有已完成的 `call_model`）

图不引用 Service。`AgentExecutor` 造一个闭包 `record(...)`，关掉本次请求的 `db` 和 `conversation_id`，传给图当 `span_recorder`。落库失败只打日志，不打断 Chat。

`async with` 和 `await` 不同：`await` 等一次调用结束；`async with` 把一段代码套进「进入 / 离开」。`yield` 是暂停点，不是 `return`。

---

## 7. SSE

过程事件：`token` / `tool` / `interrupt`。最后一帧是 SSE 的 `event: done`，其 `data` 行与非流式 `ChatResponse` 同形。

`token` 是整段回答切块，不是模型真流式。

---

## 8. Structured output：为什么不算落地

「结构化」指约束 **模型怎么生成**（`response_format`），不是给 HTTP 再包一层 `output`。

Chat 同一轮始终带着 tools，事先不知道这是不是最后一轮，图因此 **不传** `response_format`。Gateway 预留了该参数；Mock 若返回 `{ "answer": "..." }` 会拆进 `content`。真实模型多为散文，原样进 `content`。

对话路径明确不再打一轮 LLM、不加重复的 `output` 字段。以后 citations 用单独字段。

---

## 9. 面试口吻（能讲清这几句就算过）

1. 生产路径是手写 `StateGraph`，不是 `create_react_agent`。loop 留下对照。
2. 对话 Memory 和 checkpoint 不是一张表。
3. HITL 停在节点边界；resume 重跑节点，所以 interrupt 前不能先执行工具。
4. `interrupt()` 用调用次序对齐 resume 列表；我们把多个工具收成一次 interrupt。
5. 轨迹是 `run_span` + GET API，不是 Langfuse（R6）。
6. 最终答案只在 `content`。

---

## 10. 代码地图

| 文件 | 职责 |
| --- | --- |
| `ai/runtime/agent_graph.py` | 图、HITL、span 计时、SSE `_emit` |
| `ai/runtime/agent_executor.py` | Chat 接线、拼 messages、落库、span 闭包 |
| `ai/runtime/checkpointer.py` | Postgres checkpointer |
| `core/lifespan.py` | 启动时打开 checkpointer，失败则内存 |
| `api/v1/runs.py` | 状态 / resume / spans |
| `models/run_span.py` | 轨迹表 |
| `ai/structured.py` | 拆 Mock JSON `answer` |
| `tests/test_agent_graph.py` | 图 / checkpoint / HITL / spans |

---

## 11. 本地怎么验

先 `alembic upgrade head`（需有 `run_span` 表）。演示账号：`user@eaap.com` / `user`。登录与建 Agent 见 [08-JWT.md](08-JWT.md) 第 12 节。

Windows 上若 `uv run alembic` 报 trampoline 路径错误，用：

```bash
cd apps/api
uv run python -m alembic upgrade head
uv run python -m pytest tests/test_agent_graph.py
```

（venv 在别的盘符建的，再整个目录搬走，`alembic.exe` 里会写死旧路径。`python -m` 不走那个 exe。）

```bash
# 计算器：应 completed，再查 spans 为 call_model → execute_tools → call_model
curl -X POST http://localhost:8000/api/v1/agents/<agent_id>/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"conversation_id\":null,\"user_message\":\"12*7+5 等于多少\"}"

curl http://localhost:8000/api/v1/runs/<conversation_id>/spans \
  -H "Authorization: Bearer <access_token>"

# 发邮件：interrupted；resume 后再查 spans
curl -X POST http://localhost:8000/api/v1/agents/<agent_id>/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"conversation_id\":null,\"user_message\":\"请发邮件给老板\"}"

curl -X POST http://localhost:8000/api/v1/runs/<conversation_id>/resume \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"decisions\":[{\"id\":\"<pending_id>\",\"approved\":true}]}"
```

---

## 12. 明确不做（R2）

| 项 | 去向 |
| --- | --- |
| Chat 再打一轮 Structured output | 不做 |
| 前端批准按钮 | 选修；用 Swagger / curl |
| Langfuse | R6 |
| RAG | R3 |
| resume 的 SSE | 未接；非流式 resume 足够 |

---

## 13. 问过的问题

学习 R2 时实际问过的点。正文在上面各节；这里按原问题收口，方便回看。

### 图与 HITL

**为什么不能把不需要审批的工具放到 interrupt 前执行？**  
resume 会从 `execute_tools` **开头**再跑一遍。interrupt 前执行过的安全工具会再执行一次。见第 5 节。

**resume 后重跑工具节点，会不会再次 `_emit(("interrupt", pending))`？**  
会执行到那一行，但第二次 `interrupt()` 是 **返回值** 而不是再暂停。非流式 resume 没有 SSE writer，`_emit` 被吃掉。接 stream 时不要在节点里 emit interrupt。见第 5 节。

**多次 interrupt，图怎么知道这次已经有值了？是不是 checkpoint 存一份结果列表再匹配？**  
是列表，但按下标对齐，不按 `pending` 内容查。同一次 node task 里第几次调用 `interrupt()` 对应 `resume[i]`。你们现在整节点只 interrupt 一次，列表长度是 1。工具 `id` 是自己拆的。见第 5 节。

**给 resume 也接上 stream，代码应该是什么样的？**  
节点里只 `interrupt()`；`astream(Command(resume=...))` 结束后若 `snapshot.next` 再 yield 一帧 interrupt。Executor 对齐 `execute_stream`，只补 assistant。路由 `POST /runs/{id}/resume/stream`。R2 未做。

**图状态什么时候写到 Postgres？每步都存还是只存最新？**  
`ainvoke` 收到 input 时就会先建一条 checkpoint（第一步开始前已经有了）。之后每个 **super-step 结束**再 `aput` 一次（你们图是直线，一步通常就是一个节点），`interrupt` 时也会存。不是等整轮 Chat 返回。存的是当时的 messages / iteration，所以能停在工具前。历史 checkpoint 都在，`aget_state` 默认取最新。

**lifespan 里为什么不能 `app.state.checkpointer = open_postgres_checkpointer()`？**  
那是异步上下文，必须 `async with`（或 `AsyncExitStack.enter_async_context`）才能拿到实例并在关应用时拆掉连接池。直接赋值得到的是没进入的上下文。

### `async with` 与 `_node_span`

**`async with self._node_span("call_model")` 是什么意思？**  
给节点主体套一层计时：进去记 `started_at`，出来写 span。本身不调 LLM。

**`async with` 怎么用？和 `await` 有什么不同？**  
`await` 等一次调用的返回值。`async with` 管一段代码的进入/离开。`@asynccontextmanager` + `yield`：yield 前准备，yield 后收尾。

**`_node_span` 能捕获 async with 体里的异常吗？**  
能。体插在 `yield` 处，等于跑在 `_node_span` 的 `try` 里。捕获后你们每条分支都 `raise`，并不吞掉。

**为什么不是「父函数捕获子函数」？**  
`_node_span` 在 `yield` 处暂停、还没返回。体不是在它结束之后才跑。

**`await self._node_span("call_model")` 还能捕获体里的异常吗？**  
不能。而且现在带了 `@asynccontextmanager`，一般也不能 `await`（不是协程）。

**体里 `return` 了，async with 后面的代码还会跑吗？**  
同一函数里后面的语句不会。但 `yield` 之后的收尾（写 `ok` span）会先跑完再真正 return。

**没有 `return`、后面还有代码时，先跑 yield 后面还是 async with 后面？**  
先跑 `_node_span` 里 `yield` 之后（含 `else`），再跑 `async with` 块后面。

**什么时候进 `_node_span` 的 `else`？**  
`try`（也就是 `yield` / 体）成功结束时，包括体里 `return`。异常走 `except`。

**yield 后面如果还有代码，会先于 `else` 执行吗？**  
会。`else` 等整个 `try` 成功结束。你们的 `try` 里目前只有 `yield`，写 `ok` 就放在 `else`。

**如果没有 `except GraphBubbleUp: raise`，异常会怎样？**  
`GraphBubbleUp` 也是 `Exception`，会进 `except Exception`，HITL 被记成 `error` span，但最后仍 `raise`，图还是会停。中断还在，账记错了。

**`raise` 后面没有参数，默认抛捕获的那个吗？**  
对，且保留原来的 traceback。只能写在 `except` 里。

**`_node_span` 不捕获，异常还会抛出吗？**  
会。不捕获只是失败时不写 `error` span，异常照样给 LangGraph。

**`yield` 只会搭配 `async with` 用吗？**  
不是。更常见是生成器 + `for` / `async for`。`async with` 只是「只 yield 一次」的那种用法。

**`yield` 之后 `await` 拿到值，函数就结束、后面不跑了吗？**  
不是。`yield` 是暂停。`anext` 只推进到 yield；后面要再推进（或 `async with` 离开）才跑。`return` 才会结束。

**`gen = await self._node_span("call_model")` 会得到 `"paused"` 吗？**  
不会。上下文对象不能 `await`。裸 `yield` 交出的是 `None`。要取值用 `await anext(gen)`，且得写成 `yield "paused"`。

### span 怎么进库

**`_span_recorder` 怎么把数据存到数据库？**  
图只调用传入的回调。Executor 的闭包里 `RunSpanService.create_span` → Repository `add` + `commit`。见第 6 节。

**它怎么知道调用哪个 Service？又没绑定？**  
图不选 Service。绑在 `AgentExecutor.self.span_service` 上；`record` 是嵌套函数，闭包带着这个 `self`。

### 工具与验收

**换目录，之前的 venv 就不行了？**  
`python.exe` 还能用。`alembic.exe` / `pytest.exe` 是 uv trampoline，写死了创建时的绝对路径。用 `python -m alembic`。见第 11 节。

**`uv run install` 报 `Failed to spawn: install`？**  
`uv run X` 表示装环境再运行程序 `X`。没有 `install` 这个命令。同步环境用 `uv sync`。

**怎么查看当前迁移状态？**  
`uv run alembic current`。有 `(head)` 即已最新。`history` / `heads` 看文件链。

**R2 是不是已经完成了？**  
后端是：图、checkpoint、HITL、spans。Chat Structured output 和前端批准明确不做。Langfuse 属 R6。

### Structured output（决策过程里问过的）

**是不是所有返回都封装成模型响应再拆给前端？`output` 是什么？**  
不必。用户看见的回复就是 `content`。不要再包一层和 `content` 重复的 `output`。系统信息（如以后的 citations）用单独字段。

**Structured output 是为了响应统一吗？要把 `content` 改成 dict 吗？**  
不是 HTTP 包一层。是约束模型生成。`content` 保持 `str`。

**图调模型时没传 `response_format`，怎么知道是不是最后一轮？**  
事先不知道。有 tools 的同一轮里，要等模型回复后才知道还要不要调工具。所以图不传 `response_format`。

**`parse_final_answer` 为什么还要？真实模型会返回 `{"answer":"89"}` 吗？**  
多为散文，函数等于原样返回。Mock 才可能是 JSON。留着不报错，价值低，未再加 finalize 节点。

**Anthropic 的 `response_format` 好像没用到？**  
忽略该参数。各家能力不同，不能靠它保证前端看到同一形状。统一靠 `ChatResponse.content`。

### 关于传递 resume 的问题

看的是 **当前 `snapshot.interrupts` 有几条**，不是图里有没有并行节点。

| 当时 pending | 单值 `Command(resume=value)` |
| --- | --- |
| 1 条 | 可以，就喂给这一条 |
| ≥ 2 条 | 不行，必须 `{Interrupt.id: value}` |

所以并行图里只有一个节点真的 `interrupt()` 了，仍然可以单值，和直线图停一次一样。

同一节点里多次 `interrupt()`：一次只抛一条，pending 通常是 1，因此每次 resume 也是单值；节点重跑后已有值的调用直接返回，下一个没值的再停（内部按下标对齐）。

两条以上同时挂起（典型是同一超步里多个节点都 interrupt）才要按 id 点名：

```python
Command(
    resume={
        "interrupt-id-A": {"result": "approved"},
        "interrupt-id-B": {"result": "rejected"},
    }
)
```

键必须是 `Interrupt.id`（这次 node task namespace 的 xxHash），不是 tool call id。

你们现在 `_execute_tools` 只 `interrupt()` 一次，走单值：

```python
Command(resume={"decisions": {call_id: bool}})
```

这是 **一个** resume 值（里面自己拆了各工具的批准），不是上面那种 id 映射。

`StateSnapshot` **没有** resume 列表字段。已提交的 resume 存在 checkpoint 的 pending writes（channel `RESUME`）里，节点重跑时由内部 scratchpad 按下标配对。