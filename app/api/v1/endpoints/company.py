from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File
from app.core.responses import ApiResponse
from app.domain.exceptions import FactusAPIError
from app.domain.models.company import (
    CompanyData,
    CompanyUpdate,
    LogoData,
)
from app.infrastructure.gateways.factus_company_gateway import FactusCompanyGateway
from app.core.config import settings

from app.api.deps import verify_api_key

router = APIRouter()

def get_company_gateway() -> FactusCompanyGateway:
    return FactusCompanyGateway(base_url=settings.FACTUS_BASE_URL)

@router.get("/", response_model=ApiResponse[CompanyData])
async def get_company(
    x_factus_token: str = Header(...),
    gateway: FactusCompanyGateway = Depends(get_company_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.get_company(x_factus_token)
        return ApiResponse(message="Empresa obtenida exitosamente", data=resp.data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/", response_model=ApiResponse[CompanyData])
async def update_company(
    company: CompanyUpdate,
    x_factus_token: str = Header(...),
    gateway: FactusCompanyGateway = Depends(get_company_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.update_company(company, x_factus_token)
        return ApiResponse(message="Empresa actualizada exitosamente", data=resp.data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/logo", response_model=ApiResponse[LogoData])
async def update_company_logo(
    image: UploadFile = File(...),
    x_factus_token: str = Header(...),
    gateway: FactusCompanyGateway = Depends(get_company_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        file_content = await image.read()
        resp = await gateway.update_company_logo(
            file_name=image.filename,
            file_content=file_content,
            file_content_type=image.content_type,
            token=x_factus_token
        )
        return ApiResponse(message="Logo de la empresa actualizado exitosamente", data=resp.data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
