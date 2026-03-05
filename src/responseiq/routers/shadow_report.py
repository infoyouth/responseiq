"""
Shadow Report Export Router — v2.17.0 PDF/CSV Pilot Report.

Endpoint:
    GET /api/v1/shadow/report/export

Query params:
    format   csv | pdf  (default: csv)
    days     integer    lookback window (default: 30)

Produces:
    text/csv; charset=utf-8          when format=csv
    application/pdf                  when format=pdf

Trust Gate:
    - rationale  : Exposes ProjectedValueReport KPIs as downloadable artifacts
                   so VP-level stakeholders can paste numbers into board decks.
    - blast_radius: read-only; never mutates any DB or incident state.
    - rollback_plan: remove router include from app.py – zero side-effects.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from responseiq.services.shadow_analytics import ProjectedValueReport, ShadowAnalyticsService
from responseiq.utils.logger import logger

router = APIRouter(prefix="/api/v1/shadow", tags=["Shadow Analytics"])

# Lazily initialized to avoid triggering the full service init chain at import time.
_shadow_service: ShadowAnalyticsService | None = None


def _get_shadow_service() -> ShadowAnalyticsService:
    global _shadow_service
    if _shadow_service is None:
        _shadow_service = ShadowAnalyticsService()
    return _shadow_service


@router.get(
    "/report/export",
    summary="Export the Shadow Mode Pilot Report as CSV or PDF",
    responses={
        200: {"description": "Report file download"},
        400: {"description": "Unsupported format"},
        422: {"description": "Validation error on query params"},
        500: {"description": "PDF library not installed"},
    },
)
async def export_shadow_report(
    format: str = Query(default="csv", description="Export format: 'csv' or 'pdf'"),
    days: int = Query(default=30, ge=1, le=365, description="Lookback window in days"),
) -> Response:
    """
    Generate and stream a Pilot Value Report.

    The report is built from all shadow-analysis results accumulated by the
    in-memory ``ShadowAnalyticsService`` during the requested lookback window.
    When the service has no results yet (e.g. fresh deployment) a synthetic
    empty report is returned — all KPIs will show zero, which is truthful.

    Args:
        format: ``csv`` returns a UTF-8 CSV file.  ``pdf`` returns a rendered
                A4 PDF (requires ``fpdf2``; install with
                ``pip install "responseiq[reports]"``).
        days:   Number of calendar days to include (1–365).

    Returns:
        ``Response`` with the correct content-type and a ``Content-Disposition``
        attachment header so browsers trigger a file download.

    Raises:
        HTTPException 400: unknown format string.
        HTTPException 500: fpdf2 not installed when format=pdf requested.
    """
    fmt = format.lower().strip()
    if fmt not in {"csv", "pdf"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{format}'. Use 'csv' or 'pdf'.",
        )

    # Build report from accumulated shadow results
    report: ProjectedValueReport = await _get_shadow_service().generate_period_report(days_back=days)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_stem = f"responseiq_pilot_report_{timestamp}"

    if fmt == "csv":
        logger.info(f"📄 Exporting shadow report as CSV (days={days})")
        content = report.to_csv().encode("utf-8")
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename_stem}.csv"',
                "X-Report-Period-Days": str(report.period_days),
                "X-Report-Total-Incidents": str(report.total_incidents_analyzed),
            },
        )

    # fmt == "pdf"
    logger.info(f"📄 Exporting shadow report as PDF (days={days})")
    try:
        content_bytes = report.to_pdf_bytes()
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=('fpdf2 is not installed. Add the reports extra: pip install "responseiq[reports]"'),
        ) from exc

    return Response(
        content=content_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_stem}.pdf"',
            "X-Report-Period-Days": str(report.period_days),
            "X-Report-Total-Incidents": str(report.total_incidents_analyzed),
        },
    )
