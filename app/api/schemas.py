# API response models

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    enable_rewrite: Optional[bool] = None
    enable_hyde: Optional[bool] = None
    enable_decompose: Optional[bool] = None
    enable_evaluation: Optional[bool] = None
    ground_truth: Optional[str] = None


class RetrievedDocument(BaseModel):
    id: str
    content: str
    source: Optional[str] = None
    score: float = 0.0
    rank: int = 0
    retrieval_method: str = "unknown"


class QueryProcessingResult(BaseModel):
    original_query: str
    rewritten_query: Optional[str] = None
    hyde_document: Optional[str] = None
    sub_queries: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    precision: Optional[float] = None
    recall: Optional[float] = None
    mrr: Optional[float] = None
    ndcg: Optional[float] = None
    faithfulness: Optional[float] = None
    relevancy: Optional[float] = None


class TraceInfo(BaseModel):
    trace_id: str
    latency_ms: float
    llm_tokens: int = 0
    llm_cost: float = 0.0
    retrieval_latency_ms: float = 0.0
    reranking_latency_ms: float = 0.0
    query_processing_latency_ms: float = 0.0


class QueryResponse(BaseModel):
    answer: str
    query_processing: Optional[QueryProcessingResult] = None
    documents: list[RetrievedDocument] = Field(default_factory=list)
    evaluation: Optional[EvaluationResult] = None
    trace: Optional[TraceInfo] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Berdasarkan dokumen yang ada...",
                "query_processing": {
                    "original_query": "Apa dampak kenaikan suku bunga?",
                    "rewritten_query": "dampak kenaikan suku bunga terhadap sektor properti 2026"
                },
                "documents": [
                    {
                        "id": "doc-001",
                        "content": "...",
                        "source": "laporan_keuangan_2026.pdf",
                        "score": 0.95,
                        "rank": 1,
                        "retrieval_method": "hybrid"
                    }
                ],
                "trace": {
                    "trace_id": "trace-abc123",
                    "latency_ms": 2340.5,
                    "llm_tokens": 512,
                    "llm_cost": 0.0023
                }
            }
        }
    )
