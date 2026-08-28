# R2 学习笔记：StateSnapshot 是什么

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 日期 | 2026-08-28 |
| 对照代码 | `apps/api/app/ai/runtime/agent_graph.py`（`aget_state`） |
| 概念 | [11-R2_Langgraph_Runtime.md](11-R2_Langgraph_Runtime.md) |
| 一次执行 | [12-R2_Langgraph_Runtime_Flow.md](12-R2_Langgraph_Runtime_Flow.md) |

在 **LangGraph Python** 里，官方把 `StateSnapshot` 定义成：

> **某个 step 开始时，Graph 状态的快照**（`at the beginning of a step`）。

所以 `next` / `tasks` 说的是「这一步马上要跑谁」，不是「上一步刚跑完谁」。有 checkpoint 时，它也就是该存档对应的执行现场。thread 从未 `ainvoke` 过、checkpointer 里没有存档时，`aget_state` 仍会返回一个占位 Snapshot（`values={}`、`metadata=None`），那不是某条真实 checkpoint。

当前官方定义是一个 `NamedTuple`，有 **8 个属性**：

```python
StateSnapshot(
    values=...,
    next=...,
    config=...,
    metadata=...,
    created_at=...,
    parent_config=...,
    tasks=...,
    interrupts=...,
)
```

### 1. `values`

```python
snapshot.values
```

当前 Checkpoint 中的 channel 值（官方：*Current values of channels.*）。本仓库就是 State：`messages` + `iteration`。下面是官方常见的抽象例子，不要把 `user_id` 当成本仓库字段：

```python
class State(TypedDict):
    messages: list
    user_id: int  # 示例用，不是本仓库字段
```

那么：

```python
snapshot.values
```

可能是：

```python
{
    "messages": [...],
    "user_id": 123
}
```

这是最核心的属性，可以理解成：

> **“这一刻 Graph 的 State 是什么？”**

---

### 2. `next`

```python
snapshot.next
```

表示：

> **The name of the node to execute in each task for this step.**

也就是这一步每个 task 要跑的节点名。你们图是直线，所以常见是 `("call_model",)` 或 `("execute_tools",)`。并行时这个 tuple 可以有多项。

如果：

```python
snapshot.next == ()
```

在**已有 checkpoint** 时，表示这个存档上没有下一步要跑的节点，也就是图已经结束。HITL 暂停时 `next` **不是**空的，例如 `("execute_tools",)`。刚写入的 input checkpoint（`step=-1`）通常是 `("__start__",)` 或第一个节点，也不是空。

thread **从未 `ainvoke` 过**时 checkpointer 里没有存档。`aget_state` 仍会返回一个空 Snapshot（`values={}`、`next=()`、`metadata=None`），那是找不到 checkpoint 时的占位，**不是**图判定「下一步为空」。区分两者看 `created_at` / `metadata` 是不是 `None`，或 `values` 里有没有 `messages`。

所以你可以把它理解成：

```text
values → 当前状态
next   → 下一步去哪
```

---

### 3. `config`

```python
snapshot.config
```

官方定义是 “Config used to fetch this snapshot”。有真实 checkpoint 时，返回值会带上该存档的 `checkpoint_id`，不一定等于你传入 `aget_state` 的那份（你往往只传了 `thread_id`）。没存档的占位 Snapshot 里通常 **没有** `checkpoint_id`。

典型情况下（已有存档）：

```python
{
    "configurable": {
        "thread_id": "1",
        "checkpoint_ns": "",
        "checkpoint_id": "..."
    }
}
```

其中最重要的是：

```python
thread_id
checkpoint_id
checkpoint_ns
```

所以：

```python
snapshot.config["configurable"]["thread_id"]
```

可以得到当前 Thread。

而：

```python
snapshot.config["configurable"]["checkpoint_id"]
```

可以定位这个具体的 Checkpoint。

---

### 4. `metadata`

```python
snapshot.metadata
```

Checkpoint 的元数据。

例如：

```python
{
    "source": "loop",
    "writes": {
        "node_a": {
            "foo": "bar"
        }
    },
    "step": 2
}
```

常见的几个字段：

```text
source
writes
step
```

其中：

* `source`：这个 Checkpoint 是怎么产生的，例如 `input`、`loop`、`update`
* `writes`：这一步 Node 写入了什么
* `step`：当前执行到第几个 super-step

官方文档也是这样定义的。

---

### 5. `created_at`

```python
snapshot.created_at
```

Checkpoint 创建时间。

例如：

```python
"2026-08-28T04:30:12.123456+00:00"
```

它主要用于知道：

> **这个 Snapshot 是什么时候产生的。**

---

### 6. `parent_config`

```python
snapshot.parent_config
```

这个非常重要，尤其你现在正在学习 **LangGraph Checkpoint / Resume**。

它表示：

> **用来取出父 Snapshot 的 config（本身不是 Snapshot 对象）。**

例如：

```python
snapshot.config
```

是：

```python
{
    "configurable": {
        "thread_id": "1",
        "checkpoint_id": "C3"
    }
}
```

而：

```python
snapshot.parent_config
```

可能是：

```python
{
    "configurable": {
        "thread_id": "1",
        "checkpoint_id": "C2"
    }
}
```

于是：

```text
C1
 ↓
C2
 ↓
C3
 ↓
C4
```

就形成了 Checkpoint 历史链。

链上最早那条真实 checkpoint（通常是 `source=input` 那条）：

```python
snapshot.parent_config is None
```

`aget_state` 默认返回的是**最新**一条，跑过之后它的 `parent_config` 一般不是 `None`。

官方定义就是“用于获取父 Snapshot 的 config，如果存在的话”。

---

### 7. `tasks`

```python
snapshot.tasks
```

这是当前 Step 对应的 **PregelTask 集合**。

例如：

```python
snapshot.tasks
```

可能是：

```python
(
    PregelTask(
        id="...",
        name="call_model",
        error=None,
        interrupts=(),
        ...
    ),
)
```

一个 `PregelTask` 可以包含：

```text
id
name
error
result
interrupts
state
```

其中：

* `id`：Task ID
* `name`：执行哪个 Node
* `error`：执行过程中有没有错误
* `result`：执行结果
* `interrupts`：这个 Task 是否产生 interrupt
* `state`：如果涉及 Subgraph，可以包含子图 State Snapshot
---

### 8. `interrupts`

```python
snapshot.interrupts
```

表示：

> **这个 Step 中产生、并且目前仍然等待解决的 Interrupt 集合。**

例如你：

```python
interrupt({
    "question": "是否批准？"
})
```

暂停 Graph 后，就可能在：

```python
snapshot.interrupts
```

里看到对应的 interrupt。

这和你最近学习的：

```python
Command(resume=...)
```

关系非常密切。

官方定义是：

> interrupts that occurred in this step that are pending resolution。

---

## 你可以把 8 个属性这样记

我觉得你现在学习 LangGraph，最适合用这个方式理解：

| 属性              | 你可以理解成                     |
| --------------- | -------------------------- |
| `values`        | **现在是什么状态**                |
| `next`          | **接下来去哪**                  |
| `config`        | **我是谁 / 我是哪一个 checkpoint** |
| `metadata`      | **这个 checkpoint 是怎么产生的**   |
| `created_at`    | **什么时候产生的**                |
| `parent_config` | **取出父 checkpoint 的 config**    |
| `tasks`         | **这一阶段有哪些任务**              |
| `interrupts`    | **有没有暂停等待人工处理的事情**         |

尤其是你现在在学 **LangGraph 的 persistence、checkpoint、interrupt、resume**，可以重点抓住这几个关系：

```text
                    StateSnapshot
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
     values            next            tasks
   当前状态          下一步节点        当前任务
        │                                 │
        │                                 ↓
        │                            interrupts
        │                          是否有人机暂停
        ↓
      config
        │
        ├── thread_id
        ├── checkpoint_id
        └── checkpoint_ns
        │
        ↓
 parent_config
        │
        ↓
   取出上一个 Snapshot 的 config
```

所以 **`StateSnapshot` 不只是“State 的副本”**。

更准确地说，有真实 checkpoint 时它是：

> **某个 Thread 在某个 Checkpoint 上、某个 step 开始时的执行现场。**
 
### 9.这些属性中哪些是数组

 如果你说的是 Python 里的**序列类型（list / tuple）**，那么 `StateSnapshot` 的 8 个属性可以这样看：

| 属性              | 是否是数组/序列 | 类型                       |
| --------------- | -------- | ------------------------ |
| `values`        | ❌        | 对本仓库的 `StateGraph` 是 `dict`（类型上也可以是别的） |
| `next`          | ✅        | `tuple[str, ...]`        |
| `config`        | ❌        | `dict`                   |
| `metadata`      | ❌        | `dict \| None`           |
| `created_at`    | ❌        | `str \| None`            |
| `parent_config` | ❌        | `dict \| None`           |
| `tasks`         | ✅        | `tuple[PregelTask, ...]` |
| `interrupts`    | ✅        | `tuple[Interrupt, ...]`  |

所以严格来说，有 **3 个是序列**：

```python
snapshot.next
snapshot.tasks
snapshot.interrupts
```

但这里有一个很容易混淆的地方：

### `next`

```python
snapshot.next
```

通常是：

```python
("node1", "node2")
```

也就是说，**它可以同时包含多个下一步节点**。

---

### `tasks`

```python
snapshot.tasks
```

也是一个 tuple：

```python
(
    PregelTask(...),
    PregelTask(...),
)
```

所以一个 Snapshot 可以对应多个 Task。

---

### `interrupts`

```python
snapshot.interrupts
```

同样是一个 tuple：

```python
(
    Interrupt(...),
    Interrupt(...),
)
```

> **一个 `StateSnapshot` 的 `interrupts` 可以包含多个 interrupt。**

例如并行：

```text
       ┌── node1 ── interrupt A ──┐
START ─┤                          ├── ...
       └── node2 ── interrupt B ──┘
```

那么 Snapshot 中可以表现为：

```python
snapshot.interrupts == (
    Interrupt(...A...),
    Interrupt(...B...),
)
```

而不是只能有一个。

不过这里还要特别区分 **`tasks` 和 `interrupts`**：
`tasks` 是“当前这个 checkpoint 对应的执行任务”，而 `interrupts` 是“其中处于 pending 状态的 interrupt”。这两个概念不是一回事。

---

### 10. Snapshot 里没有 resume 列表

`StateSnapshot` 的 8 个字段 **不含** 当前节点已经收到的 resume 值。

| 你想看的 | 在哪 |
| --- | --- |
| 还没解开的暂停 | `snapshot.interrupts` / `tasks[].interrupts` |
| 已经 `Command(resume=…)` 过的值 | checkpoint 的 pending writes（channel `RESUME`），不在 Snapshot 上 |

`Command(resume=value)` 能不能用单值，只看 **当前 pending 有几条**：1 条可以（并行图里只挂起一条也一样）；≥ 2 条必须 `{Interrupt.id: value}`。同一节点多次 `interrupt()` 时，每次停住通常只有 1 条 pending，resume 值由内部 scratchpad **按下标** 喂给下一次调用。
