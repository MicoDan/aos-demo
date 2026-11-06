import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from taskcommon.auth import User, get_current_user, validator_from_env
from taskcommon.logging_setup import setup_logging
from taskcommon.migrate import run_migrations

setup_logging()
log = logging.getLogger("replica-api")
engine = create_engine(os.environ["DB_B_URL"], pool_pre_ping=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # same idempotent, lock-protected migrations as the consumer (both are System B)
    run_migrations(engine, Path(os.environ.get("MIGRATIONS_DIR", "/app/migrations")))
    if not hasattr(app.state, "validator"):
        app.state.validator = validator_from_env()
    yield


app = FastAPI(title="Replica API (System B, read-only)", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("CORS_ORIGIN", "http://localhost:5173")],
    allow_methods=["GET"],
    allow_headers=["Authorization"],
)


class Stats(BaseModel):
    total: int
    pending: int
    in_progress: int
    completed: int
    completed_last_7_days: int


class ActivityItem(BaseModel):
    event_id: str
    task_id: str
    event_type: str
    details: dict
    occurred_at: datetime
    processed_at: datetime


class SyncStatus(BaseModel):
    live_tasks: int
    last_event_id: Optional[str]
    last_synced_at: Optional[datetime]
    seconds_since_sync: Optional[float]
    latest_task_updated_at: Optional[datetime]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats", response_model=Stats)
def stats(user: User = Depends(get_current_user)):
    with engine.connect() as c:
        r = c.execute(text("""
            SELECT count(*) AS total,
                   count(*) FILTER (WHERE status = 'pending') AS pending,
                   count(*) FILTER (WHERE status = 'in_progress') AS in_progress,
                   count(*) FILTER (WHERE status = 'completed') AS completed,
                   count(*) FILTER (WHERE status = 'completed'
                                    AND updated_at >= now() - interval '7 days') AS completed_last_7_days
            FROM tasks_replica
            WHERE created_by = :u AND deleted_at IS NULL
        """), {"u": user.sub}).one()
    return Stats(**r._mapping)


@app.get("/activity", response_model=list[ActivityItem])
def activity(limit: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user)):
    with engine.connect() as c:
        rows = c.execute(text("""
            SELECT event_id, task_id, event_type, details, occurred_at, processed_at
            FROM task_activity WHERE user_id = :u
            ORDER BY occurred_at DESC, processed_at DESC LIMIT :n
        """), {"u": user.sub, "n": limit}).all()
    return [ActivityItem(event_id=str(r.event_id), task_id=str(r.task_id), event_type=r.event_type,
                         details=r.details, occurred_at=r.occurred_at, processed_at=r.processed_at)
            for r in rows]


@app.get("/sync-status", response_model=SyncStatus)
def sync_status(user: User = Depends(get_current_user)):
    with engine.connect() as c:
        live = c.execute(text("""
            SELECT count(*) AS n, max(updated_at) AS latest FROM tasks_replica
            WHERE created_by = :u AND deleted_at IS NULL"""), {"u": user.sub}).one()
        last = c.execute(text("""
            SELECT event_id, processed_at, extract(epoch FROM now() - processed_at) AS age
            FROM task_activity WHERE user_id = :u
            ORDER BY processed_at DESC LIMIT 1"""), {"u": user.sub}).first()
    return SyncStatus(
        live_tasks=live.n,
        last_event_id=str(last.event_id) if last else None,
        last_synced_at=last.processed_at if last else None,
        seconds_since_sync=float(last.age) if last else None,
        latest_task_updated_at=live.latest,
    )
