from fastapi import APIRouter, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse

router = APIRouter(tags=["meta"])


@router.get("/openapi.json", include_in_schema=False)
def openapi_json(request: Request):
    return JSONResponse(request.app.openapi())


@router.get("/docs", include_in_schema=False)
def docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Docs")


@router.get("/redoc", include_in_schema=False)
def redoc():
    return get_redoc_html(openapi_url="/openapi.json", title="ReDoc")
