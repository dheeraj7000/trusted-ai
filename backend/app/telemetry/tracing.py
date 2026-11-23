"""OpenTelemetry tracing setup for AgentProof."""
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_exporter: InMemorySpanExporter | None = None


def setup_tracing() -> None:
    """Configure the OpenTelemetry TracerProvider with an in-memory exporter."""
    global _exporter
    _exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(_exporter))
    trace.set_tracer_provider(provider)


def get_tracer() -> trace.Tracer:
    """Return a named tracer for AgentProof."""
    return trace.get_tracer("agentproof")


def get_exported_spans() -> list:
    """Retrieve spans from the in-memory exporter."""
    if _exporter is None:
        return []
    return list(_exporter.get_finished_spans())


@contextmanager
def create_run_span(run_id: str):
    """Create a root span for an agent run."""
    tracer = get_tracer()
    with tracer.start_as_current_span("agent.run", attributes={"run_id": run_id}) as span:
        yield span


def record_event(span: trace.Span, event_name: str, attributes: dict[str, Any] | None = None) -> None:
    """Add an event to a span."""
    span.add_event(event_name, attributes=attributes or {})
