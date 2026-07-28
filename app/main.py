# Main FastAPI Application — Advanced RAG Pipeline System

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.config import settings
from app.api.routes import router
from app.core.pipeline import RAGPipeline
from app.core.retrieval.bm25_retriever import BM25Retriever
from app.core.retrieval.embedding_retriever import DenseRetriever
from app.core.generation.llm_generator import LLMGenerator
from app.core.reranking.cross_encoder import CrossEncoderReranker
from app.evaluation.evaluator import RAGEvaluator
from app.observability.logger import ObservabilityLogger
from app.core.ingestion.ingestion import DocumentStore, DocumentIngestion

# Global pipeline instance
pipeline: Optional[RAGPipeline] = None

# Eager initialization for non-LLM components
bm25_retriever: BM25Retriever = BM25Retriever()
dense_retriever: DenseRetriever = DenseRetriever()
doc_store: DocumentStore = DocumentStore()
doc_ingestion: DocumentIngestion = DocumentIngestion(doc_store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager — setup and teardown."""
    global pipeline

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="[%(asctime)s] %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    logger = logging.getLogger(__name__)
    logger.info("Initializing RAG Pipeline components...")

    # Initialize components
    bm25 = bm25_retriever
    dense = dense_retriever
    llm = LLMGenerator()
    reranker = CrossEncoderReranker()
    evaluator = RAGEvaluator()
    obs = ObservabilityLogger()

    # Build pipeline
    global pipeline
    pipeline = RAGPipeline(
        bm25_retriever=bm25,
        dense_retriever=dense,
        llm_generator=llm,
        cross_encoder=reranker,
        evaluator=evaluator,
        observability=obs,
    )

    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} ready")
    yield

    # Teardown
    logger.info("Shutting down RAG Pipeline...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Advanced RAG Pipeline dengan Query Processing, Hybrid Retrieval, "
                    "Cross-Encoder Reranking, Evaluasi, dan Observability.",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve static frontend
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def root():
        """Redirect to frontend."""
        return RedirectResponse(url="/static/index.html")

    # Register API routes
    app.include_router(router, prefix=settings.API_PREFIX)

    return app


app = create_app()
