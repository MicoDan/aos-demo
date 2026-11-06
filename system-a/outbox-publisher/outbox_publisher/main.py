import logging
import os
import signal
import time

from confluent_kafka import Producer
from sqlalchemy import create_engine

from taskcommon.heartbeat import beat
from taskcommon.logging_setup import setup_logging

from .publisher import PublishFailed, publish_batch

setup_logging()
log = logging.getLogger("outbox")
stop = False


def _sig(*_):
    global stop
    stop = True


def make_producer() -> Producer:
    return Producer({
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        "enable.idempotence": True,
        "acks": "all",
        "message.timeout.ms": 10000,
        "linger.ms": 5,
    })


def main():
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)
    engine = create_engine(os.environ["DB_A_URL"], pool_pre_ping=True)
    topic = os.environ.get("EVENTS_TOPIC", "task-events")
    poll = float(os.environ.get("POLL_INTERVAL", "0.5"))
    producer = make_producer()
    backoff = 1.0
    log.info("outbox publisher started, topic=%s", topic)
    while not stop:
        beat()
        try:
            n = publish_batch(engine, producer, topic)
            backoff = 1.0
            if n == 0:
                time.sleep(poll)
        except Exception as e:  # never crash the loop
            if isinstance(e, PublishFailed):
                log.warning("kafka unavailable or delivery failed (%s); retry in %.0fs", e, backoff)
            else:
                log.exception("publish loop error; retry in %.0fs", backoff)
            try:
                producer.purge()
                producer.flush(2)
            except Exception:
                pass
            producer = make_producer()  # fresh producer: recovers from fatal idempotence errors
            end = time.time() + backoff
            while time.time() < end and not stop:
                beat()
                time.sleep(0.5)
            backoff = min(backoff * 2, 15.0)
    producer.flush(5)
    log.info("outbox publisher stopped")


if __name__ == "__main__":
    main()
