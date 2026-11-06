import logging
import os
import signal
import time

from confluent_kafka import Consumer, KafkaError, Producer, TopicPartition
from sqlalchemy import create_engine

from taskcommon.heartbeat import beat
from taskcommon.logging_setup import setup_logging
from taskcommon.migrate import run_migrations

from pathlib import Path

from .handler import process_message

setup_logging()
log = logging.getLogger("replica")
stop = False


def _sig(*_):
    global stop
    stop = True
    log.info("shutdown requested")


def main():
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)
    bootstrap = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
    topic = os.environ.get("EVENTS_TOPIC", "task-events")
    dlq_topic = os.environ.get("DLQ_TOPIC", "task-events.dlq")

    engine = create_engine(os.environ["DB_B_URL"], pool_pre_ping=True)
    run_migrations(engine, Path(os.environ.get("MIGRATIONS_DIR", "/app/migrations")))

    dlq_producer = Producer({"bootstrap.servers": bootstrap, "enable.idempotence": True,
                             "message.timeout.ms": 15000})
    consumer = Consumer({
        "bootstrap.servers": bootstrap,
        "group.id": os.environ.get("CONSUMER_GROUP", "replica-consumer"),
        "enable.auto.commit": False,
        "auto.offset.reset": "earliest",
        "session.timeout.ms": 10000,
    })
    consumer.subscribe([topic])
    log.info("replica consumer started: topic=%s group=%s", topic, os.environ.get("CONSUMER_GROUP"))

    current = {}

    def publish_dlq(raw, reason):
        m = current["msg"]
        errors = []
        dlq_producer.produce(
            dlq_topic, key=m.key(), value=raw,
            headers=[("error", reason.encode()), ("source_topic", m.topic().encode()),
                     ("source_partition", str(m.partition()).encode()),
                     ("source_offset", str(m.offset()).encode())],
            on_delivery=lambda err, _m: errors.append(err),
        )
        dlq_producer.flush(20)
        if not errors or errors[0] is not None:
            raise RuntimeError(f"DLQ publish failed: {errors}")
        log.warning("message %s[%d]@%d sent to DLQ: %s", m.topic(), m.partition(), m.offset(), reason)

    while not stop:
        beat()
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                log.error("consumer error: %s", msg.error())
            continue
        current["msg"] = msg
        try:
            process_message(engine, msg.value(), publish_dlq)
            consumer.commit(message=msg, asynchronous=False)  # only AFTER DB-B commit
        except Exception:
            # DB/DLQ trouble: do not commit; rewind to this message and retry
            log.exception("processing failed at %s[%d]@%d; retrying", msg.topic(), msg.partition(), msg.offset())
            try:
                consumer.seek(TopicPartition(msg.topic(), msg.partition(), msg.offset()))
            except Exception:
                log.exception("seek failed")
            time.sleep(2)
    consumer.close()
    log.info("replica consumer stopped cleanly")


if __name__ == "__main__":
    main()
