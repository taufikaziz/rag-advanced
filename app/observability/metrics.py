# Metrics collector — menyediakan metrik untuk Prometheus / monitoring

from typing import Optional
from app.config import settings

# In-memory metrics store (can be replaced with Prometheus)
_metrics_store = {
    "total_queries": 0,
    "total_latency_ms": 0.0,
    "total_tokens": 0,
    "total_cost": 0.0,
    "error_count": 0,
}


def record_query(latency_ms: float, token_count: int, cost: float):
    _metrics_store["total_queries"] += 1
    _metrics_store["total_latency_ms"] += latency_ms
    _metrics_store["total_tokens"] += token_count
    _metrics_store["total_cost"] += cost


def record_error():
    _metrics_store["error_count"] += 1


def get_metrics() -> dict:
    store = dict(_metrics_store)
    q = store["total_queries"]
    store["avg_latency_ms"] = round(store["total_latency_ms"] / q, 2) if q > 0 else 0.0
    store["avg_tokens"] = round(store["total_tokens"] / q, 2) if q > 0 else 0.0
    store["avg_cost"] = round(store["total_cost"] / q, 6) if q > 0 else 0.0
    store["error_rate"] = round(store["error_count"] / q, 4) if q > 0 else 0.0
    return store
