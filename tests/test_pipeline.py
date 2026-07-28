# Test suite untuk RAG Pipeline

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.document import Document, DocumentChunk
from app.api.schemas import QueryRequest, QueryResponse, RetrievedDocument, QueryProcessingResult, TraceInfo
from app.core.retrieval.bm25_retriever import BM25Retriever
from app.core.retrieval.hybrid_retriever import HybridRetriever
from app.core.retrieval.embedding_retriever import DenseRetriever
from app.evaluation.metrics import precision_at_k, recall_at_k, mrr, ndcg_at_k
from app.evaluation.evaluator import RAGEvaluator
from app.observability.metrics import get_metrics, record_query


class TestBM25Retriever:
    @pytest.fixture
    def retriever(self):
        return BM25Retriever()

    def test_index_and_retrieve(self, retriever):
        docs = [
            DocumentChunk(id="1", document_id="doc1", content="Kenaikan suku bunga mempengaruhi sektor properti", metadata={"source": "doc1"}),
            DocumentChunk(id="2", document_id="doc2", content="Inflasi tahun ini mencapai 5 persen", metadata={"source": "doc2"}),
            DocumentChunk(id="3", document_id="doc3", content="Properti residensial tumbuh 10 persen tahun ini", metadata={"source": "doc3"}),
        ]
        retriever.index_documents(docs)
        assert retriever._built is True
        assert retriever._corpus_size == 3

    @pytest.mark.asyncio
    async def test_retrieve_relevant(self, retriever):
        docs = [
            DocumentChunk(id="1", document_id="doc1", content="Kenaikan suku bunga mempengaruhi sektor properti"),
            DocumentChunk(id="2", document_id="doc2", content="Inflasi tahun ini mencapai 5 persen"),
            DocumentChunk(id="3", document_id="doc3", content="Properti residensial tumbuh 10 persen tahun ini"),
        ]
        retriever.index_documents(docs)
        results = await retriever.retrieve("suku bunga properti", top_k=2)
        assert len(results) > 0
        assert results[0][0].id == "1"  # Most relevant doc


class TestMetrics:
    def test_precision_at_k(self):
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = {"a", "c", "f"}
        assert precision_at_k(retrieved, relevant, 5) == 2 / 5

    def test_recall_at_k(self):
        retrieved = ["a", "b", "c"]
        relevant = {"a", "d", "e"}
        assert recall_at_k(retrieved, relevant, 3) == 1 / 3

    def test_mrr(self):
        retrieved = ["x", "a", "b"]
        relevant = {"a"}
        assert mrr(retrieved, relevant) == 1 / 2

    def test_mrr_no_relevant(self):
        retrieved = ["x", "y", "z"]
        relevant = {"a"}
        assert mrr(retrieved, relevant) == 0.0

    def test_ndcg(self):
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "c"}
        ndcg = ndcg_at_k(retrieved, relevant, 4)
        assert 0 < ndcg <= 1.0

    def test_empty_relevant(self):
        retrieved = ["a", "b", "c"]
        relevant = set()
        assert ndcg_at_k(retrieved, relevant, 3) == 0.0


class TestEvaluator:
    @pytest.mark.asyncio
    async def test_faithfulness(self):
        evaluator = RAGEvaluator()
        docs = [
            DocumentChunk(id="1", document_id="doc1", content="Suku bunga naik 25 basis poin. Properti akan terpengaruh."),
        ]
        score = await evaluator._compute_faithfulness("Suku bunga naik. Properti terpengaruh.", docs)
        assert score > 0.5

    @pytest.mark.asyncio
    async def test_relevancy(self):
        evaluator = RAGEvaluator()
        score = await evaluator._compute_relevancy(
            "Kenaikan suku bunga menyebabkan properti turun",
            "dampak suku bunga properti"
        )
        assert score > 0


class TestMetricsStore:
    def test_record_and_get(self):
        record_query(100.0, 50, 0.001)
        record_query(200.0, 100, 0.002)
        metrics = get_metrics()
        assert metrics["total_queries"] >= 2
        assert metrics["total_latency_ms"] >= 300.0
        assert metrics["avg_latency_ms"] > 0


class TestSchemas:
    def test_query_request_defaults(self):
        req = QueryRequest(query="test query")
        assert req.query == "test query"
        assert req.top_k is None

    def test_query_response_with_all_fields(self):
        response = QueryResponse(
            answer="Test answer",
            query_processing=QueryProcessingResult(original_query="test"),
            documents=[
                RetrievedDocument(id="1", content="doc content", score=0.95, rank=1, retrieval_method="hybrid")
            ],
            trace=TraceInfo(trace_id="trace-1", latency_ms=100.0, llm_tokens=50, llm_cost=0.001),
        )
        assert response.answer == "Test answer"
        assert len(response.documents) == 1
        assert response.trace.trace_id == "trace-1"
