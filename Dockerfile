# Dockerfile — multi-stage production image
FROM python:3.11-slim AS base
WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN pip install --upgrade pip

FROM base AS builder
COPY backend/pyproject.toml backend/ /app/backend/
RUN pip wheel -w /wheels -e /app/backend

FROM base AS runtime
COPY --from=builder /wheels /wheels
RUN pip install /wheels/* && rm -rf /wheels
COPY backend /app/backend
ENV APP_ENV=prod
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
