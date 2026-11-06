"""Task mutations. Each one writes the task change AND its outbox row(s) in the
caller's single DB transaction (the caller commits). Nothing here talks to Kafka."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskcommon.events import TaskEvent, new_event

from .models import OutboxEvent, Task


# every standard, directly-stored task field a client may write
EDITABLE = ("title", "description", "status", "due_date", "project", "attachments", "parent_task",
            "priority", "assignees", "lead_institution", "supporting_institutions_within_gsas",
            "supporting_institutions_outside_gsas", "date_issued", "labels")
LIST_FIELDS = ("attachments", "assignees", "labels", "supporting_institutions_within_gsas",
               "supporting_institutions_outside_gsas")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def snapshot(t: Task) -> dict:
    return {
        "id": t.id, "title": t.title, "description": t.description, "status": t.status,
        "due_date": t.due_date, "created_by": t.created_by,
        "created_at": t.created_at, "updated_at": t.updated_at,
        **{f: getattr(t, f) for f in EDITABLE if f not in ("title", "description", "status", "due_date")},
    }


def add_outbox(session: Session, event: TaskEvent) -> None:
    session.add(OutboxEvent(
        id=event.event_id,
        aggregate_id=event.task_id,
        event_type=event.event_type,
        payload=event.model_dump(mode="json"),
        created_at=_now(),
    ))
    session.flush()


def is_owned_task(session: Session, task_id, user_id: str) -> bool:
    return session.scalar(select(Task.id).where(Task.id == task_id, Task.created_by == user_id)) is not None


def create_task(session: Session, user_id: str, data) -> Task:
    now = _now()
    values = data.model_dump()
    values["date_issued"] = values["date_issued"] or now.date()
    if values["parent_task"] is not None and not is_owned_task(session, values["parent_task"], user_id):
        raise ValueError("parent_task must be one of your tasks")
    task = Task(id=uuid.uuid4(), created_by=user_id, created_at=now, updated_at=now, version=1, **values)
    session.add(task)
    session.flush()
    add_outbox(session, new_event("task.created", snapshot(task), task.version, user_id))
    return task


def update_task(session: Session, task: Task, data) -> Task:
    changes = {}
    for field, new in data.model_dump(exclude_unset=True).items():
        if new is None and field in ("title", "status", "priority", "date_issued"):
            continue  # required fields cannot be cleared
        if new is None and field in LIST_FIELDS:
            new = []
        if field == "parent_task" and new is not None:
            if new == task.id:
                raise ValueError("a task cannot be its own parent")
            if not is_owned_task(session, new, task.created_by):
                raise ValueError("parent_task must be one of your tasks")
        old = getattr(task, field)
        if old != new:
            changes[field] = {"old": old, "new": new}
            setattr(task, field, new)
    if not changes:
        return task  # nothing changed: no version bump, no event
    task.version += 1
    task.updated_at = _now()
    session.flush()
    jsonable = {k: {"old": _j(v["old"]), "new": _j(v["new"])} for k, v in changes.items()}
    add_outbox(session, new_event("task.updated", snapshot(task), task.version, task.created_by, jsonable))
    if "status" in changes and changes["status"]["new"] == "completed":
        add_outbox(session, new_event("task.completed", snapshot(task), task.version,
                                      task.created_by, {"status": jsonable["status"]}))
    return task


def delete_task(session: Session, task: Task) -> None:
    task.version += 1  # tombstone version, so B's version guard can order it
    task.updated_at = _now()
    session.flush()
    add_outbox(session, new_event("task.deleted", snapshot(task), task.version, task.created_by))
    session.delete(task)
    session.flush()


def _j(v):
    if isinstance(v, uuid.UUID):
        return str(v)
    return v.isoformat() if hasattr(v, "isoformat") else v
