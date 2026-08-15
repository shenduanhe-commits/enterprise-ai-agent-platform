# 用户故事 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 替代 | `docs/01-product/UserStory.md`（V1） |

格式：作为 [角色] 我希望 [目标] 从而 [价值]。验收以 API 为主，UI 为辅。

---

## Epic 总览

| Epic | 阶段 | 优先级 |
| --- | --- | --- |
| E00 Runtime 闭环 | R0 | P0 |
| E01 认证与隔离 | R1 | P0 |
| E02 流式对话与会话 | R1 | P0 |
| E03 Agent 管理（鉴权后） | R1 | P0 |
| E04 生产 Runtime | R2 | P0 |
| E05 知识库与 RAG | R3 | P0 |
| E06 工具平台与 MCP | R4 | P1 |
| E07 多 Agent | R5 | P2 |
| E08 治理与作品 | R6 | P1 |

V1 的 Workflow Designer、组织管理 Epic 不列入主路径。

---

## E00 Runtime 闭环（R0）

### US-000 工具循环可用

作为开发者，我希望 Chat 在模型返回 tool_calls 时能执行工具并再次询问模型，从而证明 Runtime 不是单轮补全。

验收：

- Qwen 或 Mock 下，「12*7+5」会调 calculator 并给出数字答案。
- 无 tool_calls 时直接返回文本。
- 超过最大轮次返回明确错误，不死循环。
- OpenAI/Anthropic 与 Qwen 一样解析 tool_calls。

### US-000b 密码只在服务端哈希

作为用户，我希望注册时只提交明文密码一次，从而避免把哈希当密码协议。

验收：请求体是 `password`；库中是 Argon2/bcrypt；无法用明文当 `password_hash` 写入。

---

## E01 认证与隔离（R1）

### US-001 注册登录

作为员工，我希望用邮箱注册并登录，从而获得访问令牌。

验收：`POST /auth/register`、`POST /auth/login` 返回 access + refresh；错误密码 401。

### US-002 资源隔离

作为员工，我希望只能看到自己的 Agent 和会话，从而避免数据串读。

验收：带他人 ID 访问返回 404 或 403；未带 JWT 返回 401。

---

## E02 流式对话与会话（R1）

### US-003 流式 Chat

作为员工，我希望看到模型逐 token 输出，从而确认系统可交互。

验收：`POST /agents/{id}/chat/stream`（或等价）为 SSE；客户端断开后服务端停止生成。

### US-004 多轮与历史

作为员工，我希望同一 `conversation_id` 继续聊，并拉到历史。

验收：第二轮能引用第一轮信息；`GET` 消息按时间序。

### US-005 自动建会话

作为员工，我希望不传 `conversation_id` 时系统建新会话。

验收：响应带回新 `conversation_id`。

---

## E03 Agent 管理（R1）

### US-006 创建与配置 Agent

作为开发者，我希望指定 name、provider、model、system_prompt 创建 Agent。

验收：创建后 GET 一致；未登录不可创建。

### US-007 列出我的 Agent

作为开发者，我希望列出自己的 Agent 并按 status 区分。

验收：列表不含他人 Agent；status 至少有 active / disabled。

---

## E04 生产 Runtime（R2）

### US-008 图执行与对照

作为开发者，我希望生产路径走 LangGraph，且与自研 loop 对同一用例结果一致（允许文本措辞差，工具序列应一致）。

验收：对照测试；配置可切 runtime。

### US-009 进程重启可恢复

作为运维，我希望执行中途杀 API 后能从 checkpoint 继续。

验收：resume 不从头重跑已完成的工具。

### US-010 HITL

作为管理员，我希望「发送」类工具执行前暂停。

验收：未 resume 则工具未执行；resume 后执行并进入下一节点。

---

## E05 知识库与 RAG（R3）

### US-011 上传文档

作为知识管理员，我希望上传 Markdown/PDF，看到处理完成状态。

验收：状态 pending → ready / failed；失败有原因。

### US-012 带引用问答

作为员工，我希望答案带来源文档名（及 chunk）。

验收：手册题有 citation；问无关手册内容时不得伪造手册出处。

### US-013 RAG 评测

作为开发者，我希望有离线黄金集分数。

验收：至少 20 条；报告含 recall@k 与引用正确率。

---

## E06 工具与 MCP（R4）

### US-014 为 Agent 勾选工具

作为开发者，我希望不同 Agent 有不同工具集。

验收：未勾选的工具模型不可见也调不到。

### US-015 MCP 工具

作为开发者，我希望 Runtime 从 MCP Server 发现工具并调用。

验收：Server 停止时返回明确错误，不挂死。

---

## E07 多 Agent（R5）

### US-016 协作简报

作为员工，我希望「根据知识库写一页简报」由检索与写作分工完成。

验收：trace 或响应中能看到至少两个 `agent_name`；失败可中止。

---

## E08 治理（R6）

### US-017 看一次执行

作为开发者，我希望打开一次 Chat 的 node/工具/耗时。

验收：Langfuse 或内部 trace API 能对应到 `conversation_id`。

### US-018 基础护栏

作为管理员，我希望明显的提示注入和超权工具调用被拒绝。

验收：有针对性测试用例。
