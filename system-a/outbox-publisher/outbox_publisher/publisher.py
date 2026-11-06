import json
import logging
from typing import Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine

log = logging.getLogger("outbox")

CLAIM_SQL = text("""
    SELECT id, aggregate_id, event_type, payload
    FROM outbox_events
    WHERE published_at IS NULL
    ORDER BY created_at
    LIMIT :n
    FOR UPDATE SKIP LOCKED
""")
MARK_SQL = text("UPDATE outbox_events SET published_at = now() WHERE id = ANY(CAST(:ids AS uuid[]))")


class PublishFailed(Exception):
    pass


def publish_batch(engine: Engine, producer, topic: str, batch_size: int = 100,
                  flush_timeout: float = 20.0) -> int:
    """Claim a batch, publish it, and set published_at ONLY for messages whose delivery
    report succeeded (an in-order prefix). Raises PublishFailed if any were not delivered."""
    failed = False
    delivered_count = 0
    with engine.begin() as conn:
        rows = conn.execute(CLAIM_SQL, {"n": batch_size}).all()
        if not rows:
            return 0
        results: dict = {}

        def make_cb(row_id):
            def cb(err, msg):
                results[row_id] = err
            return cb

        for r in rows:
            producer.produce(
                topic,
                key=str(r.aggregate_id),
                value=json.dumps(r.payload).encode(),
                headers=[("event_type", r.event_type.encode()), ("event_id", str(r.id).encode())],
                on_delivery=make_cb(r.id),
            )
        producer.flush(flush_timeout)

        ok_ids = []
        for r in rows:  # keep order: stop at first undelivered message
            if r.id in results and results[r.id] is None:
                ok_ids.append(r.id)
            else:
                failed = True
                break
        if ok_ids:
            conn.execute(MARK_SQL, {"ids": ok_ids})
        delivered_count = len(ok_ids)
    if failed:
        raise PublishFailed(f"delivered {delivered_count}/{len(rows)}")
    log.info("published %d event(s)", delivered_count)
    return delivered_count
