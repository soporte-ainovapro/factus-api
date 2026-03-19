from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File
from app.core.exceptions import FactusAPIError
from app.schemas.company import (
    CompanyData,
    CompanyUpdate,
    LogoData,
)
from app.services.factus_company_service import FactusCompanyService
from app.core.config import settings

from app.api.deps import verify_api_key

router = APIRouter()

def get_company_service() -> FactusCompanyService:
    return FactusCompanyService(base_url=settings.FACTUS_BASE_URL)

@router.get("/", response_model=CompanyData)
async def get_company(
    x_factus_token: str = Header(...),
    service: FactusCompanyService = Depends(get_company_service),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await service.get_company(x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/", response_model=CompanyData)
async def update_company(
    company: CompanyUpdate,
    x_factus_token: str = Header(...),
    service: FactusCompanyService = Depends(get_company_service),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await service.update_company(company, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/logo", response_model=LogoData)
async def update_company_logo(
    image: UploadFile = File(...),
    x_factus_token: str = Header(...),
    service: FactusCompanyService = Depends(get_company_service),
    _: str = Depends(verify_api_key)
):
    try:
        file_content = await image.read()
        resp = await service.update_company_logo(
            file_name=image.filename,
            file_content=file_content,
            file_content_type=image.content_type,
            token=x_factus_token
        )
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
