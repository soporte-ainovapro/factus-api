from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel, EmailStr

from app.core.exceptions import FactusAPIError
from app.schemas.invoice import Invoice
from app.schemas.results import (
    DocumentResult,
    DownloadResult,
    DocumentDataResult,
    DeleteDocumentResult,
    DocumentEventsResult,
    DocumentEvent,
)
from app.schemas.invoice import ImplicitAcceptanceEvent
from app.schemas.shared import SendEmailRequest
from app.services.interfaces import InvoiceService
from app.api.deps import get_factus_token, verify_api_key, get_invoice_service

router = APIRouter()

# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("/", response_model=DocumentResult)
async def create_invoice(
    invoice: Invoice,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        return await service.create_invoice(invoice, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/", response_model=DocumentDataResult)
async def get_invoices(
    x_factus_token: str = Depends(get_factus_token),
    filter_number: Optional[str] = Query(None, alias="filter[number]"),
    filter_reference_code: Optional[str] = Query(None, alias="filter[reference_code]"),
    filter_identification: Optional[str] = Query(None, alias="filter[identification]"),
    filter_names: Optional[str] = Query(None, alias="filter[names]"),
    page: Optional[int] = Query(None),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        filters: Dict[str, Any] = {}
        if filter_number:
            filters["number"] = filter_number
        if filter_reference_code:
            filters["reference_code"] = filter_reference_code
        if filter_identification:
            filters["identification"] = filter_identification
        if filter_names:
            filters["names"] = filter_names
        if page:
            filters["page"] = page

        return await service.get_invoices(x_factus_token, filters)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/pdf", response_model=DownloadResult)
async def get_pdf(
    number: str,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        return await service.download_pdf(number, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/xml", response_model=DownloadResult)
async def get_xml(
    number: str,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        return await service.download_xml(number, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/events", response_model=List[DocumentEvent])
async def get_invoice_events(
    number: str,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        resp = await service.get_invoice_events(number, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}", response_model=Dict[str, Any])
async def get_invoice(
    number: str,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        resp = await service.get_invoice(number, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/reference/{reference_code}", response_model=DeleteDocumentResult)
async def delete_invoice(
    reference_code: str,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        return await service.delete_invoice(reference_code, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/{number}/send-email")
async def send_email(
    number: str,
    request: SendEmailRequest,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        await service.send_email(number, request, x_factus_token)
        return {"status": "ok", "message": "Correo enviado correctamente"}
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/email-content", response_model=Dict[str, Any])
async def get_email_content(
    number: str,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        resp = await service.get_email_content(number, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/{number}/implicit-acceptance", response_model=Dict[str, Any])
async def register_implicit_acceptance(
    number: str,
    event_data: ImplicitAcceptanceEvent,
    x_factus_token: str = Depends(get_factus_token),
    service: InvoiceService = Depends(get_invoice_service),
    _: str = Depends(verify_api_key),
):
    try:
        resp = await service.register_implicit_acceptance(number, event_data.model_dump(), x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

