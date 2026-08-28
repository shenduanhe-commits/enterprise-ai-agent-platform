# pnpm 使用方法：

是一个快速、节省磁盘空间的 Node.js 包管理器，它通过内容寻址的方式存储包，所有版本的依赖会集中存储在系统的一个位置，然后通过硬链接的方式链接到项目中，避免了重复安装。

## 做法 A（用 init）

- 根目录 pnpm init → 生成根 package.json
- 手写/创建 pnpm-workspace.yaml
- 创建子包（如 apps/web，可再 pnpm init 或用脚手架）
- 根目录 pnpm install

## 做法 B（不用 init）

直接手写根 package.json 和 pnpm-workspace.yaml，再 pnpm install。效果一样。

推荐顺序可以记成：

```text
根 package.json（可用 pnpm init）
  → pnpm-workspace.yaml
  → 各子包 package.json
  → pnpm install
```

所以：pnpm init 是创建 package.json 的快捷方式，先有 package.json / workspace 配置，再 install；不是“必须先 init 才能用 pnpm”。

pnpm init 的作用只是在当前目录生成一个基础 package.json。你们 monorepo 根目录需要这个文件。

# uv使用方法

## 安装：

### 使用python的包管理工具安装 ，新版本的python自带pip

```text
pip install uv
```

### 使用windows powershell安装

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

- uv python list 查看uv都支持的所有python版本
- uv python install 版本号 安装特定python版本

- uv init 初始化项目
- uv init -p 版本号 创建特定python版本的项目，这是在项目内选择使用哪个版本的python

- uv venv 创建虚拟环境
- uv add 包 安装依赖

- uv sync 安装虚拟环境和依赖。（这会按 pyproject.toml（以及有的话 uv.lock）创建/使用 .venv，并装上所有依赖。）

`.venv\Scripts\activate`

是虚拟环境里的一个脚本，执行后，当前终端会“进入”这个虚拟环境（提示符前可能出现 (.venv)），之后直接敲的 python / pip 就会用这个环境里的。

使用uv命令时会直接使用这个虚拟环境，不需要再进入到这个环境里执行命令。

进入这个虚拟环境后只是可以直接使用虚拟环境里的版本运行命令。

deactivate 退出虚拟环境命令

注意：如果项目更换了存储位置，使用uv run xxx 会报错：uv trampoline failed to canonicalize script path。无法将脚本路径规范化为标准路径。
但是这时\.venv\Scripts\python.exe还能用，只是直接用uv run 命令会有问题。
解决方法：删掉venv，使用uv sync命令重新安装venv和项目依赖

# pnpm 与 uv 对照总结

两者都是包管理工具：pnpm 管前端/Node，uv 管 Python。你们仓库里正好各用一个。

| | pnpm | uv |
|--|--|--|
| 生态 | Node.js / 前端 | Python / 后端 |
| 你们项目位置 | 仓库根 + apps/web | apps/api |
| 配置文件 | package.json、pnpm-workspace.yaml、pnpm-lock.yaml | pyproject.toml、uv.lock、.python-version、README.md |
| 项目本地目录 | node_modules | .venv |
| 全局复用 | store | cache |
| 省空间方式 | 全部硬链接自 store | 尽量硬链接自 cache（有时链接有时会复制） |
| 一键装齐依赖 | pnpm install | uv sync |
| 加依赖 | pnpm add xxx | uv add xxx |
| 跑命令 | pnpm <script> / pnpm exec | uv run <命令> |
| 是否要先激活环境 | 一般不用 | 一般不用（可 activate，非必须） |

## 相同点

- 都有全局缓存/仓库，避免每个项目完整拷多份实体数据
- 项目里仍能看到本地目录（node_modules / .venv），不是“看不见的魔法引用”
- 都用锁文件保证大家装到同一版本
- 安装、运行都可以不手动“激活”一整套环境

## 不同点

- pnpm：面向 JS monorepo，用 workspace 管理多个前端包；根目录加依赖要 -w
- uv：面向 Python，每个项目一个虚拟环境 .venv；uv sync 会自动建环境并装依赖
- 隔离单元：pnpm 是依赖树 + node_modules；uv 是完整 Python 环境 .venv
