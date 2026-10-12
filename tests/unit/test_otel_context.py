# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors

import json

from responseiq.utils.otel_context import parse_otel_json_log_line


def test_parse_otel_json_log_record_preserves_standard_context_and_provenance():
    line = json.dumps(
        {
            "body": {"stringValue": "database timeout"},
            "timeUnixNano": "1791820800000000000",
            "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
            "spanId": "00f067aa0ba902b7",
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "payments"}},
                    {"key": "deployment.environment.name", "value": {"stringValue": "production"}},
                    {"key": "deployment.id", "value": {"stringValue": "deploy-42"}},
                ]
            },
        }
    )

    parsed = parse_otel_json_log_line(line)

    assert parsed is not None
    assert parsed.body == "database timeout"
    assert parsed.context.service_name == "payments"
    assert parsed.context.deployment_environment_name == "production"
    assert parsed.context.deployment_id == "deploy-42"
    assert parsed.context.observed_at.isoformat() == "2026-10-12T16:00:00+00:00"
    assert parsed.context.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parsed.context.span_id == "00f067aa0ba902b7"
    assert parsed.context.provenance["service_name"] == "resource.attributes[service.name]"
    assert parsed.context.provenance["trace_id"] == "log_record.traceId"
    assert parsed.context.provenance["observed_at"] == "log_record.timeUnixNano"


def test_flat_attributes_are_supported_and_invalid_trace_ids_are_not_carried():
    parsed = parse_otel_json_log_line(
        json.dumps(
            {
                "message": "cache miss",
                "trace_id": "not-an-otel-trace-id",
                "attributes": {
                    "service.name": "cache",
                    "deployment.environment.name": "staging",
                },
            }
        )
    )

    assert parsed is not None
    assert parsed.context.service_name == "cache"
    assert parsed.context.deployment_environment_name == "staging"
    assert parsed.context.trace_id is None


def test_non_otel_log_line_is_left_to_existing_parser():
    assert parse_otel_json_log_line("plain ERROR log line") is None
    assert parse_otel_json_log_line('{"message":"ordinary JSON log"}') is None
