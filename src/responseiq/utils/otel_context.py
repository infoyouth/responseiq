# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Parse a single OpenTelemetry JSON log record without inferring context."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from responseiq.schemas.telemetry import OTelIncidentContext, ParsedOTelLogRecord

_TRACE_ID = re.compile(r"^[0-9a-fA-F]{32}$")
_SPAN_ID = re.compile(r"^[0-9a-fA-F]{16}$")
_OTEL_FIELDS = {
    "service.name",
    "deployment.environment.name",
    "deployment.id",
    "trace_id",
    "trace.id",
    "span_id",
    "span.id",
}


def parse_otel_json_log_line(line: str) -> ParsedOTelLogRecord | None:
    """Parse flattened OTLP JSON log records; return None for ordinary or unsupported lines."""
    try:
        record = json.loads(line)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(record, Mapping):
        return None

    resource_attributes = _attributes(record.get("resource"))
    record_attributes = _attributes(record.get("attributes"))
    service_name, service_source = _first_attribute(
        resource_attributes,
        record_attributes,
        names=("service.name",),
        source_names=("resource.attributes[service.name]", "attributes[service.name]"),
    )
    deployment_environment, deployment_environment_source = _first_attribute(
        resource_attributes,
        record_attributes,
        names=("deployment.environment.name",),
        source_names=(
            "resource.attributes[deployment.environment.name]",
            "attributes[deployment.environment.name]",
        ),
    )
    deployment_id, deployment_id_source = _first_attribute(
        resource_attributes,
        record_attributes,
        names=("deployment.id",),
        source_names=("resource.attributes[deployment.id]", "attributes[deployment.id]"),
    )
    observed_at, observed_at_source = _timestamp(record)

    trace_id = _string(record.get("traceId") or record.get("trace_id"))
    trace_source = "log_record.traceId" if record.get("traceId") else "log_record.trace_id"
    if not trace_id:
        trace_id, trace_source = _first_attribute(
            record_attributes,
            resource_attributes,
            names=("trace_id", "trace.id"),
            source_names=("attributes[trace_id]", "resource.attributes[trace_id]"),
        )
    if trace_id and not _TRACE_ID.fullmatch(trace_id):
        trace_id = None
        trace_source = ""

    span_id = _string(record.get("spanId") or record.get("span_id"))
    span_source = "log_record.spanId" if record.get("spanId") else "log_record.span_id"
    if not span_id:
        span_id, span_source = _first_attribute(
            record_attributes,
            resource_attributes,
            names=("span_id", "span.id"),
            source_names=("attributes[span_id]", "resource.attributes[span_id]"),
        )
    if span_id and not _SPAN_ID.fullmatch(span_id):
        span_id = None
        span_source = ""

    provenance = {
        key: source
        for key, source in (
            ("service_name", service_source),
            ("deployment_environment_name", deployment_environment_source),
            ("deployment_id", deployment_id_source),
            ("observed_at", observed_at_source),
            ("trace_id", trace_source if trace_id else ""),
            ("span_id", span_source if span_id else ""),
        )
        if source
    }
    context = OTelIncidentContext(
        service_name=service_name,
        deployment_environment_name=deployment_environment,
        deployment_id=deployment_id,
        observed_at=observed_at,
        trace_id=trace_id,
        span_id=span_id,
        provenance=provenance,
    )
    if not any((service_name, deployment_environment, deployment_id, observed_at, trace_id, span_id)):
        return None

    body = _string(record.get("body") or record.get("message") or record.get("msg"))
    return ParsedOTelLogRecord(body=body or line, context=context)


def _timestamp(record: Mapping[str, Any]) -> tuple[datetime | None, str]:
    for field, source in (("timeUnixNano", "log_record.timeUnixNano"), ("time_unix_nano", "log_record.time_unix_nano")):
        value = record.get(field)
        if value is None:
            continue
        try:
            return datetime.fromtimestamp(int(value) / 1_000_000_000, tz=timezone.utc), source
        except (OverflowError, OSError, TypeError, ValueError):
            return None, ""

    for field in ("timestamp", "time"):
        value = record.get(field)
        if not isinstance(value, str):
            continue
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None, ""
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc), f"log_record.{field}"
    return None, ""


def _attributes(container: Any) -> dict[str, str]:
    if isinstance(container, Mapping):
        raw_attributes = container.get("attributes", container)
    else:
        raw_attributes = container

    if isinstance(raw_attributes, Mapping):
        return {str(key): text for key, value in raw_attributes.items() if (text := _string(value))}

    attributes: dict[str, str] = {}
    if isinstance(raw_attributes, list):
        for item in raw_attributes:
            if not isinstance(item, Mapping):
                continue
            key = item.get("key")
            text = _string(item.get("value"))
            if isinstance(key, str) and text:
                attributes[key] = text
    return attributes


def _first_attribute(
    first: dict[str, str],
    second: dict[str, str],
    *,
    names: tuple[str, ...],
    source_names: tuple[str, ...],
) -> tuple[str | None, str]:
    for attributes, source in ((first, source_names[0]), (second, source_names[1])):
        for name in names:
            value = attributes.get(name)
            if value and value.strip():
                return value.strip(), source
    return None, ""


def _string(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Mapping):
        for key in ("stringValue", "string_value", "intValue", "int_value", "boolValue", "bool_value"):
            if key in value:
                return _string(value[key])
    return None
