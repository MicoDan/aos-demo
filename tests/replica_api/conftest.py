import os
from pathlib import Path

import pytest
from sqlalchemy import text

from dbutil import ensure_test_db

os.environ["DB_B_URL"] = ensure_test_db(os.environ["DB_B_URL"], "replica_api_test")
os.environ["MIGRATIONS_DIR"] = str(Path(__file__).resolve().parents[2] / "system-b" / "migrations")
os.environ.setdefault("KEYCLOAK_ISSUER", "http://localhost:8080/realms/taskapp")
os.environ.setdefault("KEYCLOAK_JWKS_URL", "http://unused/certs")

from fastapi.testclient import TestClient  # noqa: E402

import jwtutil  # noqa: E402
from replica_api.main import app, engine  # noqa: E402


@pytest.fixture(scope="session")
def client():
    app.state.validator = jwtutil.make_validator()
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean(client):
    with engine.begin() as c:
        c.execute(text("TRUNCATE tasks_replica, task_activity"))


@pytest.fixture
def put_task():
    def _put(user="user-1", status="pending", deleted=False, updated_days_ago=0, title="t"):
        with engine.begin() as c:
            c.execute(text("""
                INSERT INTO tasks_replica (id, title, status, created_by, created_at, updated_at, version,
                                           deleted_at, last_event_id, synced_at, date_issued)
                VALUES (gen_random_uuid(), :t, :s, :u, now(), now() - make_interval(days => :d), 1,
                        CASE WHEN :del THEN now() END, gen_random_uuid(), now(), current_date)"""),
                {"t": title, "s": status, "u": user, "d": updated_days_ago, "del": deleted})
    return _put


@pytest.fixture
def put_activity():
    def _put(user="user-1", etype="task.created", n=1):
        with engine.begin() as c:
            for i in range(n):
                c.execute(text("""
                    INSERT INTO task_activity VALUES (gen_random_uuid(), gen_random_uuid(), :u, :e,
                      '{"title": "x", "version": 1}'::jsonb, now() + make_interval(secs => :i), now())"""),
                    {"u": user, "e": etype, "i": i})
    return _put
