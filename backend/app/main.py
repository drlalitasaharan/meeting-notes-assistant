# backend/app/main.py
import os
from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import configure_logging, get_logger
from app.core.errors import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)

from app.routers.health import router as health_router
from app.routers.meetings import router as meetings_router
from app.routers.slides import router as slides_router
from app.deps import demo_auth_dependency  # simple auth stub

# -------------------------------------------------------------------
# App configuration
# -------------------------------------------------------------------
APP_ENV = os.getenv("APP_ENV", "dev").lower()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_TITLE = os.getenv("APP_NAME", "meeting-notes-assistant")
API_VERSION = os.getenv("APP_VERSION", "0.1.0")
API_DESC = "Phase 1 polished endpoints with slides download + docs"

# Configure JSON logging early
configure_logging(LOG_LEVEL)
log = get_logger(__name__)

# Create FastAPI app (with docs enabled)
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESC,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# -------------------------------------------------------------------
# CORS (defaults for Streamlit localhost; override via env)
# -------------------------------------------------------------------
origins_env = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501"
)
origins = [o.strip() for o in origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Routers
#   - health: always open
#   - meetings/slides: require auth only in production
# -------------------------------------------------------------------
app.include_router(health_router)

if APP_ENV in ("prod", "production"):
    # Enforce auth in prod
    app.include_router(meetings_router, dependencies=[Depends(demo_auth_dependency)])
    app.include_router(slides_router,   dependencies=[Depends(demo_auth_dependency)])
else:
    # In dev/demo/local: skip auth to simplify testing
    app.include_router(meetings_router)
    app.include_router(slides_router)

# -------------------------------------------------------------------
# Error handlers (standardized JSON errors)
# -------------------------------------------------------------------
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

log.info(
    "API started",
    extra={"env": APP_ENV, "version": API_VERSION}
)

