FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY backend /app/backend
COPY backend/requirements.txt /app/backend/requirements.txt
COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt && pip install --no-cache-dir -r /app/worker/requirements.txt

COPY worker /app/worker

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "worker.worker"]
