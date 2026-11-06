FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
COPY system-b/replica-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/taskcommon /app/taskcommon
COPY system-b/migrations /app/migrations
COPY system-b/replica-api/replica_api /app/replica_api
EXPOSE 8000
CMD ["uvicorn", "replica_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
