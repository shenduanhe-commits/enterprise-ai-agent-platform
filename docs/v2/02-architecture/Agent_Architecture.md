# Agent 架构 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/02-architecture/Agent_Architecture.md`、`docs/Agent设计文档 V1.0.md` |

---

## 1. Chatbot vs Agent

```
Chatbot:  问题 → LLM → 回答
Agent:    目标 → 状态循环 →（思考 / 工具 / 检索 / 等待人）→ 结果
```

企业要的是后者，且必须 **可控**：有最大轮次、有权限、有暂停、有轨迹。

V1 一上来画 Supervisor 多 Agent。V2 承认：**先把单 Agent 做成可恢复的图，再拆多 Agent。**

---

## 2. Agent 作为数据，不是类爆炸

一个 Agent 行数据描述身份，Runtime 是共享引擎。

| 字段（已落地） | 含义 |
| --- | --- |
| name / description | 身份 |
| provider / model_name | 用哪家模型 |
| system_prompt | 默认系统提示 |
| status | active / disabled / archived |
| created_by | 所有者 |
| prompts[] | 可版本化的模板（优先于 system_prompt） |

目标字段（R4）：绑定的 tool 列表、是否启用 RAG、HITL 策略。

不要为「销售 Agent / HR Agent」各写一套 Python 类，用不同 prompt + 工具集区分。

---

## 3. Runtime 组成

```
                    User message
                         │
                         ▼
              PromptManager  +  Memory (recent N)
                         │
                         ▼
              ┌── Runtime loop / graph ──┐
              │  LLMGateway (+ tools)    │
              │  ToolManager / MCP       │
              │  RAG retrieve (R3)       │
              │  interrupt HITL (R2)     │
              └──────────┬───────────────┘
                         ▼
              persist messages + trace
```

| 组件 | 现状 | 目标 |
| --- | --- | --- |
| `AgentExecutor` | for-loop，最多 5 轮 | 对照实现，保留 |
| LangGraph `StateGraph` | 无 | R2 生产路径 |
| `LLMGateway` | chat + tool_calls；`response_format` 预留 | 图侧按需传入；真流式仍缺 |
| `PromptManager` | 最新 prompt 或 system_prompt | 保留；变量渲染已有 |
| `MemoryManager` | 最近 10 条 | 与 checkpoint 分工：Memory=对话，Checkpoint=图状态 |
| `ToolManager` | 内存注册 calculator | R4 注册表 + MCP |
| RAG | 无 | R3 作为节点或工具 |

---

## 4. 当前执行循环（已落地）

```
messages = [system, *recent, user]
for i in 1..5:
    response = gateway.chat(provider, model, messages, tools)
    if not response.tool_calls:
        return response
    messages += assistant + tool_results
raise AgentRuntimeException
```

缺口：OpenAI 丢 tool_calls；tool schema 为空；无流式；无持久图状态。

这套 loop 必须能向面试官讲清，再升级到图。

---

## 5. 目标执行图（R2）

状态建议：

```text
messages: list[AIMessage]
iteration: int
pending_tool_calls: list | None
hitl: { pending: [{ id, name, arguments }], decisions: [{ id, approved }] } | None
error: str | None
```

节点：`build_prompt` → `call_model` →（条件）`execute_tools` / `wait_human` / `finalize`。

Checkpointer：Postgres 或 Redis。杀进程后用 thread_id（建议=conversation_id）恢复。

HITL：危险工具进 `wait_human`，暴露 `POST /.../resume`。

只用 `langchain.agents.create_agent` 当薄封装；复杂边必须手写 StateGraph。禁用已弃用 prebuilt。

---

## 6. 工具

进程内工具：

```python
class BaseTool:
    name: str
    description: str
    async def execute(**kwargs): ...
    @property
    def schema(self) -> dict:  # OpenAI function JSON Schema
```

R4 后 Runtime 只认「描述 + 调用」，不关心工具在进程内还是 MCP。

策略：

- 白名单：Agent 未绑定则模型看不到。
- 超时与错误写成 tool message，不要炸死图。
- 写操作默认 HITL。

---

## 7. Memory 与知识

| 种类 | 实现 | 阶段 |
| --- | --- | --- |
| 短期 | `conversation_message` 最近 N 条 | 已有 |
| 执行状态 | LangGraph checkpoint | R2 |
| 长期企业知识 | Qdrant + 文档表 | R3 |
| 用户长期偏好 | 不做，除非有明确场景 | 选修 |

不要用 LangChain 旧 Memory 类。

---

## 8. 多 Agent（R5，不是现在）

```
Supervisor ── Knowledge Agent
           └─ Writer Agent
```

- 每个专职 Agent 仍是同一 Runtime + 不同配置。
- 协作用子图或 A2A 消息，不用函数直接互调冒充协议。
- 默认先问：单 Agent + 工具是否够用。不够再用 Supervisor。

---

## 9. 失败与边界

| 情况 | 行为 |
| --- | --- |
| 模型无 tool_calls | 结束 |
| 工具不存在 | tool 角色返回 `tool not found`，继续一轮 |
| 超过 max iterations | `AgentRuntimeException` |
| Provider 不支持 | `LLMException` |
| Prompt 变量缺失 | `BusinessException` |
| MCP 不可达 | 明确错误，降级，不卡死 |

---

## 10. 评测

R3 起：黄金问答（RAG）。R6：trajectory（工具序列是否合理）+ LLM-as-judge。评测是 Runtime 的一部分，不是上线后补丁。
