FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for better caching)
COPY backend/requirements.txt /app/backend/requirements.txt
COPY worker/requirements.txt /app/worker/requirements.txt

# Install deps (BuildKit cache friendly)
RUN --mount=type=cache,target=/root/.cache/pip     pip install -r /app/backend/requirements.txt &&     pip install -r /app/worker/requirements.txt

# Copy source
COPY backend /app/backend
COPY worker /app/worker

# Healthcheck script
COPY worker/healthcheck.py /usr/local/bin/worker-redis-healthcheck.py

# Healthcheck: verify Redis is reachable
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5   CMD ["python","/usr/local/bin/worker-redis-healthcheck.py"]

# Launch the RQ worker module
CMD ["python","-m","worker.worker"]
