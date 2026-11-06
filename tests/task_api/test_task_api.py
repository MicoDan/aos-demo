import uuid

import pytest
from sqlalchemy import text

import jwtutil
from jwtutil import auth


def outbox(db):
    return db.execute(text("SELECT event_type, payload, published_at FROM outbox_events ORDER BY created_at")).all()


def mk(client, title="t1", user="user-1", **extra):
    r = client.post("/tasks", json={"title": title, **extra}, headers=auth(user))
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------- JWT
def test_health_is_public(client):
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize("path", ["/tasks", f"/tasks/{uuid.uuid4()}"])
def test_missing_token_rejected(client, path):
    assert client.get(path).status_code == 401


def test_expired_token_rejected(client):
    assert client.get("/tasks", headers=auth(exp_in=-60)).status_code == 401


def test_wrong_issuer_rejected(client):
    assert client.get("/tasks", headers=auth(iss="http://evil/realms/x")).status_code == 401


def test_bad_signature_rejected(client):
    h = {"Authorization": f"Bearer {jwtutil.bad_signature_token()}"}
    assert client.get("/tasks", headers=h).status_code == 401


def test_wrong_azp_rejected(client):
    assert client.get("/tasks", headers=auth(azp="other-client")).status_code == 401


def test_garbage_token_rejected(client):
    assert client.get("/tasks", headers={"Authorization": "Bearer nope"}).status_code == 401


# ---------------------------------------------------------------- CRUD
def test_crud_roundtrip(client, db):
    t = mk(client, "write docs", description="d", due_date="2030-01-02")
    assert t["version"] == 1 and t["status"] == "pending" and t["created_by"] == "user-1"
    assert client.get(f"/tasks/{t['id']}", headers=auth()).json()["title"] == "write docs"
    r = client.put(f"/tasks/{t['id']}", json={"title": "write more docs"}, headers=auth())
    assert r.status_code == 200 and r.json()["version"] == 2
    assert client.delete(f"/tasks/{t['id']}", headers=auth()).status_code == 204
    assert client.get(f"/tasks/{t['id']}", headers=auth()).status_code == 404


def test_list_filter_and_pagination(client):
    for i in range(5):
        mk(client, f"t{i}", status="completed" if i % 2 else "pending")
    page = client.get("/tasks?limit=2&offset=0", headers=auth()).json()
    assert page["total"] == 5 and len(page["items"]) == 2
    done = client.get("/tasks?status=completed", headers=auth()).json()
    assert done["total"] == 2
    assert client.get("/tasks?status=bogus", headers=auth()).status_code == 422


def test_validation(client):
    assert client.post("/tasks", json={"title": ""}, headers=auth()).status_code == 422
    assert client.post("/tasks", json={"title": "x", "status": "weird"}, headers=auth()).status_code == 422


def test_noop_update_does_not_bump_version_or_emit(client, db):
    t = mk(client)
    r = client.put(f"/tasks/{t['id']}", json={"title": t["title"]}, headers=auth())
    assert r.json()["version"] == 1
    assert len(outbox(db)) == 1


# ---------------------------------------------------------------- ownership
def test_ownership_enforced(client):
    t = mk(client, user="alice")
    h = auth("bob")
    assert client.get(f"/tasks/{t['id']}", headers=h).status_code == 404
    assert client.put(f"/tasks/{t['id']}", json={"title": "hax"}, headers=h).status_code == 404
    assert client.delete(f"/tasks/{t['id']}", headers=h).status_code == 404
    assert client.get("/tasks", headers=h).json()["total"] == 0
    assert client.get(f"/tasks/{t['id']}", headers=auth("alice")).json()["title"] == "t1"


# ---------------------------------------------------------------- outbox
def test_create_writes_one_outbox_row_with_full_snapshot(client, db):
    t = mk(client, "snap")
    rows = outbox(db)
    assert [r.event_type for r in rows] == ["task.created"]
    p = rows[0].payload
    assert p["task_id"] == t["id"] and p["version"] == 1 and p["user_id"] == "user-1"
    assert p["task"]["title"] == "snap" and p["task"]["status"] == "pending"
    assert rows[0].published_at is None
    assert "token" not in str(p).lower()


def test_update_writes_exactly_one_outbox_row(client, db):
    t = mk(client)
    client.put(f"/tasks/{t['id']}", json={"status": "in_progress"}, headers=auth())
    rows = outbox(db)
    assert [r.event_type for r in rows] == ["task.created", "task.updated"]
    assert rows[1].payload["changes"]["status"] == {"old": "pending", "new": "in_progress"}
    assert rows[1].payload["version"] == 2


def test_completion_writes_two_outbox_rows(client, db):
    t = mk(client)
    client.put(f"/tasks/{t['id']}", json={"status": "completed"}, headers=auth())
    rows = outbox(db)
    assert [r.event_type for r in rows] == ["task.created", "task.updated", "task.completed"]
    assert rows[1].payload["version"] == rows[2].payload["version"] == 2


def test_delete_writes_one_outbox_row_with_last_snapshot(client, db):
    t = mk(client, "bye")
    client.delete(f"/tasks/{t['id']}", headers=auth())
    rows = outbox(db)
    assert [r.event_type for r in rows] == ["task.created", "task.deleted"]
    assert rows[1].payload["version"] == 2 and rows[1].payload["task"]["title"] == "bye"


def test_reads_emit_no_events(client, db):
    t = mk(client)
    client.get("/tasks", headers=auth())
    client.get(f"/tasks/{t['id']}", headers=auth())
    assert len(outbox(db)) == 1


def test_create_rolls_back_if_outbox_insert_fails(client, db, monkeypatch):
    from task_api import service

    def boom(*a, **k):
        raise RuntimeError("outbox insert failed")

    monkeypatch.setattr(service, "add_outbox", boom)
    r = client.post("/tasks", json={"title": "ghost"}, headers=auth())
    assert r.status_code == 500
    assert db.execute(text("SELECT count(*) FROM tasks")).scalar() == 0
    assert db.execute(text("SELECT count(*) FROM outbox_events")).scalar() == 0


def test_update_and_delete_roll_back_if_outbox_insert_fails(client, db, monkeypatch):
    from task_api import service

    t = mk(client, "keep")
    monkeypatch.setattr(service, "add_outbox", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    assert client.put(f"/tasks/{t['id']}", json={"status": "completed"}, headers=auth()).status_code == 500
    assert client.delete(f"/tasks/{t['id']}", headers=auth()).status_code == 500
    row = db.execute(text("SELECT status, version FROM tasks")).one()
    assert (row.status, row.version) == ("pending", 1)
    assert db.execute(text("SELECT count(*) FROM outbox_events")).scalar() == 1


# ---------------------------------------------------------------- the 14 standard fields
FULL = {
    "title": "Full task", "project": "Accreditation 2026", "status": "in_progress",
    "description": "all fields", "priority": "high",
    "attachments": [{"name": "plan.pdf", "url": "https://example.org/plan.pdf", "content_type": "application/pdf", "size": 1234}],
    "assignees": ["amina", "jean", "amina", "  "],
    "lead_institution": "Institution A",
    "supporting_institutions_within_gsas": ["Inst B", "Inst C"],
    "supporting_institutions_outside_gsas": ["External D"],
    "date_issued": "2026-01-05", "due_date": "2026-03-01", "labels": ["urgent", "q1"],
}
FIELDS = ["title", "project", "status", "description", "attachments", "parent_task", "priority", "assignees",
          "lead_institution", "supporting_institutions_within_gsas", "supporting_institutions_outside_gsas",
          "date_issued", "due_date", "labels"]


def test_every_task_has_all_fields(client):
    t = mk(client, "bare")  # only a title supplied
    for f in FIELDS:
        assert f in t, f
    assert t["priority"] == "medium" and t["attachments"] == [] and t["labels"] == [] and t["assignees"] == []
    assert t["parent_task"] is None and t["project"] is None and t["lead_institution"] is None
    assert t["date_issued"]  # defaults to today


def test_create_and_read_back_all_fields(client):
    parent = mk(client, "parent")
    t = client.post("/tasks", json={**FULL, "parent_task": parent["id"]}, headers=auth()).json()
    got = client.get(f"/tasks/{t['id']}", headers=auth()).json()
    assert got["assignees"] == ["amina", "jean"]  # trimmed + de-duplicated
    assert got["parent_task"] == parent["id"] and got["priority"] == "high"
    assert got["attachments"][0]["name"] == "plan.pdf"
    for f in FIELDS:
        if f not in ("assignees", "parent_task"):
            assert got[f] == FULL[f], f


def test_event_snapshot_carries_all_fields(client, db):
    client.post("/tasks", json=FULL, headers=auth())
    snap = outbox(db)[0].payload["task"]
    for f in FIELDS:
        assert f in snap, f
    assert snap["lead_institution"] == "Institution A" and snap["labels"] == ["urgent", "q1"]


def test_update_each_field_and_clear(client, db):
    t = client.post("/tasks", json=FULL, headers=auth()).json()
    r = client.put(f"/tasks/{t['id']}", headers=auth(), json={
        "project": "Other", "priority": "critical", "labels": [], "lead_institution": None,
        "supporting_institutions_outside_gsas": ["E", "F"], "assignees": ["z"], "attachments": []}).json()
    assert (r["project"], r["priority"], r["labels"], r["lead_institution"]) == ("Other", "critical", [], None)
    assert r["supporting_institutions_outside_gsas"] == ["E", "F"] and r["attachments"] == [] and r["version"] == 2
    ch = outbox(db)[-1].payload["changes"]
    assert ch["priority"] == {"old": "high", "new": "critical"} and "lead_institution" in ch


def test_fields_are_per_task_and_independent(client):
    a = client.post("/tasks", json={**FULL, "title": "A"}, headers=auth()).json()
    b = mk(client, "B")
    client.put(f"/tasks/{a['id']}", json={"labels": ["changed"]}, headers=auth())
    assert client.get(f"/tasks/{b['id']}", headers=auth()).json()["labels"] == []


def test_invalid_field_values_rejected(client):
    for bad in ({"priority": "urgent"}, {"assignees": [1]}, {"date_issued": "not-a-date"},
                {"attachments": [{"url": "x"}]}, {"labels": [f"l{i}" for i in range(51)]}):
        assert client.post("/tasks", json={"title": "x", **bad}, headers=auth()).status_code == 422, bad


def test_parent_task_rules(client):
    t = mk(client, "child")
    assert client.put(f"/tasks/{t['id']}", json={"parent_task": t["id"]}, headers=auth()).status_code == 422
    assert client.put(f"/tasks/{t['id']}", json={"parent_task": str(uuid.uuid4())}, headers=auth()).status_code == 422
    other = mk(client, "theirs", user="bob")
    assert client.put(f"/tasks/{t['id']}", json={"parent_task": other["id"]}, headers=auth()).status_code == 422
    mine = mk(client, "mine")
    r = client.put(f"/tasks/{t['id']}", json={"parent_task": mine["id"]}, headers=auth())
    assert r.status_code == 200 and r.json()["parent_task"] == mine["id"]
