from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.src.api.v1.schemas.auth import LoginRequest, RefreshTokenRequest
from app.src.core.responses import ApiResponse
from app.src.domain.models.auth_token import AuthToken
from app.src.domain.models.user import User, Token
from app.src.infrastructure.gateways.factus_auth_gateway import FactusAuthGateway
from app.src.core.config import settings
from app.src.core.security import create_access_token
from app.src.api.deps import get_current_user

router = APIRouter()

def get_auth_gateway() -> FactusAuthGateway:
    return FactusAuthGateway(
        base_url=settings.FACTUS_BASE_URL,
        client_id=settings.FACTUS_CLIENT_ID,
        client_secret=settings.FACTUS_CLIENT_SECRET
    )

@router.post("/login", response_model=Token)
async def login_local(form_data: OAuth2PasswordRequestForm = Depends()):
    # Mock authentication - admin:admin123
    if form_data.username != "admin" or form_data.password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/factus/login", response_model=ApiResponse[AuthToken])
async def login_factus(
    request: LoginRequest,
    gateway: FactusAuthGateway = Depends(get_auth_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.authenticate(request.email, request.password)
        return ApiResponse(message="Autenticación exitosa", data=data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo obtener el token de Factus: {str(e)}"
        )

@router.post("/factus/refresh", response_model=ApiResponse[AuthToken])
async def refresh_factus_token(
    request: RefreshTokenRequest,
    gateway: FactusAuthGateway = Depends(get_auth_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.refresh_token(request.refresh_token)
        return ApiResponse(message="Token refrescado exitosamente", data=data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo refrescar el token de Factus: {str(e)}"
        )
