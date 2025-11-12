FROM python:3.11-slim
WORKDIR /app

# Preinstall UI deps so starts are instant
RUN pip install --no-cache-dir streamlit==1.50.0 pandas==2.3.2 pyarrow==21.0.0

# Copy UI (compose will still mount volume for hot reload)
COPY frontend /app/frontend

EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
