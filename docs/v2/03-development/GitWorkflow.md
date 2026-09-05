# Git 工作流 V2.1

| 项目 | 内容 |
| --- | --- |
| 版本 | V2.1 |
| 模型 | **GitHub Flow**（与常见 Web / Agent 团队一致） |
| 替代 | `docs/03-development/GitWorkflow.md`、根目录 `GIT_WORKFLOW.md` |

---

## 1. 采用 GitHub Flow

```
main              随时可 clone、可演示、可跑测试
feature/<scope>   短命分支，只做一件事，PR 合回 main 后删除
```

不用长期 `develop` / `release` / `hotfix`。那是经典 Git Flow，本仓库和多数 Agent 岗位都不需要。

规则：

- `main` 只收能运行的代码。半成品留在 feature 分支。
- 分支活不过一个故事。一个 PR 不要同时做 Runtime 和 RAG。
- **一个 R 阶段 = 一条 feature 分支。** 做完必须先提交、推远程、合进 `main`，再从最新 `main` 开下一阶段的分支。
- 禁止在 `feature/rN-*` 的未提交改动上直接开始 R(N+1)，也禁止从脏工作区 `checkout -b` 当「下一步」。
- 即使用你一个人，也走 PR，练说明和审查。一人仓库也可本机 `merge` 进 `main` 再 push，顺序不变。

---

## 2. 分支命名

按 V2 阶段：

```
feature/r0-runtime-hardening
feature/r1-auth-sse
feature/r2-langgraph
feature/r3-rag
feature/r4-mcp
feature/r5-multi-agent
feature/r6-portfolio
```

更小的修补：`fix/chat-tool-calls`、`docs/update-status`。

**当前：** R4 合入 `main` 后，下一阶段从最新 `main` 继续 `feature/r5-multi-agent`。

---

## 3. 日常步骤

```bash
git checkout main
git pull

git checkout -b feature/r4-mcp

# 只做本阶段。工作、小步提交
git add <相关文件>
git commit -m "feat(r4): add MCP client and tool catalog"

git push -u origin HEAD
# 开 PR → 目标 main → CI 绿 → 合并
# 或：git checkout main && git merge feature/r4-mcp && git push origin main
```

### 阶段切换（必须按这个顺序）

```bash
# 1. 当前分支没有未提交的「下一阶段」代码
git status

# 2. 本阶段提交已在 feature/rN-* 上
git push -u origin HEAD

# 3. 合进 main 并推远程
git checkout main
git pull
git merge feature/rN-*
git push origin main

# 4. 这时才允许开下一阶段
git checkout main
git pull
git checkout -b feature/r(N+1)-*
```

中途要切分支：先 `git stash -u`（或先提交），禁止把两个 R 的改动堆在同一个脏工作区。

提交格式：`type(scope): message`

`feat` / `fix` / `docs` / `test` / `refactor` / `chore`

---

## 4. 约定

- 不提交 `.env`、密钥、`__pycache__`、`node_modules`。
- 不跳过 hook（不用 `--no-verify`）。
- 不 force push `main`。
- 文档只改 `docs/v2/` 与根 `DOCUMENTATION.md`，不回写 V1。
- 阶段完成时更新 `docs/v2/00-master/STATUS.md`。
- 合并前：`cd apps/api && uv run pytest` 通过。

---

## 5. 当前仓库怎么过渡

历史上有过 `develop`（V2 文档曾推到这里）。从现在起：

1. 新工作开 `feature/*`，不再往 `develop` 堆长期提交。
2. 每个 R 用对应的 `feature/rN-*`，做完再合 `main`，再开下一支。
3. `develop` 不再作为开发主线；需要时可以删或只作只读备份。
