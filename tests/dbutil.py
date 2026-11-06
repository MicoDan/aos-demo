"""Create (if needed) a throwaway test database next to the real one on the same server."""
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def ensure_test_db(url: str, name: str) -> str:
    u = make_url(url)
    admin = create_engine(u, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        if not c.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name}).first():
            c.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()
    return u.set(database=name).render_as_string(hide_password=False)
