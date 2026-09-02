# R3 向量检索全流程


| 项目   | 内容                                                                                                    |
| ---- | ----------------------------------------------------------------------------------------------------- |
| 版本   | V2.1                                                                                                  |
| 日期   | 2026-09-02                                                                                            |
| 对照代码 | `knowledge_service.py`、`embedding.py`、`sparse.py`、`store.py`、`retriever.py`、`reranker.py`、`budget.py` |


切块向量 **不进 Postgres**。Postgres 只存文档元数据；原文在磁盘；向量在 Qdrant `eaap_chunks`。上传和 Chat 必须共用同一个 embedding 客户端（同一模型、同一维数）。

---



## 1. 三套存储各放什么

```text
上传文件
  → 磁盘  apps/api/data/knowledge/<user_id>/<uuid>.md|pdf|docx
  → Postgres  knowledge_document（元数据，无 chunk）
  → Qdrant    eaap_chunks（每个 chunk 一个 point，dense + sparse）
```

**Postgres** `knowledge_document`


| 字段                       | 含义                                                |
| ------------------------ | ------------------------------------------------- |
| id                       | 文档主键，Qdrant payload 的 `document_id`               |
| owner_user_id / agent_id | 隔离；检索 filter 用这两列对应的 payload                      |
| title                    | 写入 Qdrant payload `source`，Chat `citations.title` |
| source_uri               | 磁盘相对路径；维数变了可从这里重嵌，不必再上传                           |
| status                   | `pending` → `ready` / `failed`                    |


**Qdrant 一个 point（一条 chunk）**

```text
id:        uuid5(document_id + ":" + ordinal)     → citations.chunk_id
vector:
  dense:   [f0, f1, ..., f_{DIM-1}]               # 语义向量
  sparse:  { indices: [i, j, ...], values: [tf, ...] }  # 词面向量
payload:
  document_id, user_id, agent_id, ordinal, text, source
```

Collection 配置：named 向量 `dense`（cosine，维数 = hash 的 64 或 `EMBEDDING_DIM`）+ named `sparse`（modifier = IDF）。schema 或维数对不上会删 collection，启动时按磁盘重嵌。

---



## 2. 入库：文本如何变成两条向量

```text
文件字节
  → extract_text（.md UTF-8 / .pdf pypdf / .docx 段落）
  → chunk_markdown（按标题切，超过约 800 字再按段落切）
  → 每个 chunk：
       dense  = embedder.embed([chunk])[0]
       sparse = encode_sparse(chunk)          # upsert 时若空则补
  → upsert 到 eaap_chunks
```

一条文档多 chunk：`ordinal` = 0, 1, 2… 各占一个 point。

### 2.1 Dense（语义）

有 `EMBEDDING_API_KEY` + `EMBEDDING_MODEL`：走 OpenAI 兼容 `embeddings.create`，维数 `EMBEDDING_DIM`，按 `EMBEDDING_BATCH` 分批。`use_lexical_gate = False`。

没配：`HashEmbeddingClient`，64 维。对整段 UTF-8 做 SHA256，铺成 64 个 0–1 再 L2 归一化。**相近问句几乎正交**，不能当语义用。`use_lexical_gate = True`。

Dense 是 **稠密定长数组**：每一维都有数，表示「这段话在语义空间里的位置」。比较用 **余弦**（两边都单位化时等于点积）。Qdrant `using="dense"`，`distance=Cosine`。

### 2.2 Sparse（词面）

和 embedding 模型无关，纯本地 `encode_sparse`。

**分词** `lexical_terms`**（问句、chunk 同一套）**

- 英文：`[a-zA-Z0-9]+`，小写；长度 ≥ 2 且不是纯数字才保留（`ABC-123` → 只留 `abc`）。
- 中文：连续汉字整段计 1 次，再切每个 **2-gram** 各计 1 次。  
`"年假多少天"` → `年假多少天`、`年假`、`假多`、`多少`、`少天`。

**词频**：该词在这段里出现几次，`counts[term] += 1`。

**落到稀疏维**：`index = sha256(term) 的前 4 字节`（无符号 int）。同一 index 的次数相加（哈希碰撞也会叠在一维）。按下标排序后得到：

```text
indices = [18392011, 40122887, ...]   # 出现过的「词桶」
values  = [1.0,       2.0,      ...]   # 对应词频
```

未出现的维不存，所以叫稀疏。Qdrant 写入 `vector.sparse`，检索时用 **IDF**：常见词降权，生僻词（如工单号）加权。

内存测试不做 IDF，点积就是：

\mathrm{dot}(q, d) = \sum_{i \in q \cap d} q_i \cdot d_i

即：**只对两边都有的哈希维，问句词频 × 文档词频再加总**。文档里把无关词重复一万遍不加分；问句里的词在文档里出现越多，这一维越大。

---



## 3. 问句如何变成向量、如何去库里匹配

Chat 在拼 messages 之后、`call_model` 之前调用 `KnowledgeRetriever.retrieve(user_message)`。`resume` 不检索。

```text
query = 本轮 user_message
  ① dense_q = embedder.embed([query])[0]     # 与入库同一客户端
  ② sparse_q = encode_sparse(query)          # 与入库同一分词
  ③ Qdrant 两条查询，filter 必须同时：
       payload.user_id  = JWT 用户
       payload.agent_id = 当前 Agent
     每条最多 32 个 point（_CANDIDATE_LIMIT）
  ④ RRF 合成一个排行榜
```

别人的文档、别的 Agent 的文档：filter 直接挡掉，不会进入排行榜。

### 3.1 Dense 查询

`query_points(query=dense_q, using="dense")`。  
Qdrant 按 cosine 从高到低排。`SearchHit.dense_score` 记下这条 cosine（融合后 `score` 会改成 RRF 分，dense 分仍留着给后面准入 / rerank）。

语义近的会排前（「年假几天」vs「每年可休息 15 天」）。Hash 模式下这个分几乎是噪声。

### 3.2 Sparse 查询

`query_points(query=SparseVector(indices, values), using="sparse")`。  
问句 sparse 和库里各 point 的 sparse 做加权点积（含 IDF）。词面对上的排前（「ABC-123」）。

Sparse **不是覆盖率**。覆盖率是「问句词种类有几成作为子串出现在原文」；点积是「对上的哈希维上词频乘积（再乘 IDF）」。只反复写「年假」的长段，点积可以很高、覆盖率很低。

### 3.3 为什么要两条、如何合成（RRF）

Dense 分（0~1 cosine）和 sparse 点积（可大于 1、带 IDF）**量纲不同，不能相加**。

RRF 只看 **名次**：

\mathrm{RRF}(c) = \sum_{\text{榜}} \frac{1}{k + \mathrm{rank}},\quad k=60

第 1 名 1/61，第 2 名 1/62。同一 chunk 在 dense 榜、sparse 榜各加一次。两边都靠前会被抬高。

例子：天气段只在 dense 拿第 1；工单段 sparse 第 1、dense 第 2 → 工单 RRF 更高。这就是 hybrid。

问句 sparse 为空时只走 dense。

---



## 4. 准入：排行榜上的不一定能引用

RRF 总会给出「相对最像」的若干条，库里有文档时几乎不会空。所以还要决定 **能不能塞进 Prompt**。


| embedding | 留下的条件                              |
| --------- | ---------------------------------- |
| Hash（假向量） | 问句 `lexical_terms` 与 chunk 原文有子串重叠 |
| 真模型       | `dense_score ≥ 0.3` **或** 同样有词面子串  |


`12*7+5 等于多少` 不应引用员工手册：Hash 靠闸门；真模型靠 cosine 不够且词面也对不上。

`ABC-123` 在真模型下 cosine 可能很低，但词面能中，靠「或」留下。这是 hybrid 的价值，不是 RRF 名次本身。

---



## 5. 重排（rerank）

**不再查 Qdrant。** 对已经准入的 hits 打分排序，再取前 4 条（`_RETURN_LIMIT`）。

配齐 `RERANK_API_KEY` / `RERANK_BASE_URL` / `RERANK_MODEL` 时走 **cross-encoder**：把 `(问句, 各 chunk 原文)` 成对送给 rerank 模型，用返回的 `relevance_score` 排序。百炼 `qwen3.7-text-rerank` 必须用原生 `.../text-rerank/text-rerank` 地址，不要抄 embedding 的 `compatible-mode/v1`。调用失败则回退下面的特征 rerank。

未配这三个变量时（单测、无 Key）用 **FeatureReranker**：


\mathrm{score} = \mathrm{densescore} + 2 \times \frac{\text{问句词有多少个出现在 chunk 原文里}}{\text{问句词总数}}


覆盖率只问「有没有」，不计次数。用来纠正：RRF 被 dense 概述带偏、或 sparse 奖了「重复一个词」的长段。

---



## 6. 写入模型上下文

```text
前 4 条
  → fit_context_budget（KNOWLEDGE_CONTEXT_TOKENS，默认 1024）
  → format_knowledge_message → 一条 system（【知识库】…）
  → 插在本轮 user 前面
  → citations 与最终留下的 hits 一致
```

预算按顺序 **整段** 装；下一条会超就停。第一条单独超则截断加 `…`。只限制知识摘录，不管会话历史、checkpoint 里攒下的图 messages。

知识原文不写 `conversation_message`。

---



## 7. 一张图串起来

```text
【入库】
  文件 → 切块 → dense embed + encode_sparse → Qdrant point
                Postgres 只记文档行；磁盘留原文件

【检索】
  问句 → 同一套 dense embed
       → 同一套 encode_sparse
       → filter(user, agent)
       → dense cosine 榜  ∪  sparse 点积/IDF 榜
       → RRF（融合成名次）
       → 准入（hash 要词面；真向量 cosine 或词面）
       → CrossEncoder（配了 RERANK_*）或 FeatureReranker
       → 最多 4 条 + token 预算
       → 【知识库】system + citations
```

面试可记三句：

1. **Dense** 回答「意思像不像」；**Sparse** 回答「词撞没撞」。
2. **RRF** 融合两条排行榜的名次，因为分数不能加。
3. **Rerank** 在已经捞出的几条里再排序，不再回库：有 Key 走 cross-encoder 成对打分，否则用覆盖率纠偏。



### 问题1：为什么dense分高的chunk sparse得分却低呢？

这是正常现象，不是打分坏了。两条向量根本不在比同一件事。

**Dense 比的是语义位置**（cosine）：改写、同义、中英对译都可以近。  
**Sparse 比的是哈希维交集**：问句和 chunk **必须撞上同一个词桶**才加分，没撞上就是 0。

所以「意思很像、用词完全不同」→ dense 高、sparse 低。反过来「工单号对上了、周围句子不像」→ sparse 高、dense 低。Hybrid 就是为了同时接住这两种。

---

用你们现在的 `lexical_terms` 看交集就明白。中文是「整段 + 2-gram」，英文是「长度 ≥ 2 且非纯数字」；sparse 点积只对两边都有的维做 `问句词频 × 文档词频`。

问句「年假几天」切出来是：`年假几天`、`年假`、`假几`、`几天`。


| chunk                           | 词面交集                                                | sparse           | 真 embedding 的 dense |
| ------------------------------- | --------------------------------------------------- | ---------------- | ------------------- |
| 每年可休息 15 天                      | 空（`每年/年可/可休/休息` 对不上 `年假/假几/几天`；`15` 当纯数字丢掉；单字「天」丢掉） | **0**            | **高**（都在说休假天数）      |
| how many vacation days → 中文年假条文 | 中英词表不相交                                             | **0**            | **高**（多语 embedding） |
| 员工手册规定年假为 15 天。年假需提前报备。         | 只有 `年假`                                             | 2.0（正文里「年假」出现两次） | 也高                  |
| 年假制度见人力资源部通知。                   | 只有 `年假`                                             | 1.0              | 中高（同主题，没写天数）        |


第一条就是笔记里那个例子：语义近到 cosine 能排第一，2-gram 一个都对不上，sparse 榜上根本没有它。

---

再叠加两个会把 sparse **压得更低**、却几乎不动 dense 的机制：

1. **只认撞上的维，不管「意思」**
  cosine 是整段向量的方向，改写后方向仍近。`sparse_dot` 在交集为空时直接 0，段落写得再相关也没用。
2. **Qdrant 的 IDF**
  即使撞上了「制度」「通知」这种常见词，IDF 会降权。Dense 不看词频，只看语义空间。于是：主题相近、只共用几个常见词 → dense 仍可高，sparse 被打得很低。

Hash 模式先别用这个直觉：假向量几乎正交，看不到「dense 高」。上面说的是配了真 embedding 之后。

---

所以看到 dense 高、sparse 低，先问：**这段是不是换了说法在讲同一件事？** 是的话 sparse 本来就不该高。RRF 才把它从 dense 榜捞进来；rerank 再用覆盖率决定要不要排到条文前面——概述段往往 dense 不差、词面盖不住「几天」，正好会被覆盖率往下按。

### 问题2：为什么有时sparse 得分高但问题的覆盖率却低？

因为 **sparse 计次数，覆盖率计种类**。两个数回答的不是同一个问题。

问句「年假多少天」切成 5 个词：`年假多少天`、`年假`、`假多`、`多少`、`少天`。


|             | Sparse 点积                                                                          | 覆盖率（rerank 用的）     |
| ----------- | ---------------------------------------------------------------------------------- | ------------------ |
| 公式          | (问题中词1的词频 x 文档中词1的词频 x qdrant中词1的IDF)+(问题中词2的词频 x 文档中词2的词频 x qdrant中词2的IDFIDF)+... | 问句词有几个在文档中出现/问句词总数 |
| 没撞上的词       | 不加分，但 **不惩罚**                                                                      | 分母仍在，直接把比例拉低       |
| 同一个词出现 20 次 | 那一维乘 20                                                                            | 仍只算 1              |


所以：只反复写「年假」的长段，sparse 可以很高，覆盖率仍然很低。

本地跑出来的数：


| chunk                 | 对上的词    | sparse | 覆盖率            |
| --------------------- | ------- | ------ | -------------- |
| `年假。` × 20            | 只有 `年假` | **40** | 1/5 = 0.20     |
| `年假多少天：15 天。年假需提前申请。` | 5 个全中   | 6      | **5/5 = 1.00** |
| `年假制度见人力资源部通知。`       | 只有 `年假` | 1      | 1/5 = 0.20     |


刷「年假」的段 sparse 比真正答「多少天」的条文高 6 倍以上，覆盖率和一句空概述一样差。RRF 若只看 sparse 名次，会把刷词段抬上去——这就是 `FeatureReranker` 用覆盖率纠的那一类。

---

还可以从三个机制看为什么会这样。

**1. 点积是「对上的维 × 词频」，不是「问句被盖住多少」**  
问句里 4 个词完全没出现，sparse 也不减分。文档侧 `年假` 的 TF 越大，这一维越大。覆盖率分母是 5，只中 1 个就是 0.2。

**2. 长段天然占便宜**  
同一词在长文里出现次数多，sparse 跟着涨。覆盖率只问「有没有」，段落拉长不会把 1/5 变成 5/5。

**3. IDF 会再放大「只撞上生僻词」**  
工单号、专有名词权重大。问句是「工单 ABC-123 现在什么状态」，chunk 里只有一串 `ABC-123`、没有「状态」——sparse（尤其带 IDF）仍然可以排很前，覆盖率只有 1/N。

哈希碰撞是次要因素：两个不同词落到同一维，文档猛写无关词也可能抬 sparse，覆盖率仍按原文子串算，对不上。

---

和上一问对称记：

- **Dense 高、sparse 低**：换了说法，词没撞上。  
- **Sparse 高、覆盖率低**：撞上了，但只撞上问句的一小部分，还靠重复/长段/IDF 把分刷高了。

Sparse 适合召回（「有没有词面线索」）；覆盖率适合精排（「问句被这段讲全了没有」）。所以检索先用 sparse 捞，rerank 再用覆盖率往下按刷词段。

### 问题3：Sparse检索时，Qdrant 里文档侧还会再乘 IDF，IDF是什么

**IDF = Inverse Document Frequency，逆文档频率。** 衡量一个词有多「稀罕」：很多文档都有的词权重要压低，只有少数文档有的词要抬高。

经典写法：

```text
IDF(词) ≈ log( 总文档数 / 含该词的文档数 )
```


| 词         | 出现范围    | IDF      |
| --------- | ------- | -------- |
| 「的」「员工」   | 几乎每篇都有  | 低，区分度差   |
| 「年假」「陪产假」 | 只有制度里几段 | 高，更该用来匹配 |


和 **TF（词频）** 配对：TF 是「这篇里这个词出现几次」，IDF 是「整个库里这个词有多特有」。TF-IDF ≈ TF × IDF。BM25 也是这一族，只是公式更细。

## 在你们的 Qdrant 里

写入 sparse 时，`values` 仍是 **词频**（`encode_sparse` 数出来的次数）。collection 配了：

```158:160:apps/api/app/ai/knowledge/store.py
            sparse_vectors_config={
                SPARSE_VECTOR: SparseVectorParams(modifier=Modifier.IDF)
            },
```

表示：**查询打分时，Qdrant 再按该 collection 统计的 DF 乘上 IDF**，不是你们在 Python 里算的。常见词即使 TF 不低，对最终分的贡献也会变小。

内存版 `sparse_dot` **没有**这一步，只是两边 TF 点积，所以测试和线上 Qdrant 的绝对分会对不齐，排序大方向可以接近。

## 和「模拟编码器」的关系

IDF 是 **检索器侧的统一加权**，和 hash / 2-gram / BM25 分词是两层：

- 编码器：词 → index + TF  
- IDF：Qdrant 根据「这个 index 在多少 point 里出现过」再加权

语料太少时 IDF 不稳定（一篇文档里罕见词会被抬得很高）。这是统计量，不是神经网络。

一句话：**TF 看这篇有多密，IDF 看这个词在全库有多稀；乘在一起，才不会让「的」「员工」把「年假」打死。**