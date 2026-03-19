"""
Dependency injection for the factus-api endpoints.

Authentication uses a shared API Key (X-API-Key header) instead of
a local username/password JWT. The key is configured via the
FACTUS_INTERNAL_API_KEY environment variable and must match the value
configured in backend-app-baiji.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.services.interfaces import (
    InvoiceService,
    AuthService,
    LookupService,
    NumberingRangeService,
    CompanyService,
)

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


def get_invoice_service() -> InvoiceService:
    """
    Retorna el gateway de facturación según el proveedor configurado.
    Añadir nuevos proveedores aquí es el único cambio necesario para soportarlos.
    """
    if settings.BILLING_PROVIDER == "factus":
        from app.services.providers.factus.factus_invoice_service import (
            FactusInvoiceService,
        )

        return FactusInvoiceService(base_url=settings.FACTUS_BASE_URL)

    raise ValueError(
        f"Proveedor de facturación no soportado: '{settings.BILLING_PROVIDER}'. "
        "Valores válidos: 'factus'"
    )


def get_auth_service() -> AuthService:
    if settings.BILLING_PROVIDER == "factus":
        from app.services.providers.factus.factus_auth_service import FactusAuthService

        return FactusAuthService(
            base_url=settings.FACTUS_BASE_URL,
            client_id=settings.FACTUS_CLIENT_ID,
            client_secret=settings.FACTUS_CLIENT_SECRET,
        )
    raise ValueError(f"Proveedor no soportado: {settings.BILLING_PROVIDER}")


def get_lookup_service() -> LookupService:
    if settings.BILLING_PROVIDER == "factus":
        from app.services.providers.factus.factus_lookup_service import (
            FactusLookupService,
        )

        return FactusLookupService(base_url=settings.FACTUS_BASE_URL)
    raise ValueError(f"Proveedor no soportado: {settings.BILLING_PROVIDER}")


def get_numbering_range_service() -> NumberingRangeService:
    if settings.BILLING_PROVIDER == "factus":
        from app.services.providers.factus.factus_numbering_range_service import (
            FactusNumberingRangeService,
        )

        return FactusNumberingRangeService(base_url=settings.FACTUS_BASE_URL)
    raise ValueError(f"Proveedor no soportado: {settings.BILLING_PROVIDER}")


def get_company_service() -> CompanyService:
    if settings.BILLING_PROVIDER == "factus":
        from app.services.providers.factus.factus_company_service import (
            FactusCompanyService,
        )

        return FactusCompanyService(base_url=settings.FACTUS_BASE_URL)
    raise ValueError(f"Proveedor no soportado: {settings.BILLING_PROVIDER}")
