"""Tiny forward-only SQL migration runner (one per database; no cross-db access)."""
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

log = logging.getLogger("migrate")


def run_migrations(engine: Engine, directory: Path) -> None:
    with engine.begin() as conn:
        # advisory lock so two services starting together don't race
        conn.execute(text("SELECT pg_advisory_xact_lock(727274)"))
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"))
        applied = {r[0] for r in conn.execute(text("SELECT version FROM schema_migrations"))}
        for f in sorted(Path(directory).glob("*.sql")):
            if f.name in applied:
                continue
            log.info("applying migration %s", f.name)
            conn.exec_driver_sql(f.read_text())
            conn.execute(text("INSERT INTO schema_migrations(version) VALUES (:v)"), {"v": f.name})
