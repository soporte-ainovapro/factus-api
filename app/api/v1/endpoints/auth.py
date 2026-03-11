"""
Auth endpoints for factus-api.

- POST /factus/login  → Authenticate against Factus using the API Key.
- POST /factus/refresh → Refresh an existing Factus token.

The /login (local mock) endpoint has been removed. All callers
must authenticate using the shared X-API-Key header instead.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.api.v1.schemas.auth import LoginRequest, RefreshTokenRequest
from app.core.responses import ApiResponse
from app.domain.exceptions import FactusAPIError
from app.domain.models.auth_token import AuthToken
from app.infrastructure.gateways.factus_auth_gateway import FactusAuthGateway
from app.core.config import settings
from app.api.deps import verify_api_key

router = APIRouter()


def get_auth_gateway() -> FactusAuthGateway:
    return FactusAuthGateway(
        base_url=settings.FACTUS_BASE_URL,
        client_id=settings.FACTUS_CLIENT_ID,
        client_secret=settings.FACTUS_CLIENT_SECRET,
    )


@router.post("/factus/login", response_model=ApiResponse[AuthToken])
async def login_factus(
    request: LoginRequest,
    gateway: FactusAuthGateway = Depends(get_auth_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Autentica contra la API de Factus usando las credenciales proporcionadas.
    Requiere la cabecera X-API-Key con la clave interna de la plataforma.
    """
    try:
        data = await gateway.authenticate(request.email, request.password)
        return ApiResponse(message="Autenticación exitosa", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/factus/refresh", response_model=ApiResponse[AuthToken])
async def refresh_factus_token(
    request: RefreshTokenRequest,
    gateway: FactusAuthGateway = Depends(get_auth_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Refresca el token de acceso de Factus usando el refresh_token.
    Requiere la cabecera X-API-Key con la clave interna de la plataforma.
    """
    try:
        data = await gateway.refresh_token(request.refresh_token)
        return ApiResponse(message="Token refrescado exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
