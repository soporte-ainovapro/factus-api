"""
Dependency injection for the factus-api endpoints.

Authentication uses a shared API Key (X-API-Key header) instead of
a local username/password JWT. The key is configured via the
FACTUS_INTERNAL_API_KEY environment variable and must match the value
configured in backend-app-baiji.
"""
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.src.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validates the X-API-Key header against the configured secret.
    Returns the key on success; raises 403 on failure.
    """
    if api_key != settings.FACTUS_INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida o ausente.",
        )
    return api_key
