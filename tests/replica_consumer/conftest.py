import os

import pytest
from sqlalchemy import create_engine, text
from pathlib import Path

from dbutil import ensure_test_db
from taskcommon.migrate import run_migrations

URL = ensure_test_db(os.environ["DB_B_URL"], "replica_test")
MIGRATIONS = Path(__file__).resolve().parents[2] / "system-b" / "migrations"


@pytest.fixture(scope="session")
def engine():
    e = create_engine(URL)
    run_migrations(e, MIGRATIONS)
    yield e
    e.dispose()


@pytest.fixture(autouse=True)
def clean(engine):
    with engine.begin() as c:
        c.execute(text("TRUNCATE tasks_replica, task_activity"))
