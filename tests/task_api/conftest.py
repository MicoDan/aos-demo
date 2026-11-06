import os

import pytest
from sqlalchemy import text

from dbutil import ensure_test_db

os.environ["DB_A_URL"] = ensure_test_db(os.environ["DB_A_URL"], "tasks_test")
os.environ.setdefault("KEYCLOAK_ISSUER", "http://localhost:8080/realms/taskapp")
os.environ.setdefault("KEYCLOAK_JWKS_URL", "http://unused/certs")

from fastapi.testclient import TestClient  # noqa: E402

import jwtutil  # noqa: E402
from task_api.db import engine  # noqa: E402
from task_api.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    app.state.validator = jwtutil.make_validator()
    with TestClient(app, raise_server_exceptions=False) as c:  # runs migrations
        yield c


@pytest.fixture(autouse=True)
def clean(client):
    with engine.begin() as c:
        c.execute(text("TRUNCATE tasks, outbox_events"))
    yield


@pytest.fixture
def db():
    with engine.connect() as c:
        yield c
