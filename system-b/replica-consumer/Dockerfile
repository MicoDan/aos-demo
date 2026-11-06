FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
COPY system-b/replica-consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/taskcommon /app/taskcommon
COPY system-b/migrations /app/migrations
COPY system-b/replica-consumer/replica_consumer /app/replica_consumer
CMD ["python", "-m", "replica_consumer.main"]
