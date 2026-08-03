# SQLAlchemy / asyncpg / Alembic / psycopg2-binary 使用总结

四者分工可以记成：

| 工具 | 角色 |
|--|--|
| SQLAlchemy | ORM / 引擎 / Session，用 Python 操作数据库 |
| asyncpg | FastAPI 异步运行时的 Postgres 驱动 |
| psycopg2-binary | Alembic 等同步场景的 Postgres 驱动 |
| Alembic | 表结构迁移（建表、改列等） |

关系：

```text
FastAPI 请求
  → SQLAlchemy AsyncSession
  → asyncpg
  → PostgreSQL
改模型后
  → Alembic 生成/执行 migration
  → SQLAlchemy 同步 Engine
  → psycopg2
  → PostgreSQL
```

## 1. SQLAlchemy（核心）

干什么： 定义模型、建引擎、开 Session、写查询。

你们项目里：

- 模型：app/models/user.py（User 继承 Base）
- 连接：app/core/database.py

常用概念：

```python
# 异步引擎
engine = create_async_engine("postgresql+asyncpg://...")
# Session 工厂
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)
# 依赖注入取 Session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

业务里典型用法：

```python
result = await session.execute(select(User).where(User.email == email))
user = result.scalar_one_or_none()
session.add(user)
await session.commit()
```

安装：

```bash
uv add sqlalchemy
```

## 2. asyncpg（异步驱动）

干什么： 给 SQLAlchemy 异步引擎真正去连 Postgres。

URL 形式：

```text
postgresql+asyncpg://用户:密码@主机:端口/库名
```

你们代码里把 .env 的：

```text
postgresql://...
```

替换成：

```text
postgresql+asyncpg://...
```

安装：

```bash
uv add asyncpg
```

注意：

- 给 FastAPI / create_async_engine 用
- 不要直接拿带 +asyncpg 的 URL 给默认同步 Alembic（除非你把 Alembic 配成异步）

## 3. psycopg2-binary（同步驱动）

干什么： 同步连接 Postgres。Alembic 默认就是同步的，所以常用它。

URL 形式：

```text
postgresql://用户:密码@主机:端口/库名
# 或显式
postgresql+psycopg2://用户:密码@主机:端口/库名
```

你们 alembic/env.py 里：

```python
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

这里用的是同步 URL（postgresql://...），走 psycopg2。

安装：

```bash
uv add psycopg2-binary
```

binary 表示自带编译好的包，Windows 上更好装。

## 4. Alembic（迁移）

干什么： 把模型变更变成可版本管理的 SQL 脚本，并应用到数据库。

常用流程（在 apps/api）：

```bash
# 1. 初始化（已做过可跳过）
uv run alembic init alembic
# 2. 改模型后，生成迁移
uv run alembic revision --autogenerate -m "create users table"
# 3. 应用到数据库
uv run alembic upgrade head
# 4. 回退一步（可选）
uv run alembic downgrade -1
```

关键配置：

- alembic.ini：Alembic 主配置
- alembic/env.py：指定 sqlalchemy.url、target_metadata = Base.metadata
- alembic/versions/*.py：具体迁移脚本（含 upgrade / downgrade）

检查库结构是否和模型一致：

```bash
uv run alembic check
```

## 5. 和你们项目对应的最小心智模型

```text
.env
  DATABASE_URL=postgresql://eaap:...@localhost:5432/eaap
       │
       ├─ database.py  → 换成 +asyncpg → FastAPI 异步读写
       │
       └─ alembic/env.py → 保持同步 URL → psycopg2 → 迁移表结构
models/*.py  → SQLAlchemy ORM 模型
versions/*.py → Alembic 迁移历史
```

日常开发顺序：

- 改 models
- alembic revision --autogenerate -m "..."
- alembic upgrade head
- 在 FastAPI 里用 AsyncSession + SQLAlchemy 读写

## 6. 易混点

| 问题 | 结论 |
|--|--|
| 为什么既要 asyncpg 又要 psycopg2？ | 一个给异步 API，一个给同步迁移 |
| Alembic 能直接用 asyncpg 吗？ | 可以，但要额外配异步 env；你们现在用同步更简单 |
| SQLAlchemy 能脱离驱动用吗？ | 不能，必须配一种 DB 驱动 |
| migration 改什么？ | 主要改表结构，不是业务数据 |

一句话：
SQLAlchemy 是操作层；asyncpg 服务异步 API；psycopg2 服务 Alembic 同步迁移；Alembic 负责把模型变更安全落到 Postgres。

---

# 问题：

## 1.每次改了models都要手动调用一下alembic revision --autogenerate -m "..." 吗？

对，正常流程就是每次改完 models，再手动生成一次迁移（然后 upgrade）。

```bash
# 1. 改 models
# 2. 生成迁移脚本
uv run alembic revision --autogenerate -m "说明这次改了什么"
# 3. 应用到数据库
uv run alembic upgrade head
```

原因：Alembic 不会监视文件自动跑；它要你确认“这次结构变更”并留下版本记录，方便团队同步和回滚。

补充：

- 开发偷懒：有人用 Base.metadata.create_all() 自动建表，但不适合正式流程，也难回滚
- 没改结构（只改业务逻辑）：不用跑 Alembic
- 改了模型但忘了迁移：代码和数据库会不一致，运行时容易报错

所以记住：
改表结构 → revision --autogenerate → upgrade head。

## 2.迁移了以后数据库的表结构才会改是吗，也就是说对表结构的操作是Alembic 做的，SQLAlchemy 只是规定了表结构是什么样？

对，你的理解基本正确。

更准确一点：

| 角色 | 做什么 |
|--|--|
| SQLAlchemy 模型 | 在代码里声明表应该长什么样（类、字段、类型） |
| Alembic | 根据模型变化生成迁移，并真正执行 SQL 去改数据库 |
| 数据库 | 最终存着真实的表结构 |

所以流程是：

```text
改 models（规定结构）
  → alembic revision --autogenerate（生成改库脚本）
  → alembic upgrade head（Alembic 执行，数据库表结构才变）
  → 之后 SQLAlchemy 按这个结构读写数据
```

补充两点：

- SQLAlchemy 也能直接建表（如 create_all()），但你们现在规范做法是交给 Alembic。
- SQLAlchemy 日常更多是增删改查数据；改表结构走 Alembic。

一句话：模型是设计图，Alembic 是施工队，数据库才是盖好的房子。

## 3.SQLAlchemy 其实也能做所有的sql语句，只是我们这里将建表的部分交给了alembic ？

对，可以这么理解。

SQLAlchemy 能力很全，既能：

- 写查询（SELECT / INSERT / UPDATE / DELETE）
- 也能执行建表、改表这类 DDL（create_all()、drop_all()，或直接执行 SQL）

你们项目里的分工是工程选择，不是能力限制：

| 事情 | 交给谁 | 原因 |
|--|--|--|
| 日常读写数据 | SQLAlchemy | API 业务逻辑 |
| 建表 / 改表结构 | Alembic | 有版本记录、可回滚、团队可同步 |

所以：

- 不是 SQLAlchemy 不能建表
- 而是 不建议在应用里随便建表，改用 Alembic 管理结构变更更安全、可追踪

一句话：SQLAlchemy 能干几乎所有 SQL 的事；这里把“改表结构”规范地交给 Alembic。

## 4.models里面的base.py代码是什么意思？

base.py 的作用是：定义所有模型的公共基类。

```python
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
```

含义：

**DeclarativeBase**

SQLAlchemy 2.x 提供的 ORM 基类。继承它之后，类才能变成“数据库表模型”。

**class Base(DeclarativeBase): pass**

项目自己的基类。目前是空的，但所有模型都继承它，比如：

```python
class User(Base):
    __tablename__ = "users"
    ...
```

为什么单独抽出来

- 所有模型共用一个 Base
- Alembic 用 Base.metadata 知道“有哪些表”
- 以后要加公共字段（如统一 id、created_at）可以写在 Base 里，一次生效

一句话：Base 是模型家族的“祖宗类”；User 等表模型都从它继承，Alembic 也靠它发现表结构。

## 5.Base.metadata是什么意思？

Base.metadata 是挂在基类 Base 上的一份 表结构清单（MetaData）。

可以理解为：

```text
Base.metadata
  └── 收集了所有继承 Base 的模型对应的表信息
        ├── users 表（来自 User）
        ├── 以后的 orders 表
        └── ...
```

当你写：

```python
class User(Base):
    __tablename__ = "users"
    ...
```

SQLAlchemy 会把这张表的定义登记进 Base.metadata。

所以在 alembic/env.py 里：

```python
target_metadata = Base.metadata
```

意思是告诉 Alembic：
以这些模型登记的表结构为准，去和数据库对比，生成迁移。

一句话：Base.metadata = 当前项目所有 ORM 模型汇总后的“表结构目录”。

## 6.基类可以有多个吗？

可以，但一个项目里通常只用一个。

常见做法： 只有一个 Base(DeclarativeBase)，所有模型都继承它。
这样 Base.metadata 里能收齐全部表，Alembic 也好用。

可以多个： 比如：

```python
class Base(DeclarativeBase):
    pass
class AuditBase(DeclarativeBase):
    pass
```

不同模型继承不同基类。但要注意：

- 每个基类有自己的 .metadata
- Alembic 要分别配置，或手动合并，否则容易漏表
- 一般没必要这么复杂

结论： 技术上能有多个基类；你们现在这种“一个 Base 管所有模型”是标准、推荐做法。
