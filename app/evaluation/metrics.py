# Evaluation metrics utility functions

from typing import Optional
import math


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if k == 0:
        return 0.0
    relevant_retrieved = sum(1 for doc_id in retrieved_ids[:k] if doc_id in relevant_ids)
    return relevant_retrieved / k


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    relevant_retrieved = sum(1 for doc_id in retrieved_ids[:k] if doc_id in relevant_ids)
    return relevant_retrieved / len(relevant_ids)


def mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, doc_id in enumerate(retrieved_ids, 1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    dcg = 0.0
    for i in range(min(k, len(retrieved_ids))):
        rel = 1.0 if retrieved_ids[i] in relevant_ids else 0.0
        dcg += (2**rel - 1) / math.log2(i + 2)

    idcg = 0.0
    num_rel = min(len(relevant_ids), k)
    for i in range(num_rel):
        idcg += 1.0 / math.log2(i + 2)

    return dcg / idcg if idcg > 0 else 0.0
