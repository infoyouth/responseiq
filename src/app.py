# replace startup with lifespan
from fastapi import FastAPI, HTTPException, Depends
from typing import List
from contextlib import asynccontextmanager
import os

from sqlmodel import select

from .models import Log, Incident
from .services.analyzer import analyze_message
from .db import init_db, get_session
from .schemas.log import LogIn, LogOut
from .schemas.incident import IncidentOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="ResponseIQ MVP", lifespan=lifespan)


POST_LOG_EXAMPLE = {"message": "critical: panic when allocating resource", "severity": "high"}


@app.post("/logs", status_code=201, response_model=LogOut, summary="Ingest a log")
def ingest_log(payload: LogIn, session=Depends(get_session)):
    # create log (temporarily without analyzer severity)
    log = Log(message=payload.message, severity=payload.severity)
    session.add(log)
    session.commit()
    session.refresh(log)

    # analyze and possibly create incident; persist analyzer-detected severity on the log
    incident_meta = analyze_message(log.message)
    if incident_meta:
        detected_sev = incident_meta.get("severity")
        # update log.severity if analyzer found something
        if detected_sev and not log.severity:
            log.severity = detected_sev
            session.add(log)
            session.commit()
            session.refresh(log)

        incident = Incident(log_id=log.id, severity=detected_sev, description=incident_meta.get("reason"))
        session.add(incident)
        session.commit()
        session.refresh(incident)

    return LogOut(id=log.id, message=log.message, severity=log.severity)


@app.get("/incidents", response_model=List[IncidentOut], summary="List incidents")
def list_incidents(severity: str | None = None, session=Depends(get_session)):
    q = select(Incident)
    if severity:
        q = q.where(Incident.severity == severity)
    results = session.exec(q).all()
    return [
        IncidentOut(id=i.id, title=(i.description or i.severity or "incident"), severity=i.severity, description=i.description or "")
        for i in results
    ]

# ...existing code above handles app and endpoints
