from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.invoices import router as invoice_router
from app.api.v1.endpoints.lookups import router as lookup_router
from app.api.v1.endpoints.company import router as company_router
from app.api.v1.endpoints.numbering_ranges import router as numbering_ranges_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(invoice_router, prefix="/invoices", tags=["invoices"])
router.include_router(lookup_router, prefix="/lookups", tags=["lookups"])
router.include_router(company_router, prefix="/company", tags=["company"])
router.include_router(numbering_ranges_router, prefix="/numbering-ranges", tags=["numbering-ranges"])

@router.get("/health")
async def health_check():
    return {"status": "ok"}
