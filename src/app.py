# replace startup with lifespan
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlmodel import select

from .db import get_session, init_db
from .models import Incident, Log
from .schemas.incident import IncidentOut
from .schemas.log import LogIn, LogOut
from .services.analyzer import analyze_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ResponseIQ MVP",
    lifespan=lifespan,
)


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


POST_LOG_EXAMPLE = {
    "message": "critical: panic when allocating resource",
    "severity": "high",
}


@app.post(
    "/logs",
    status_code=201,
    response_model=LogOut,
    summary="Ingest a log",
)
def ingest_log(
    payload: LogIn,
    session=Depends(get_session),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    # optional API key enforcement for ingestion
    required_key = __import__("os").environ.get("LOG_INGEST_API_KEY")
    if required_key and x_api_key != required_key:
        raise HTTPException(status_code=401, detail="invalid api key")
    # create log (temporarily without analyzer severity)
    log = Log(message=payload.message, severity=payload.severity)
    session.add(log)
    session.commit()
    session.refresh(log)

    # analyze and possibly create an incident
    # persist analyzer-detected severity on the log when available
    incident_meta = analyze_message(log.message)
    if incident_meta:
        detected_sev = incident_meta.get("severity")
        # update log.severity if analyzer found something
        if detected_sev and not log.severity:
            log.severity = detected_sev
            session.add(log)
            session.commit()
            session.refresh(log)

        incident = Incident(
            log_id=log.id,
            severity=detected_sev,
            description=incident_meta.get("reason"),
        )
        session.add(incident)
        session.commit()
        session.refresh(incident)

    return LogOut(
        id=log.id,
        message=log.message,
        severity=log.severity,
    )


@app.get(
    "/incidents",
    response_model=List[IncidentOut],
    summary="List incidents",
)
def list_incidents(
    severity: str | None = None,
    session=Depends(get_session),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    # optional API key enforcement for reading incidents
    read_key = __import__("os").environ.get("LOG_READ_API_KEY")
    if read_key and x_api_key != read_key:
        raise HTTPException(status_code=401, detail="invalid api key")
    q = select(Incident)
    if severity:
        q = q.where(Incident.severity == severity)
    results = session.exec(q).all()
    incidents: List[IncidentOut] = []
    for i in results:
        title = i.description or i.severity or "incident"
        incidents.append(
            IncidentOut(
                id=i.id,
                title=title,
                severity=i.severity,
                description=i.description or "",
            )
        )
    return incidents


# ...existing code above handles app and endpoints
