FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
COPY system-a/task-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/taskcommon /app/taskcommon
COPY system-a/task-api/task_api /app/task_api
EXPOSE 8000
CMD ["uvicorn", "task_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
