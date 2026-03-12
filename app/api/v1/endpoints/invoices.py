from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Header
from app.domain.exceptions import FactusAPIError
from app.domain.models.invoice import Invoice
from app.api.v1.schemas.invoice import (
    InvoiceResponse,
    DownloadResponse,
    InvoiceDataResponse,
    DeleteInvoiceResponse,
    SendEmailRequest,
    SendEmailResponse,
    InvoiceEventsResponse,
    InvoiceEvent,
)
from app.infrastructure.gateways.factus_invoice_gateway import FactusInvoiceGateway
from app.core.config import settings

from app.api.deps import verify_api_key

router = APIRouter()

def get_invoice_gateway() -> FactusInvoiceGateway:
    return FactusInvoiceGateway(base_url=settings.FACTUS_BASE_URL)

@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    invoice: Invoice,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.create_invoice(invoice, x_factus_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{number}/pdf", response_model=DownloadResponse)
async def get_pdf(
    number: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.download_pdf(number, x_factus_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{number}/xml", response_model=DownloadResponse)
async def get_xml(
    number: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.download_xml(number, x_factus_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{number}/events", response_model=List[InvoiceEvent])
async def get_invoice_events(
    number: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.get_invoice_events(number, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{number}", response_model=Dict[str, Any])
async def get_invoice(
    number: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.get_invoice(number, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/reference/{reference_code}", response_model=DeleteInvoiceResponse)
async def delete_invoice(
    reference_code: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.delete_invoice(reference_code, x_factus_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/{number}/send-email", response_model=SendEmailResponse)
async def send_email(
    number: str,
    body: SendEmailRequest,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.send_email(number, body, x_factus_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
