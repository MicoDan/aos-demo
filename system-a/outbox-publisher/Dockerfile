FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
COPY system-a/outbox-publisher/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/taskcommon /app/taskcommon
COPY system-a/outbox-publisher/outbox_publisher /app/outbox_publisher
CMD ["python", "-m", "outbox_publisher.main"]
