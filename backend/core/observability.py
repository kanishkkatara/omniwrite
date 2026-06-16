"""
Observability setup for OmniWrite.

Initialises:
- Prometheus Counters / Histograms
- OpenTelemetry tracer (if OTLP is enabled)
- LangSmith environment variables (if enabled)

Call `setup_observability(settings)` once at application startup.
Use `get_tracer()` to obtain a named OTel tracer in any module.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from prometheus_client import Counter, Histogram

if TYPE_CHECKING:
    from backend.core.config import Settings

logger = logging.getLogger(__name__)

# ── Prometheus metrics ────────────────────────────────────────────────────────

GENERATIONS_TOTAL = Counter(
    "omniwrite_generations_total",
    "Total number of content generation requests",
    labelnames=["platform", "model", "status"],
)

GENERATION_DURATION = Histogram(
    "omniwrite_generation_duration_seconds",
    "Duration of content generation pipeline in seconds",
    labelnames=["platform"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

TOKEN_COST_TOTAL = Counter(
    "omniwrite_token_cost_dollars_total",
    "Cumulative LLM cost in USD",
    labelnames=["model"],
)

# ── OTel tracer (lazy init) ───────────────────────────────────────────────────
_tracer = None


def get_tracer():
    """Return the OpenTelemetry tracer. Falls back to a no-op tracer if OTel is not initialised."""
    global _tracer  # noqa: PLW0603
    if _tracer is not None:
        return _tracer
    try:
        from opentelemetry import trace

        return trace.get_tracer("omniwrite")
    except Exception:
        return _NoOpTracer()


class _NoOpTracer:
    """Minimal no-op tracer used when OTel is unavailable."""

    def start_as_current_span(self, name: str, **_kwargs):  # noqa: ANN001
        import contextlib

        return contextlib.nullcontext()

    def start_span(self, name: str, **_kwargs):  # noqa: ANN001
        return _NoOpSpan()


class _NoOpSpan:
    def set_attribute(self, *_args, **_kwargs):
        pass

    def record_exception(self, *_args, **_kwargs):
        pass

    def set_status(self, *_args, **_kwargs):
        pass

    def end(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass


# ── Public setup function ─────────────────────────────────────────────────────


def setup_observability(settings: Settings) -> None:
    """
    Initialise all observability tooling.

    Should be called once at application startup (e.g. FastAPI lifespan).
    """
    global _tracer  # noqa: PLW0603

    obs = settings.observability

    # ── LangSmith ─────────────────────────────────────────────────────────────
    ls = obs.langsmith
    if ls.enabled and ls.api_key:
        os.environ.setdefault("LANGCHAIN_API_KEY", ls.api_key)
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_PROJECT", ls.project)
        logger.info("LangSmith tracing enabled (project=%s)", ls.project)

    # ── OpenTelemetry ─────────────────────────────────────────────────────────
    if obs.otlp_enabled:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create({"service.name": "omniwrite"})
            provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=obs.otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            _tracer = trace.get_tracer("omniwrite")
            logger.info("OpenTelemetry OTLP exporter configured → %s", obs.otlp_endpoint)
        except ImportError:
            logger.warning("opentelemetry-exporter-otlp not installed; OTLP tracing disabled.")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to initialise OTLP tracer: %s", exc)

    if obs.prometheus_enabled:
        logger.info("Prometheus metrics enabled")

    logger.info("Observability setup complete")
