# Observability Logger — mencatat metrik operasional dan tracing

import json
import logging
import sys
from datetime import datetime
from typing import Optional
from app.config import settings
from app.api.schemas import EvaluationResult


class ObservabilityLogger:
    def __init__(self):
        self._logger = logging.getLogger("rag_observability")
        self._logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    async def log(
        self,
        trace_id: str,
        query: str,
        latency_ms: float,
        token_count: int,
        cost: float,
        document_count: int,
        evaluation: Optional[EvaluationResult] = None,
    ):
        """Log observability data for a single query."""
        log_data = {
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "query_preview": query[:100],
            "latency_ms": round(latency_ms, 2),
            "token_count": token_count,
            "cost": round(cost, 6),
            "document_count": document_count,
        }

        if evaluation:
            log_data["evaluation"] = evaluation.model_dump(exclude_none=True)

        level = logging.WARNING if latency_ms > 5000 else logging.INFO
        self._logger.log(level, json.dumps(log_data))

    async def log_error(self, trace_id: str, query: str, error: str, latency_ms: float = 0.0):
        """Log errors with context."""
        log_data = {
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "query_preview": query[:100],
            "error": error,
            "latency_ms": round(latency_ms, 2),
        }
        self._logger.error(json.dumps(log_data))
