FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend /app/backend
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host","0.0.0.0","--port","8000"]

  CMD curl -fs http://127.0.0.1:8000/healthz || exit 1

HEALTHCHECK --interval=15s --timeout=5s --retries=6 --start-period=10s \
  CMD python -c "import sys,urllib.request; u='http://127.0.0.1:8000/healthz'; \
sys.exit(0 if urllib.request.urlopen(u, timeout=3).getcode()==200 else 1)"
