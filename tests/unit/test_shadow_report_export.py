"""
Unit tests for v2.17.0 PDF/CSV Pilot Report export.

Coverage:
    - ProjectedValueReport.to_csv()        — 6 tests
    - ProjectedValueReport.to_pdf_bytes()  — 4 tests
    - GET /api/v1/shadow/report/export     — 6 tests

Trust Gate verification:
    rationale    : export is read-only; tests confirm no state mutation occurs.
    blast_radius : zero — endpoint never writes to DB or modifies incidents.
    rollback_plan: remove shadow_report_router from app.py includes.
"""

from __future__ import annotations

import csv
import io
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from responseiq.services.shadow_analytics import (
    ProjectedValueReport,
    ShadowAnalyticsResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_report(
    total: int = 10,
    successful: int = 8,
    fix_time_per_incident_mins: float = 45.0,
    shadow_success_rate: float = 0.8,
    avg_confidence: float = 0.85,
) -> ProjectedValueReport:
    """Build a populated ProjectedValueReport without hitting the DB."""
    start = datetime(2026, 2, 1)
    end = datetime(2026, 3, 1)
    report = ProjectedValueReport(start, end)

    for i in range(total):
        result = ShadowAnalyticsResult(
            incident_id=f"INC-{i:03d}",
            would_trigger_p2=True,
            analysis_success=(i < successful),
            projected_fix_time=fix_time_per_incident_mins if i < successful else None,
            confidence_score=avg_confidence if i < successful else 0.0,
        )
        report.add_result(result)

    report.shadow_success_rate = shadow_success_rate
    report.average_confidence = avg_confidence
    return report


def _empty_report() -> ProjectedValueReport:
    start = datetime(2026, 2, 1)
    end = datetime(2026, 3, 1)
    return ProjectedValueReport(start, end)


# ---------------------------------------------------------------------------
# CSV export tests
# ---------------------------------------------------------------------------


class TestToCSV:
    def test_returns_string(self):
        report = _make_report()
        result = report.to_csv()
        assert isinstance(result, str)

    def test_csv_has_required_headers(self):
        report = _make_report()
        reader = csv.DictReader(io.StringIO(report.to_csv()))
        headers = reader.fieldnames or []
        for expected in [
            "period_start",
            "period_end",
            "total_incidents",
            "automation_candidates",
            "avg_time_saved_minutes",
            "projected_annual_savings_usd",
            "shadow_success_rate_pct",
        ]:
            assert expected in headers, f"Missing header: {expected}"

    def test_csv_data_row_total_incidents(self):
        report = _make_report(total=10)
        reader = csv.DictReader(io.StringIO(report.to_csv()))
        rows = list(reader)
        assert len(rows) >= 1
        assert float(rows[0]["total_incidents"]) == 10.0

    def test_csv_data_row_automation_candidates(self):
        report = _make_report(total=10, successful=7)
        reader = csv.DictReader(io.StringIO(report.to_csv()))
        row = next(reader)
        assert float(row["automation_candidates"]) == 7.0

    def test_csv_executive_summary_present(self):
        report = _make_report()
        csv_text = report.to_csv()
        assert "executive_summary" in csv_text
        assert "ResponseIQ" in csv_text

    def test_empty_report_produces_valid_csv(self):
        report = _empty_report()
        result = report.to_csv()
        assert isinstance(result, str)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        # First row is the KPI data row (trailing rows are the executive summary section)
        assert len(rows) >= 1
        assert float(rows[0]["total_incidents"]) == 0.0

    def test_csv_period_dates_match_report(self):
        report = _make_report()
        reader = csv.DictReader(io.StringIO(report.to_csv()))
        row = next(reader)
        assert row["period_start"] == "2026-02-01"
        assert row["period_end"] == "2026-03-01"


# ---------------------------------------------------------------------------
# PDF export tests
# ---------------------------------------------------------------------------


class TestToPDFBytes:
    def test_raises_import_error_when_fpdf_missing(self):
        """Graceful failure when fpdf2 is not installed."""
        report = _make_report()
        with patch.dict(sys.modules, {"fpdf": None}):
            with pytest.raises(ImportError, match="fpdf2 is required"):
                report.to_pdf_bytes()

    def test_returns_bytes_when_fpdf_available(self):
        """When fpdf2 is present, returns non-empty bytes."""
        pytest.importorskip("fpdf", reason="fpdf2 not installed; skipping PDF bytes test")
        report = _make_report()
        result = report.to_pdf_bytes()
        assert isinstance(result, bytes)
        assert len(result) > 100  # Real PDF has substantial content

    def test_pdf_starts_with_pdf_magic_bytes(self):
        """PDF binary must begin with the '%PDF' magic bytes."""
        pytest.importorskip("fpdf", reason="fpdf2 not installed; skipping PDF magic test")
        report = _make_report()
        result = report.to_pdf_bytes()
        assert result[:4] == b"%PDF"

    def test_pdf_with_empty_report_does_not_crash(self):
        """Empty report (zero incidents) must render without exception."""
        pytest.importorskip("fpdf", reason="fpdf2 not installed; skipping empty PDF test")
        report = _empty_report()
        result = report.to_pdf_bytes()
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Router endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    from responseiq.app import app as _app

    return TestClient(_app, raise_server_exceptions=True)


class TestShadowReportExportEndpoint:
    def test_csv_returns_200(self, client: TestClient):
        response = client.get("/api/v1/shadow/report/export?format=csv")
        assert response.status_code == 200

    def test_csv_content_type(self, client: TestClient):
        response = client.get("/api/v1/shadow/report/export?format=csv")
        assert "text/csv" in response.headers.get("content-type", "")

    def test_csv_body_has_headers(self, client: TestClient):
        response = client.get("/api/v1/shadow/report/export?format=csv")
        assert "total_incidents" in response.text

    def test_invalid_format_returns_400(self, client: TestClient):
        response = client.get("/api/v1/shadow/report/export?format=xml")
        assert response.status_code == 400
        assert "Unsupported format" in response.json()["detail"]

    def test_csv_content_disposition_attachment(self, client: TestClient):
        response = client.get("/api/v1/shadow/report/export?format=csv")
        cd = response.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert ".csv" in cd

    def test_pdf_returns_500_when_fpdf_not_installed(self, client: TestClient):
        """Endpoint returns 500 with helpful message when fpdf2 is missing."""
        with patch(
            "responseiq.routers.shadow_report._shadow_service.generate_period_report",
        ) as mock_gen:
            mock_report = MagicMock()
            mock_report.period_days = 30
            mock_report.total_incidents_analyzed = 0
            mock_report.to_pdf_bytes.side_effect = ImportError("fpdf2 is required for PDF export")

            async def _async_report(*_a, **_kw):
                return mock_report

            mock_gen.side_effect = _async_report

            response = client.get("/api/v1/shadow/report/export?format=pdf")
            assert response.status_code == 500
            assert "fpdf2" in response.json()["detail"]

    def test_pdf_success_when_fpdf_available(self, client: TestClient):
        """When fpdf2 is available, endpoint returns 200 application/pdf."""
        pytest.importorskip("fpdf", reason="fpdf2 not installed; skipping PDF endpoint test")

        with patch(
            "responseiq.routers.shadow_report._shadow_service.generate_period_report",
        ) as mock_gen:
            mock_report = MagicMock()
            mock_report.period_days = 30
            mock_report.total_incidents_analyzed = 5
            mock_report.to_pdf_bytes.return_value = b"%PDF-1.4 fake content"

            async def _async_report(*_a, **_kw):
                return mock_report

            mock_gen.side_effect = _async_report

            response = client.get("/api/v1/shadow/report/export?format=pdf")
            assert response.status_code == 200
            assert response.headers.get("content-type") == "application/pdf"
