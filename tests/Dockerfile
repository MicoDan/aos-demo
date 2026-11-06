# Shared image for tests and ops tools (seed / compare). Repo is bind-mounted at /work.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/work/common:/work/system-a/task-api:/work/system-a/outbox-publisher:/work/system-b/replica-consumer:/work/system-b/replica-api:/work/tests
RUN pip install --no-cache-dir fastapi==0.115.6 httpx==0.28.1 sqlalchemy==2.0.36 "psycopg[binary]==3.2.3" \
    pydantic==2.10.4 "PyJWT[crypto]==2.10.1" confluent-kafka==2.6.1 pytest==8.3.4 cryptography
WORKDIR /work
