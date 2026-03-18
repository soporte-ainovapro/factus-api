from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr

from app.domain.exceptions import FactusAPIError
from app.domain.models.invoice import Invoice
from app.domain.models.results import (
    InvoiceResult, DownloadResult, InvoiceDataResult,
    DeleteInvoiceResult, InvoiceEventsResult, InvoiceEvent,
)
from app.domain.interfaces.invoice_gateway import IInvoiceGateway, SendEmailRequest
from app.api.deps import verify_api_key, get_invoice_gateway

router = APIRouter()


# ── Request schemas (API layer) ──────────────────────────────────────────────

class SendEmailRequestSchema(BaseModel):
    email: EmailStr
    pdf_base_64_encoded: Optional[str] = None


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=InvoiceResult)
async def create_invoice(
    invoice: Invoice,
    x_factus_token: str = Header(...),
    gateway: IInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key),
):
    try:
        return await gateway.create_invoice(invoice, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/pdf", response_model=DownloadResult)
async def get_pdf(
    number: str,
    x_factus_token: str = Header(...),
    gateway: IInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key),
):
    try:
        return await gateway.download_pdf(number, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/xml", response_model=DownloadResult)
async def get_xml(
    number: str,
    x_factus_token: str = Header(...),
    gateway: IInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key),
):
    try:
        return await gateway.download_xml(number, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/events", response_model=List[InvoiceEvent])
async def get_invoice_events(
    number: str,
    x_factus_token: str = Header(...),
    gateway: IInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key),
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
    gateway: IInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key),
):
    try:
        resp = await gateway.get_invoice(number, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/reference/{reference_code}", response_model=DeleteInvoiceResult)
async def delete_invoice(
    reference_code: str,
    x_factus_token: str = Header(...),
    gateway: IInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key),
):
    try:
        return await gateway.delete_invoice(reference_code, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/{number}/send-email")
async def send_email(
    number: str,
    body: SendEmailRequestSchema,
    x_factus_token: str = Header(...),
    gateway: IInvoiceGateway = Depends(get_invoice_gateway),
    _: str = Depends(verify_api_key),
):
    try:
        request = SendEmailRequest(
            email=str(body.email),
            pdf_base_64_encoded=body.pdf_base_64_encoded,
        )
        await gateway.send_email(number, request, x_factus_token)
        return {"status": "ok", "message": "Correo enviado correctamente"}
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
