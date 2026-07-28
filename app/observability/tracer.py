# Tracer — tracing untuk end-to-end request (OpenTelemetry-ready)

from typing import Optional, Callable
import time
import uuid
from functools import wraps
from app.config import settings


class Tracer:
    def __init__(self, service_name: str = "rag-pipeline"):
        self._service_name = service_name
        self._enabled = settings.OBSERVABILITY_ENABLED

    def trace(self, span_name: str):
        """Decorator for tracing function calls."""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self._enabled:
                    return await func(*args, **kwargs)
                span_id = str(uuid.uuid4())[:8]
                start = time.monotonic()
                try:
                    result = await func(*args, **kwargs)
                    duration = (time.monotonic() - start) * 1000
                    return result
                except Exception as e:
                    duration = (time.monotonic() - start) * 1000
                    raise e
                finally:
                    pass  # In production, send span to OpenTelemetry collector
            return async_wrapper
        return decorator

    async def create_span(self, name: str, trace_id: str = None):
        """Context manager for manual tracing."""
        return TraceSpan(name=name, trace_id=trace_id or str(uuid.uuid4()), enabled=self._enabled)


class TraceSpan:
    def __init__(self, name: str, trace_id: str, enabled: bool = True):
        self.name = name
        self.trace_id = trace_id
        self._enabled = enabled
        self._start: float = 0.0

    async def __aenter__(self):
        if self._enabled:
            self._start = time.monotonic()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._enabled:
            duration = (time.monotonic() - self._start) * 1000
            pass  # In production, send span to OpenTelemetry
