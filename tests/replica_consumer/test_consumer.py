import json
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from replica_consumer.handler import process_message

TASK = str(uuid.uuid4())


def ev(etype="task.updated", version=1, status="pending", title="t", task_id=TASK, event_id=None, user="u1"):
    ts = datetime.now(timezone.utc).isoformat()
    return {
        "event_id": event_id or str(uuid.uuid4()), "event_type": etype, "task_id": task_id,
        "user_id": user, "version": version, "occurred_at": ts,
        "task": {"id": task_id, "title": title, "description": None, "status": status, "due_date": None,
                 "created_by": user, "created_at": ts, "updated_at": ts},
        "changes": {},
    }


class DLQ:
    def __init__(self):
        self.items = []

    def __call__(self, raw, reason):
        self.items.append((raw, reason))


def send(engine, event, dlq=None):
    raw = event if isinstance(event, (bytes, type(None))) else json.dumps(event).encode()
    return process_message(engine, raw, dlq or DLQ())


def row(engine):
    with engine.connect() as c:
        return c.execute(text("SELECT title, status, version, deleted_at FROM tasks_replica")).first()


def count(engine, table):
    with engine.connect() as c:
        return c.execute(text(f"SELECT count(*) FROM {table}")).scalar()


def test_apply_create(engine):
    assert send(engine, ev("task.created", 1, title="hello")) == "applied"
    r = row(engine)
    assert (r.title, r.version, r.deleted_at) == ("hello", 1, None)


def test_duplicate_event_is_idempotent(engine):
    e = ev("task.updated", 2, title="once")
    send(engine, e)
    before = row(engine)
    send(engine, e)
    send(engine, e)
    assert count(engine, "task_activity") == 1
    assert count(engine, "tasks_replica") == 1
    assert row(engine) == before


def test_out_of_order_v3_before_v2(engine):
    send(engine, ev("task.updated", 3, status="completed", title="v3"))
    send(engine, ev("task.updated", 2, status="in_progress", title="v2"))
    r = row(engine)
    assert (r.title, r.status, r.version) == ("v3", "completed", 3)
    assert count(engine, "task_activity") == 2  # both are logged, only v3 shapes state


def test_delete_removes_replica_row(engine):
    send(engine, ev("task.created", 1, title="a"))
    assert row(engine) is not None
    send(engine, ev("task.deleted", 2, title="a"))
    assert row(engine) is None                     # physically gone, like System A
    assert count(engine, "tasks_replica") == 0
    assert count(engine, "task_activity") == 2     # history is still logged


def test_delete_of_unknown_task_is_noop(engine):
    send(engine, ev("task.deleted", 2))
    assert count(engine, "tasks_replica") == 0


def test_redelivered_delete_is_idempotent(engine):
    send(engine, ev("task.created", 1))
    d = ev("task.deleted", 2)
    send(engine, d)
    send(engine, d)
    assert count(engine, "tasks_replica") == 0
    assert count(engine, "task_activity") == 2


def test_same_version_completed_after_updated(engine):
    send(engine, ev("task.updated", 2, status="completed"))
    send(engine, ev("task.completed", 2, status="completed"))
    assert row(engine).version == 2 and count(engine, "task_activity") == 2


@pytest.mark.parametrize("raw", [
    b"not json at all",
    b"\xff\xfe",
    b"{}",
    json.dumps({**ev(), "event_type": "task.exploded"}).encode(),
    json.dumps({**ev(), "version": 0}).encode(),
    None,
])
def test_malformed_goes_to_dlq(engine, raw):
    dlq = DLQ()
    assert process_message(engine, raw, dlq) == "dlq"
    assert len(dlq.items) == 1 and dlq.items[0][1]
    assert count(engine, "tasks_replica") == 0 and count(engine, "task_activity") == 0


def test_db_failure_propagates_and_rolls_back(engine, monkeypatch):
    from replica_consumer import handler

    real = handler.UPSERT_SQL
    monkeypatch.setattr(handler, "UPSERT_SQL", text("INSERT INTO nonexistent VALUES (1)"))
    with pytest.raises(Exception):
        send(engine, ev("task.created", 1))
    monkeypatch.setattr(handler, "UPSERT_SQL", real)
    assert count(engine, "task_activity") == 0  # activity insert rolled back with it


NEWF = {"project": "P1", "attachments": [{"name": "a.pdf", "url": None, "content_type": None, "size": None}],
        "parent_task": str(uuid.uuid4()), "priority": "critical", "assignees": ["x", "y"],
        "lead_institution": "Lead", "supporting_institutions_within_gsas": ["W1"],
        "supporting_institutions_outside_gsas": ["O1", "O2"], "date_issued": "2026-02-02", "labels": ["l1"]}


def test_all_task_fields_applied_to_replica(engine):
    e = ev("task.created", 1)
    e["task"].update(NEWF)
    send(engine, e)
    with engine.connect() as c:
        r = c.execute(text("SELECT * FROM tasks_replica")).mappings().one()
    for k, v in NEWF.items():
        assert str(r[k]) == str(v) if k in ("parent_task", "date_issued") else r[k] == v, k


def test_legacy_event_without_new_fields_still_applies(engine):
    send(engine, ev("task.created", 1))  # ev() has none of the new fields
    with engine.connect() as c:
        r = c.execute(text("SELECT priority, labels, attachments, project, date_issued FROM tasks_replica")).one()
    assert r.priority == "medium" and r.labels == [] and r.attachments == [] and r.project is None
    assert r.date_issued is not None  # falls back to the creation date
