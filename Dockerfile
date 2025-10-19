# Dockerfile — multi-stage production image (API + Worker share this image)
FROM python:3.11-slim AS base
WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- Optional OS packages if/when you enable OCR/PDF rendering ---
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     tesseract-ocr poppler-utils gcc && \
#     rm -rf /var/lib/apt/lists/*

# ---------- Build wheels for pinned deps ----------
FROM base AS builder
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip wheel --no-cache-dir -w /wheels -r /tmp/requirements.txt

# ---------- Runtime image ----------
FROM base AS runtime
# Install wheels (includes rq, redis, etc. from requirements.txt)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY backend /app/backend

# Ensure our package is importable (app.* resolves to /app/backend/app)
ENV PYTHONPATH=/app/backend \
    APP_ENV=prod

EXPOSE 8000

# Default command for API (Compose overrides this for the worker)
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]

# Ensure NLTK tokenizers are present in the image
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)"
