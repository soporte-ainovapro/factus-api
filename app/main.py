import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.limiter import limiter

logging.basicConfig(level=logging.INFO)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Check if the error is likely due to passing a stringified JSON body
    for error in errors:
        err_type = error.get("type", "")
        if err_type in ("model_type", "model_attributes_type", "json_invalid"):
            input_val = error.get("input")
            
            # Handle both string and bytes input (FastAPI might pass raw bytes)
            if isinstance(input_val, bytes):
                try:
                    input_val = input_val.decode("utf-8")
                except UnicodeDecodeError:
                    input_val = ""
                    
            if isinstance(input_val, str) and (input_val.strip().startswith("{") or '\\"' in input_val):
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "detail": "Error de validación: Parece que se ha enviado una cadena (string) "
                                  "en lugar de un objeto JSON válido. Si usas Postman, asegúrate de que el 'Body' "
                                  "esté configurado como 'raw' y el formato sea 'JSON'."
                    },
                )
    
    # Default behavior for other validation errors
    # Use jsonable_encoder to safely serialize objects like bytes
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(errors)},
    )

def create_app() -> FastAPI:
    docs_url = f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else None
    redoc_url = f"{settings.API_V1_STR}/redoc" if settings.ENVIRONMENT != "production" else None

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=docs_url,
        redoc_url=redoc_url,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get("/")
    async def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{settings.API_V1_STR}/docs")

    return app

app = create_app()
