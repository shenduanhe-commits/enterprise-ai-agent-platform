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

工具集走 `agent_tool`（R4 已落地），不写在 Agent 行上。是否启用 RAG、HITL 策略仍可后补字段。

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
              KnowledgeRetriever（拼 【知识库】，R3）
                         │
                         ▼
              ┌── Runtime graph ──┐
              │  LLMGateway (+ tools)    │
              │  ToolManager / MCP       │
              │  interrupt HITL (R2)     │
              └──────────┬───────────────┘
                         ▼
              persist messages + trace
```

| 组件 | 现状 | 目标 |
| --- | --- | --- |
| `AgentExecutor` | 非流式/SSE 走 `StateGraph`；loop 留下对照 | 对照保留 |
| LangGraph `StateGraph` | 手写 `call_model` / `execute_tools`；最多 5 轮 | R2 生产路径（已落地） |
| `LLMGateway` | chat + tool_calls；`response_format` 预留 | 图侧按需传入；真流式仍缺 |
| `PromptManager` | 最新 prompt 或 system_prompt | 保留；变量渲染已有 |
| `MemoryManager` | 最近 10 条 | 与 checkpoint 分工：Memory=对话，Checkpoint=图状态 |
| `ToolManager` | 每请求按绑定组装；builtin + MCP | R4 已落地 |
| RAG | Chat 拼 messages 时检索（非图节点）；hybrid + rerank + citations | 已落地 |

---

## 4. 当前执行循环（对照 loop，非生产）

生产 Chat 走 `StateGraph`。`run_loop` / `stream_loop` 仅对照：

```
messages = [system, *recent, user]
for i in 1..5:
    response = gateway.chat(provider, model, messages, tools)
    if not response.tool_calls:
        return response
    messages += assistant + tool_results
raise AgentRuntimeException
```

## 5. 已落地执行图（R2）

状态：`messages`、`iteration`。节点：`START → call_model ⇄ execute_tools → END`。

Checkpointer：优先 Postgres，失败则 `InMemorySaver`。`thread_id = conversation_id`。

HITL：`send_email` 在 `execute_tools` 里 `interrupt()`；`POST /api/v1/runs/{id}/resume`。不单独拆 `wait_human` 节点。

轨迹：节点进出写 `run_span`；`GET /api/v1/runs/{id}/spans`。

Chat 最终答案只在 `content`。不在对话路径启用 Structured output。禁用 `create_react_agent`。

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

Runtime 只认「描述 + 调用」，不关心工具在进程内还是 MCP（`McpTool` 走 `tools/call`）。

策略：

- 白名单：从未 PUT 绑定则全部 enabled；空绑定则模型看不到任何工具。
- 超时与错误写成 tool message，不要炸死图。
- 写操作默认 HITL（`send_email`）。

---

## 7. Memory 与知识

| 种类 | 实现 | 阶段 |
| --- | --- | --- |
| 短期 | `conversation_message` 最近 N 条 | 已有 |
| 执行状态 | LangGraph checkpoint | 已落地 |
| 长期企业知识 | Postgres `knowledge_document` + 磁盘原文 + Qdrant `eaap_chunks` | 已落地 |
| 用户长期偏好 | 不做，除非有明确场景 | 选修 |

不要用 LangChain 旧 Memory 类。

---

## 8. 多 Agent（R5）

```
Supervisor ── knowledge（检索）
           └─ writer（写简报；默认同进程，可 A2A HTTP）
```

- 用户话含「简报」「写一页」才进 Supervisor；计算器 / 普通 RAG 仍单 Agent。
- 路由是确定性的，不是一个 prompt 分饰三角色。
- Writer 失败立即 `failed`，不自动重试。
- `A2A_WRITER_URL` 指向另一进程时，Supervisor 只发 `eaap-a2a/v0` 信封，不直接 `write_brief()`。对端用 `app.ai.a2a.standalone`（`pnpm dev:api-writer`，默认 :8001），只挂信箱。

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

R3：黄金问答（RAG，`apps/api/evals/`）。R6：trajectory（工具序列是否合理）+ LLM-as-judge。评测是 Runtime 的一部分，不是上线后补丁。
