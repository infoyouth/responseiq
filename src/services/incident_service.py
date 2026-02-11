from sqlmodel import Session

from src.db import get_engine
from src.models import Incident, Log
from src.services.analyzer import analyze_message
from src.utils.logger import logger


def process_log_ingestion(log_id: int) -> None:
    """
    Analyzes the log content and creates an incident if triggers are met.
    """
    engine = get_engine()
    with Session(engine) as session:
        log = session.get(Log, log_id)
        if not log:
            logger.warning("Log entry not found during processing.", log_id=log_id)
            return

        # Run analysis logic
        analysis_result = analyze_message(log.message)

        if analysis_result:
            detected_severity = analysis_result.get("severity")
            detected_reason = analysis_result.get("reason")
            detected_source = analysis_result.get("source", "unknown")

            # Update log severity if a higher severity is detected
            if detected_severity:
                log.severity = detected_severity
                session.add(log)

            # Create a new incident record
            incident = Incident(
                log_id=log.id,
                severity=detected_severity,
                description=detected_reason,
                source=detected_source,
            )
            session.add(incident)

            session.commit()
            logger.info("Incident created from log.", incident_id=incident.id, log_id=log.id)
