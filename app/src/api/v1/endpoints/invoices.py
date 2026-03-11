from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Header
from app.src.core.responses import ApiResponse
from app.src.domain.exceptions import FactusAPIError
from app.src.domain.models.invoice import (
    Invoice,
    InvoiceResponse,
    DownloadResponse,
    InvoiceDataResponse,
    DeleteInvoiceResponse,
    SendEmailRequest,
    SendEmailResponse,
    InvoiceEventsResponse,
    InvoiceEvent,
)
from app.src.infrastructure.gateways.factus_invoice_gateway import FactusInvoiceGateway
from app.src.core.config import settings

from app.src.api.deps import verify_api_key

router = APIRouter()

def get_invoice_gateway() -> FactusInvoiceGateway:
    return FactusInvoiceGateway(base_url=settings.FACTUS_BASE_URL)

@router.post("/", response_model=ApiResponse[InvoiceResponse])
async def create_invoice(
    invoice: Invoice,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.create_invoice(invoice, x_factus_token)
        return ApiResponse(message="Factura creada exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{number}/pdf", response_model=ApiResponse[DownloadResponse])
async def get_pdf(
    number: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.download_pdf(number, x_factus_token)
        return ApiResponse(message="PDF obtenido exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{number}/xml", response_model=ApiResponse[DownloadResponse])
async def get_xml(
    number: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.download_xml(number, x_factus_token)
        return ApiResponse(message="XML obtenido exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{number}/events", response_model=ApiResponse[List[InvoiceEvent]])
async def get_invoice_events(
    number: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.get_invoice_events(number, x_factus_token)
        return ApiResponse(message="Eventos de factura obtenidos exitosamente", data=resp.data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{number}", response_model=ApiResponse[Dict[str, Any]])
async def get_invoice(
    number: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        resp = await gateway.get_invoice(number, x_factus_token)
        return ApiResponse(message="Factura obtenida exitosamente", data=resp.data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/reference/{reference_code}", response_model=ApiResponse[DeleteInvoiceResponse])
async def delete_invoice(
    reference_code: str,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.delete_invoice(reference_code, x_factus_token)
        return ApiResponse(message="Factura eliminada exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/{number}/send-email", response_model=ApiResponse[SendEmailResponse])
async def send_email(
    number: str,
    body: SendEmailRequest,
    x_factus_token: str = Header(...),
    gateway: FactusInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key)
):
    try:
        data = await gateway.send_email(number, body, x_factus_token)
        return ApiResponse(message="Correo enviado exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
