from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.config.settings import settings


def setup_telemetry(app: FastAPI):
    """
    Initialize OpenTelemetry instrumentation.
    """
    # Create Resource (Service Name, Version, etc.)
    resource = Resource.create(
        {
            "service.name": settings.app_name,
            "service.environment": settings.environment,
        }
    )

    # Set up Tracer Provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Configure Exporter
    if settings.otel_exporter_otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        span_processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(span_processor)
    else:
        # For MVP/Dev without endpoint, valid to just log or use no-op
        pass

    # We'll just add the LoggingInstrumentor globally
    # This correlates Python logs with Trace IDs automatically
    LoggingInstrumentor().instrument(set_logging_format=True)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

    return provider
