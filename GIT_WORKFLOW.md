# Git Workflow

## 1 Git分支策略

结构：

```text
main

develop

feature/*
```

说明：

**main**

生产稳定版本

**develop**

开发集成版本

**feature**

功能开发

例如：

```text
feature/auth

feature/rag

feature/agent-runtime
```

## 2 Commit规范

格式：

```text
type(scope): message
```

类型：

| 类型 | 用途 |
|--|--|
| feat | 新功能 |
| fix | Bug修复 |
| docs | 文档 |
| chore | 配置维护 |
| refactor | 重构 |

示例：

```text
feat(agent): add runtime

fix(api): fix config loading

docs: update guide
```
