import sys
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseTelemetry(ABC):
    @abstractmethod
    def emit_event(self, event: str, payload: Optional[dict] = None):
        pass

    @abstractmethod
    def start_span(self, name: str):
        pass

    @abstractmethod
    def log_metric(self, name: str, value: Any):
        pass


class ConsoleTelemetry(BaseTelemetry):
    def emit_event(self, event: str, payload: Optional[dict] = None):
        print(f"[TELEMETRY] {event}: {payload}", file=sys.stderr)

    def start_span(self, name: str):
        print(f"[TELEMETRY] Start span: {name}", file=sys.stderr)

    def log_metric(self, name: str, value: Any):
        print(f"[TELEMETRY] Metric {name}: {value}", file=sys.stderr)


class OTLPTelemetry(BaseTelemetry):
    def emit_event(self, event: str, payload: Optional[dict] = None):
        # Placeholder for future OpenTelemetry integration
        pass

    def start_span(self, name: str):
        pass

    def log_metric(self, name: str, value: Any):
        pass
