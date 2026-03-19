"""
Auth endpoints for factus-api.

- POST /factus/login  → Authenticate against Factus using the API Key.
- POST /factus/refresh → Refresh an existing Factus token.

The /login (local mock) endpoint has been removed. All callers
must authenticate using the shared X-API-Key header instead.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.auth import LoginRequest, RefreshTokenRequest
from app.core.exceptions import FactusAPIError
from app.schemas.auth_token import AuthToken
from app.services.factus_auth_service import FactusAuthService
from app.core.config import settings
from app.api.deps import verify_api_key

router = APIRouter()


def get_auth_service() -> FactusAuthService:
    return FactusAuthService(
        base_url=settings.FACTUS_BASE_URL,
        client_id=settings.FACTUS_CLIENT_ID,
        client_secret=settings.FACTUS_CLIENT_SECRET,
    )


@router.post("/factus/login", response_model=AuthToken)
async def login_factus(
    request: LoginRequest,
    service: FactusAuthService = Depends(get_auth_service),
    _: str = Depends(verify_api_key),
):
    """
    Autentica contra la API de Factus usando las credenciales proporcionadas.
    Requiere la cabecera X-API-Key con la clave interna de la plataforma.
    """
    try:
        data = await service.authenticate(request.email, request.password)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/factus/refresh", response_model=AuthToken)
async def refresh_factus_token(
    request: RefreshTokenRequest,
    service: FactusAuthService = Depends(get_auth_service),
    _: str = Depends(verify_api_key),
):
    """
    Refresca el token de acceso de Factus usando el refresh_token.
    Requiere la cabecera X-API-Key con la clave interna de la plataforma.
    """
    try:
        data = await service.refresh_token(request.refresh_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
