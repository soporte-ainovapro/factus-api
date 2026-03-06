import logging
from fastapi import FastAPI
from app.src.api.v1 import router as api_v1_router
from app.src.core.config import settings

logging.basicConfig(level=logging.INFO)

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get("/")
    async def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{settings.API_V1_STR}/docs")

    return app

app = create_app()
