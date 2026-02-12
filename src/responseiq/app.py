# replace startup with lifespan
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import select

from .db import get_session, init_db
from .models import Incident, Log
from .routers.blueprints import router as blueprints_router
from .schemas.incident import IncidentOut
from .schemas.log import LogIn, LogOut
from .services.incident_service import process_log_ingestion

# Initialize logging/telemetry early
from .utils.logger import logger
from .utils.telemetry import setup_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Telemetry setup could happen here or at module level,
    # but module level is often needed for instrumenting imports.
    # We'll call the setup function on the app object.
    setup_telemetry(app)
    logger.info("Service started successfully.")
    yield
    logger.info("Service stopping.")


app = FastAPI(
    title="ResponseIQ",
    lifespan=lifespan,
)


# Global Exception Handler for reliability
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unexpected system error.")
    return JSONResponse(
        status_code=500,
        content={"detail": "System encountered an error", "trace_id": "refer_to_logs"},
    )


# include routers

app.include_router(blueprints_router)

# serve static UI
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/ui/blueprints")
def blueprints_ui():
    return RedirectResponse(url="/static/blueprints.html")


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


POST_LOG_EXAMPLE = {
    "message": "critical: panic when allocating resource",
    "severity": "high",
}


@app.post(
    "/logs",
    status_code=202,
    response_model=LogOut,
    summary="Ingest log entry",
)
def ingest_log(
    payload: LogIn,
    background_tasks: BackgroundTasks,
    session=Depends(get_session),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    # optional API key enforcement for ingestion
    required_key = __import__("os").environ.get("LOG_INGEST_API_KEY")
    if required_key and x_api_key != required_key:
        raise HTTPException(status_code=401, detail="invalid api key")

    # 1. Persist Log
    log = Log(message=payload.message, severity=payload.severity)
    session.add(log)
    session.commit()
    session.refresh(log)

    if not log.id:
        raise HTTPException(status_code=500, detail="Database failure: Log ID not generated")

    # 2. Assign analysis task
    background_tasks.add_task(process_log_ingestion, log.id)

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
