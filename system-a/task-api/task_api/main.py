import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from taskcommon.auth import User, get_current_user, validator_from_env
from taskcommon.logging_setup import setup_logging
from taskcommon.migrate import run_migrations

from . import service
from .db import engine, get_session
from .models import Task
from .schemas import TaskCreate, TaskOut, TaskPage, TaskUpdate

setup_logging()
log = logging.getLogger("task-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations(engine, Path(__file__).parent / "migrations")
    if not hasattr(app.state, "validator"):
        app.state.validator = validator_from_env()
    yield


app = FastAPI(title="Task API (System A)", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("CORS_ORIGIN", "http://localhost:5173")],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(ValueError)
def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}


def _owned(session: Session, task_id: uuid.UUID, user: User, lock: bool = False) -> Task:
    q = select(Task).where(Task.id == task_id, Task.created_by == user.sub)
    if lock:
        q = q.with_for_update()
    task = session.scalars(q).first()
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.get("/tasks", response_model=TaskPage)
def list_tasks(
    status: Optional[Literal["pending", "in_progress", "completed"]] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    where = [Task.created_by == user.sub]
    if status:
        where.append(Task.status == status)
    total = session.scalar(select(func.count()).select_from(Task).where(*where)) or 0
    latest = session.scalar(select(func.max(Task.updated_at)).where(*where))
    items = session.scalars(
        select(Task).where(*where).order_by(Task.created_at.desc(), Task.id).limit(limit).offset(offset)
    ).all()
    return TaskPage(items=items, total=total, limit=limit, offset=offset, latest_updated_at=latest)


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create(data: TaskCreate, user: User = Depends(get_current_user),
           session: Session = Depends(get_session)):
    try:
        task = service.create_task(session, user.sub, data)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return task


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: uuid.UUID, user: User = Depends(get_current_user),
             session: Session = Depends(get_session)):
    return _owned(session, task_id, user)


@app.put("/tasks/{task_id}", response_model=TaskOut)
def update(task_id: uuid.UUID, data: TaskUpdate, user: User = Depends(get_current_user),
           session: Session = Depends(get_session)):
    try:
        task = _owned(session, task_id, user, lock=True)
        service.update_task(session, task, data)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete(task_id: uuid.UUID, user: User = Depends(get_current_user),
           session: Session = Depends(get_session)):
    try:
        task = _owned(session, task_id, user, lock=True)
        service.delete_task(session, task)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return Response(status_code=204)
