# Pipeline Orchestrator --- menghubungkan seluruh komponen end-to-end

import asyncio
import time
import uuid
from typing import Optional
from app.config import settings
from app.models.document import DocumentChunk
from app.api.schemas import (
    QueryRequest, QueryResponse, RetrievedDocument,
    QueryProcessingResult, EvaluationResult, TraceInfo,
)
from app.core.query_processing.rewrite import QueryRewriteProcessor
from app.core.query_processing.hyde import HyDEProcessor
from app.core.query_processing.decompose import DecomposeProcessor
from app.core.retrieval.hybrid_retriever import HybridRetriever
from app.core.retrieval.bm25_retriever import BM25Retriever
from app.core.retrieval.embedding_retriever import DenseRetriever
from app.core.reranking.cross_encoder import CrossEncoderReranker
from app.core.generation.llm_generator import LLMGenerator
from app.evaluation.evaluator import RAGEvaluator
from app.observability.logger import ObservabilityLogger


class RAGPipeline:
    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        dense_retriever: DenseRetriever,
        llm_generator: LLMGenerator,
        cross_encoder: CrossEncoderReranker = None,
        evaluator: RAGEvaluator = None,
        observability: ObservabilityLogger = None,
    ):
        self._hybrid_retriever = HybridRetriever(bm25_retriever, dense_retriever)
        self._bm25 = bm25_retriever
        self._dense = dense_retriever
        self._llm = llm_generator
        self._reranker = cross_encoder or CrossEncoderReranker()
        self._evaluator = evaluator
        self._observability = observability or ObservabilityLogger()

        self._rewriter = QueryRewriteProcessor(llm_generator)
        self._hyde = HyDEProcessor(llm_generator)
        self._decomposer = DecomposeProcessor(llm_generator)

    async def run(self, request: QueryRequest) -> QueryResponse:
        trace_id = str(uuid.uuid4())
        start_time = time.monotonic()

        query = request.query
        top_k = request.top_k or settings.TOP_K_FINAL

        query_proc_result = QueryProcessingResult(original_query=query)

        # --- Phase 1: Query Processing ---
        qp_start = time.monotonic()
        if settings.ENABLE_REWRITE and (request.enable_rewrite is None or request.enable_rewrite):
            query_proc_result.rewritten_query = await self._rewriter.process(query)
            enriched_query = query_proc_result.rewritten_query
        else:
            enriched_query = query

        hyde_embedding = None
        if settings.ENABLE_HYDE and (request.enable_hyde is None or request.enable_hyde):
            hyde_doc = await self._hyde.process(query)
            query_proc_result.hyde_document = hyde_doc

        sub_queries = []
        if settings.ENABLE_DECOMPOSE and (request.enable_decompose is None or request.enable_decompose):
            sub_queries = await self._decomposer.process_to_list(query)
            query_proc_result.sub_queries = sub_queries

        qp_latency = (time.monotonic() - qp_start) * 1000

        # --- Phase 2: Hybrid Retrieval ---
        ret_start = time.monotonic()
        queries_to_search = [enriched_query] + sub_queries
        all_docs: dict[str, tuple[DocumentChunk, float]] = {}

        for sq in queries_to_search:
            results = await self._hybrid_retriever.retrieve(
                sq, top_k=settings.TOP_K_INITIAL, query_embedding=hyde_embedding
            )
            for doc, score in results:
                if doc.id not in all_docs or score > all_docs[doc.id][1]:
                    all_docs[doc.id] = (doc, score)

        candidate_docs = list(all_docs.values())
        
        # Fallback: if no results from retrieval, return all indexed docs
        if not candidate_docs and self._bm25._built and self._bm25._corpus_size > 0:
            for i in range(min(self._bm25._corpus_size, settings.TOP_K_INITIAL)):
                candidate_docs.append((self._bm25._documents[i], 0.0))
        
        ret_latency = (time.monotonic() - ret_start) * 1000

        # --- Phase 3: Reranking ---
        rerank_start = time.monotonic()
        reranked = await self._reranker.rerank(enriched_query, candidate_docs)
        reranked = reranked[:top_k]
        rerank_latency = (time.monotonic() - rerank_start) * 1000

        # --- Phase 4: Generation ---
        separator = "\\n\\n---\\n\\n"
        context = separator.join(
            f"[Sumber {i+1}] {doc.content}" for i, (doc, _) in enumerate(reranked)
        )

        system_prompt = (
            "Anda adalah asisten RAG yang menjawab pertanyaan berdasarkan dokumen yang diberikan. "
            "Gunakan informasi dari dokumen untuk menjawab secara akurat. "
            "Jika jawaban tidak ditemukan dalam dokumen, katakan bahwa Anda tidak memiliki informasi yang cukup. "
            "Sertakan referensi sumber menggunakan format [Sumber N]."
        )

        user_prompt = f"Pertanyaan: {query}\\n\\nDokumen referensi:\\n{context}"

        gen_start = time.monotonic()
        answer, token_count, cost = await self._llm.generate_with_usage(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        gen_latency = (time.monotonic() - gen_start) * 1000

        total_latency = (time.monotonic() - start_time) * 1000

        response_docs = []
        for rank, (doc, score) in enumerate(reranked, 1):
            response_docs.append(RetrievedDocument(
                id=doc.id,
                content=doc.content[:500],
                source=doc.metadata.get("source", doc.metadata.get("original_filename", "")),
                score=round(score, 4),
                rank=rank,
                retrieval_method="hybrid",
            ))

        eval_result = None
        if self._evaluator:
            enable = request.enable_evaluation
            if enable is None:
                enable = settings.EVALUATION_ENABLED
            if enable:
                eval_result = await self._evaluator.evaluate(
                    query=query,
                    answer=answer,
                    ground_truth=request.ground_truth,
                    retrieved_docs=[doc for doc, _ in reranked],
                )

        trace_info = TraceInfo(
            trace_id=trace_id,
            latency_ms=round(total_latency, 2),
            llm_tokens=token_count,
            llm_cost=round(cost, 6),
            retrieval_latency_ms=round(ret_latency, 2),
            reranking_latency_ms=round(rerank_latency, 2),
            query_processing_latency_ms=round(qp_latency, 2),
        )

        await self._observability.log(
            trace_id=trace_id,
            query=query,
            latency_ms=total_latency,
            token_count=token_count,
            cost=cost,
            document_count=len(reranked),
            evaluation=eval_result,
        )

        return QueryResponse(
            answer=answer,
            query_processing=query_proc_result,
            documents=response_docs,
            evaluation=eval_result,
            trace=trace_info,
        )
