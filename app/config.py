# Advanced RAG Pipeline System Configuration

import os
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Advanced RAG Pipeline"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # --- LLM ---
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Optional[str] = None
    LLM_API_BASE: Optional[str] = None
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 1024

    # --- Embedding ---
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_DIMENSION: int = 1536

    # --- Vector DB ---
    VECTOR_DB_TYPE: str = "qdrant"
    VECTOR_DB_URL: str = "http://localhost:6333"
    VECTOR_DB_API_KEY: Optional[str] = None
    COLLECTION_NAME: str = "documents"

    # --- Retrieval ---
    TOP_K_INITIAL: int = 20
    TOP_K_FINAL: int = 5
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    HYBRID_ALPHA: float = 0.5

    # --- Reranking ---
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_DEVICE: str = "cpu"
    RERANKER_MAX_LENGTH: int = 512

    # --- Query Processing ---
    ENABLE_REWRITE: bool = True
    ENABLE_HYDE: bool = True
    ENABLE_DECOMPOSE: bool = False

    # --- Evaluation ---
    EVALUATION_ENABLED: bool = True

    # --- Observability ---
    OBSERVABILITY_ENABLED: bool = True
    OTLP_ENDPOINT: Optional[str] = None
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


settings = Settings()
