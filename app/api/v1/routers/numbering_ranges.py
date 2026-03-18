from fastapi import APIRouter, HTTPException, Depends, Header, Query
from typing import Optional, List
from app.domain.exceptions import FactusAPIError
from app.domain.models.numbering_range import (
    NumberingRange,
    NumberingRangeSoftware,
    NumberingRangeResponse,
    NumberingRangeListResponse,
    NumberingRangeCreate,
    NumberingRangeUpdate,
    NumberingRangeDeleteResponse,
    NumberingRangeSoftwareResponse,
)
from app.infrastructure.gateways.factus_numbering_range_gateway import FactusNumberingRangeGateway
from app.core.config import settings

from app.api.deps import verify_api_key

router = APIRouter()

def get_numbering_range_gateway() -> FactusNumberingRangeGateway:
    return FactusNumberingRangeGateway(base_url=settings.FACTUS_BASE_URL)

@router.get("/", response_model=List[NumberingRange])
async def get_numbering_ranges(
    x_factus_token: str = Header(...),
    id: Optional[int] = Query(None, description="Filtrar por id"),
    document: Optional[str] = Query(None, description="Filtrar por documento"),
    resolution_number: Optional[str] = Query(None, description="Filtrar por número de resolución"),
    technical_key: Optional[str] = Query(None, description="Filtrar por clave técnica"),
    is_active: Optional[int] = Query(None, description="Filtrar por estado activo (1 o 0)"),
    gateway: FactusNumberingRangeGateway = Depends(get_numbering_range_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        filters = {
            "id": id,
            "document": document,
            "resolution_number": resolution_number,
            "technical_key": technical_key,
            "is_active": is_active
        }
        resp = await gateway.get_numbering_ranges(x_factus_token, filters=filters)
        return resp.data if resp.data else []
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/software", response_model=List[NumberingRangeSoftware])
async def get_software_numbering_ranges(
    x_factus_token: str = Header(...),
    gateway: FactusNumberingRangeGateway = Depends(get_numbering_range_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.get_software_numbering_ranges(x_factus_token)
        return resp.data if resp.data else []
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{id}", response_model=NumberingRange)
async def get_numbering_range(
    id: int,
    x_factus_token: str = Header(...),
    gateway: FactusNumberingRangeGateway = Depends(get_numbering_range_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.get_numbering_range(id, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/", response_model=NumberingRange)
async def create_numbering_range(
    range_data: NumberingRangeCreate,
    x_factus_token: str = Header(...),
    gateway: FactusNumberingRangeGateway = Depends(get_numbering_range_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.create_numbering_range(range_data, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/{id}", response_model=NumberingRange)
async def update_numbering_range_consecutive(
    id: int,
    update_data: NumberingRangeUpdate,
    x_factus_token: str = Header(...),
    gateway: FactusNumberingRangeGateway = Depends(get_numbering_range_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.update_numbering_range_consecutive(id, update_data, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/{id}", response_model=dict)
async def delete_numbering_range(
    id: int,
    x_factus_token: str = Header(...),
    gateway: FactusNumberingRangeGateway = Depends(get_numbering_range_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.delete_numbering_range(id, x_factus_token)
        return {"status": resp.status}
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
