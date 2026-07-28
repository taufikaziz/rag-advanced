# Evaluation Module — menghitung metrik kualitas RAG

from typing import Optional
import math
from app.models.document import DocumentChunk
from app.api.schemas import EvaluationResult


class RAGEvaluator:
    def __init__(self):
        pass

    async def evaluate(
        self,
        query: str,
        answer: str,
        ground_truth: str,
        retrieved_docs: list[DocumentChunk],
    ) -> EvaluationResult:
        """Evaluate the RAG pipeline output against ground truth."""
        # Faithfulness: apakah answer konsisten dengan retrieved docs
        faithfulness = await self._compute_faithfulness(answer, retrieved_docs)

        # Relevancy: apakah answer relevan dengan query
        relevancy = await self._compute_relevancy(answer, query)

        return EvaluationResult(
            faithfulness=round(faithfulness, 4),
            relevancy=round(relevancy, 4),
        )

    async def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: list[tuple[DocumentChunk, float]],
        relevant_doc_ids: set[str],
    ) -> EvaluationResult:
        """Evaluate retrieval performance when ground-truth relevant docs are known."""
        retrieved_ids = [doc.id for doc, _ in retrieved_docs]
        k = len(retrieved_docs)

        # Precision@K
        relevant_retrieved = sum(1 for doc_id in retrieved_ids if doc_id in relevant_doc_ids)
        precision = relevant_retrieved / k if k > 0 else 0.0

        # Recall@K
        recall = relevant_retrieved / len(relevant_doc_ids) if relevant_doc_ids else 0.0

        # MRR (Mean Reciprocal Rank)
        mrr = 0.0
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_doc_ids:
                mrr = 1.0 / rank
                break

        # nDCG@K
        ndcg = self._compute_ndcg(retrieved_ids, relevant_doc_ids, k)

        return EvaluationResult(
            precision=round(precision, 4),
            recall=round(recall, 4),
            mrr=round(mrr, 4),
            ndcg=round(ndcg, 4),
        )

    async def _compute_faithfulness(
        self, answer: str, documents: list[DocumentChunk]
    ) -> float:
        """Estimate faithfulness by checking answer claims against document content."""
        if not documents:
            return 0.0

        answer_lower = answer.lower()
        doc_text = " ".join(d.content.lower() for d in documents)

        # Simple lexical faithfulness: proportion of answer sentences supported by docs
        import re
        sentences = re.split(r'[.!?]+', answer)
        supported = 0
        total = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # skip short fragments
                continue
            total += 1
            # Check if key terms from sentence appear in documents
            words = set(sentence.lower().split())
            content_words = {w for w in words if len(w) > 3 and w not in {
                'dengan', 'untuk', 'dalam', 'adalah', 'telah', 'akan', 'dapat',
                'yang', 'dari', 'ini', 'itu', 'dan', 'atau', 'pada', 'ke', 'di',
                'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have',
            }}
            if not content_words:
                continue
            match_count = sum(1 for w in content_words if w in doc_text)
            if match_count / len(content_words) >= 0.5:
                supported += 1

        return supported / total if total > 0 else 0.0

    async def _compute_relevancy(self, answer: str, query: str) -> float:
        """Estimate relevancy of answer to the query."""
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())

        stopwords = {
            'dengan', 'untuk', 'dalam', 'adalah', 'telah', 'akan', 'dapat',
            'yang', 'dari', 'ini', 'itu', 'dan', 'atau', 'pada', 'ke', 'di',
            'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'what',
            'how', 'why', 'when', 'where', 'apa', 'bagaimana', 'mengapa', 'kapan',
        }

        q_words = {w for w in query_words if w not in stopwords}
        a_words = {w for w in answer_words if w not in stopwords}

        if not q_words:
            return 0.5

        overlap = q_words & a_words
        return len(overlap) / len(q_words) if q_words else 0.0

    def _compute_ndcg(
        self, retrieved_ids: list[str], relevant_ids: set[str], k: int
    ) -> float:
        """Compute Normalized Discounted Cumulative Gain."""
        dcg = 0.0
        idcg = 0.0

        for i in range(min(k, len(retrieved_ids))):
            rel = 1.0 if retrieved_ids[i] in relevant_ids else 0.0
            dcg += (2**rel - 1) / math.log2(i + 2)

        # Ideal DCG: all relevant docs at top
        num_rel = min(len(relevant_ids), k)
        for i in range(num_rel):
            idcg += 1.0 / math.log2(i + 2)

        return dcg / idcg if idcg > 0 else 0.0
