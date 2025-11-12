FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend /app/backend
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host","0.0.0.0","--port","8000"]



# CI: ensure alembic is present
RUN python -m pip install --no-cache-dir alembic

# Liveness probe: quick and lenient during cold start
  CMD python -c "import urllib.request,sys;\
try:\
    r=urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=1);\
    sys.exit(0 if getattr(r,'status',200)==200 else 1)\
except Exception:\
    sys.exit(1)"

# Liveness probe: quick and lenient during cold start
  CMD python -c "import urllib.request,sys;\
try:\
    r=urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=1);\
    sys.exit(0 if getattr(r,'status',200)==200 else 1)\
except Exception:\
    sys.exit(1)"

# Dev: Traefik routing regardless of container health
HEALTHCHECK NONE
