from fastapi import APIRouter
from app.src.api.v1.endpoints.auth import router as auth_router
from app.src.api.v1.endpoints.invoices import router as invoice_router
from app.src.api.v1.endpoints.lookups import router as lookup_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(invoice_router, prefix="/invoices", tags=["invoices"])
router.include_router(lookup_router, prefix="/lookups", tags=["lookups"])

@router.get("/health")
async def health_check():
    return {"status": "ok"}
