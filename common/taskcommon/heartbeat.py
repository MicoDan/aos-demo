"""File heartbeat used by Docker healthchecks for worker processes without an HTTP port."""
from pathlib import Path

_P = Path("/tmp/healthy")


def beat() -> None:
    try:
        _P.touch()
    except OSError:
        pass
