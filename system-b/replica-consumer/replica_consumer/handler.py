"""Applies Kafka events to DB-B. Idempotent via event_id and a per-task version guard.

A task.deleted event physically deletes the task from tasks_replica."""
import json
import logging

from pydantic import ValidationError
from sqlalchemy import text

from taskcommon.events import TaskEvent

log = logging.getLogger("replica")

ACTIVITY_SQL = text("""
    INSERT INTO task_activity (event_id, task_id, user_id, event_type, details, occurred_at, processed_at)
    VALUES (:event_id, :task_id, :user_id, :event_type, CAST(:details AS jsonb), :occurred_at, now())
    ON CONFLICT (event_id) DO NOTHING
""")

_COLS = "id, title, description, status, due_date, created_by, created_at, updated_at, version, deleted_at, last_event_id, synced_at, project, attachments, parent_task, priority, assignees, lead_institution, supporting_institutions_within_gsas, supporting_institutions_outside_gsas, date_issued, labels"
_SET = """title = EXCLUDED.title, description = EXCLUDED.description, status = EXCLUDED.status,
          due_date = EXCLUDED.due_date, created_by = EXCLUDED.created_by,
          created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at,
          version = EXCLUDED.version, deleted_at = EXCLUDED.deleted_at,
          last_event_id = EXCLUDED.last_event_id, synced_at = EXCLUDED.synced_at,
          project = EXCLUDED.project, attachments = EXCLUDED.attachments,
          parent_task = EXCLUDED.parent_task, priority = EXCLUDED.priority,
          assignees = EXCLUDED.assignees, lead_institution = EXCLUDED.lead_institution,
          supporting_institutions_within_gsas = EXCLUDED.supporting_institutions_within_gsas,
          supporting_institutions_outside_gsas = EXCLUDED.supporting_institutions_outside_gsas,
          date_issued = EXCLUDED.date_issued, labels = EXCLUDED.labels"""

# created/updated/completed: only a strictly newer version wins
UPSERT_SQL = text(f"""
    INSERT INTO tasks_replica ({_COLS})
    VALUES (:id, :title, :description, :status, :due_date, :created_by, :created_at,
            :updated_at, :version, NULL, :event_id, now(),
            :project, CAST(:attachments AS jsonb), :parent_task, :priority, CAST(:assignees AS jsonb),
            :lead_institution, CAST(:within AS jsonb), CAST(:outside AS jsonb), :date_issued,
            CAST(:labels AS jsonb))
    ON CONFLICT (id) DO UPDATE SET {_SET}
    WHERE tasks_replica.version < EXCLUDED.version
""")

# deleted: the replica row is physically removed (same as System A). Nothing is kept.
REMOVE_SQL = text("DELETE FROM tasks_replica WHERE id = :id")


class MalformedEvent(Exception):
    pass


def parse_event(raw) -> TaskEvent:
    if raw is None:
        raise MalformedEvent("empty message value")
    try:
        return TaskEvent.model_validate(json.loads(raw))
    except (ValueError, ValidationError, TypeError) as e:  # JSON/UTF-8/schema errors
        raise MalformedEvent(str(e)[:500]) from e


def apply_event(conn, event: TaskEvent) -> None:
    """Runs inside ONE DB-B transaction owned by the caller."""
    t = event.task
    conn.execute(ACTIVITY_SQL, {
        "event_id": event.event_id, "task_id": event.task_id, "user_id": event.user_id,
        "event_type": event.event_type, "occurred_at": event.occurred_at,
        "details": json.dumps({"title": t.title, "status": t.status,
                               "version": event.version, "changes": event.changes}),
    })
    params = {
        "id": t.id, "title": t.title, "description": t.description, "status": t.status,
        "due_date": t.due_date, "created_by": t.created_by, "created_at": t.created_at,
        "updated_at": t.updated_at, "version": event.version, "event_id": event.event_id,
        "occurred_at": event.occurred_at,
        "project": t.project, "attachments": json.dumps([a.model_dump() for a in t.attachments]),
        "parent_task": t.parent_task, "priority": t.priority, "assignees": json.dumps(t.assignees),
        "lead_institution": t.lead_institution,
        "within": json.dumps(t.supporting_institutions_within_gsas),
        "outside": json.dumps(t.supporting_institutions_outside_gsas),
        "date_issued": t.date_issued, "labels": json.dumps(t.labels),
    }
    conn.execute(REMOVE_SQL if event.event_type == "task.deleted" else UPSERT_SQL, params)


def process_message(engine, raw, publish_dlq) -> str:
    """Returns 'applied' or 'dlq'. DB errors propagate (caller must NOT commit the offset)."""
    try:
        event = parse_event(raw)
    except MalformedEvent as e:
        publish_dlq(raw, str(e))
        return "dlq"
    with engine.begin() as conn:
        apply_event(conn, event)
    return "applied"
