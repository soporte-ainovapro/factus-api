from fastapi import APIRouter, Depends, Header, HTTPException
from typing import List
from app.src.core.responses import ApiResponse
from app.src.domain.models.lookup import (
    Municipality,
    Tax,
    Unit,
    NumberingRange
)
from app.src.infrastructure.gateways.factus_lookup_gateway import FactusLookupGateway
from app.src.core.config import settings

from app.src.domain.models.user import User
from app.src.api.deps import get_current_user

router = APIRouter()

def get_lookup_gateway() -> FactusLookupGateway:
    return FactusLookupGateway(base_url=settings.FACTUS_BASE_URL)

@router.get("/municipalities", response_model=ApiResponse[List[Municipality]])
async def get_municipalities(
    x_factus_token: str = Header(...),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_municipalities(x_factus_token)
        return ApiResponse(message="Municipios obtenidos exitosamente", data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/taxes", response_model=ApiResponse[List[Tax]])
async def get_taxes(
    x_factus_token: str = Header(...),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_tax_types(x_factus_token)
        return ApiResponse(message="Tipos de impuesto obtenidos exitosamente", data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/units", response_model=ApiResponse[List[Unit]])
async def get_units(
    x_factus_token: str = Header(...),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_units(x_factus_token)
        return ApiResponse(message="Unidades obtenidas exitosamente", data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/numbering-ranges", response_model=ApiResponse[List[NumberingRange]])
async def get_numbering_ranges(
    x_factus_token: str = Header(...),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_numbering_ranges(x_factus_token)
        return ApiResponse(message="Rangos de numeración obtenidos exitosamente", data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
