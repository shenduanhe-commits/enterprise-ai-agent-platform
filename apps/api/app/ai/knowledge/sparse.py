import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SparseVectorData:
    indices: list[int]
    values: list[float]

    def is_empty(self) -> bool:
        return not self.indices


# 将文本编码为稀疏向量
def encode_sparse(text: str) -> SparseVectorData:
    weights: dict[int, float] = {}
    # 提取文本中的词汇
    for term, count in lexical_terms(text).items():
        index = _term_index(term)
        weights[index] = weights.get(index, 0.0) + float(count)
    # 将词汇的权重排序
    indices = sorted(weights)
    # 返回稀疏向量
    return SparseVectorData(
        indices=indices, values=[weights[index] for index in indices]
    )


# 提取文本中的词汇
def lexical_terms(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    # 提取文本中的英文单词
    for word in re.findall(r"[a-zA-Z0-9]+", text.lower()):
        # 提取文本中的英文单词的二元组
        if len(word) >= 2 and not word.isdigit():
            counts[word] = counts.get(word, 0) + 1
    # 提取文本中的中文词汇
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(run) < 2:
            continue
        # 提取文本中的中文词汇的二元组
        counts[run] = counts.get(run, 0) + 1
        for index in range(len(run) - 1):
            gram = run[index : index + 2]
            counts[gram] = counts.get(gram, 0) + 1
    return counts


# 计算两个稀疏向量的点积
def sparse_dot(left: SparseVectorData, right: SparseVectorData) -> float:
    if left.is_empty() or right.is_empty():
        return 0.0
    right_weights = dict(zip(right.indices, right.values, strict=True))
    return sum(
        value * right_weights[index]
        for index, value in zip(left.indices, left.values, strict=True)
        if index in right_weights
    )


# 计算多个稀疏向量的点积
def rrf_scores(*ranked_ids: list[str], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ids in ranked_ids:
        for rank, item_id in enumerate(ids, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return scores


# 计算词汇的哈希值
def _term_index(term: str) -> int:
    digest = hashlib.sha256(term.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")
