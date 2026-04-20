from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr

from app.core.exceptions import FactusAPIError
from app.schemas.credit_note import CreditNote
from app.schemas.results import (
    DocumentResult,
    DownloadResult,
    DocumentDataResult,
    DeleteDocumentResult,
)
from app.schemas.shared import SendEmailRequest
from app.services.interfaces import CreditNoteService
from app.api.deps import get_factus_token, verify_api_key, get_credit_note_service

router = APIRouter()

@router.post("/", response_model=DocumentResult)
async def create_credit_note(
    credit_note: CreditNote,
    x_factus_token: str = Depends(get_factus_token),
    service: CreditNoteService = Depends(get_credit_note_service),
    _: str = Depends(verify_api_key),
):
    try:
        return await service.create_credit_note(credit_note, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/", response_model=DocumentDataResult)
async def get_credit_notes(
    identification: Optional[str] = None,
    names: Optional[str] = None,
    number: Optional[str] = None,
    prefix: Optional[str] = None,
    reference_code: Optional[str] = None,
    status: Optional[int] = None,
    x_factus_token: str = Depends(get_factus_token),
    service: CreditNoteService = Depends(get_credit_note_service),
    _: str = Depends(verify_api_key),
):
    try:
        filters = {
            "identification": identification,
            "names": names,
            "number": number,
            "prefix": prefix,
            "reference_code": reference_code,
            "status": status,
        }
        return await service.get_credit_notes(x_factus_token, filters)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}", response_model=Dict[str, Any])
async def get_credit_note(
    number: str,
    x_factus_token: str = Depends(get_factus_token),
    service: CreditNoteService = Depends(get_credit_note_service),
    _: str = Depends(verify_api_key),
):
    try:
        resp = await service.get_credit_note(number, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/pdf", response_model=DownloadResult)
async def get_pdf(
    number: str,
    x_factus_token: str = Depends(get_factus_token),
    service: CreditNoteService = Depends(get_credit_note_service),
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
    service: CreditNoteService = Depends(get_credit_note_service),
    _: str = Depends(verify_api_key),
):
    try:
        return await service.download_xml(number, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{number}/email-content", response_model=Dict[str, Any])
async def get_email_content(
    number: str,
    x_factus_token: str = Depends(get_factus_token),
    service: CreditNoteService = Depends(get_credit_note_service),
    _: str = Depends(verify_api_key),
):
    try:
        resp = await service.get_email_content(number, x_factus_token)
        return resp.data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/{number}/send-email")
async def send_email(
    number: str,
    request: SendEmailRequest,
    x_factus_token: str = Depends(get_factus_token),
    service: CreditNoteService = Depends(get_credit_note_service),
    _: str = Depends(verify_api_key),
):
    try:
        await service.send_email(number, request, x_factus_token)
        return {"status": "ok", "message": "Correo enviado correctamente"}
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/reference/{reference_code}", response_model=DeleteDocumentResult)
async def delete_credit_note(
    reference_code: str,
    x_factus_token: str = Depends(get_factus_token),
    service: CreditNoteService = Depends(get_credit_note_service),
    _: str = Depends(verify_api_key),
):
    try:
        return await service.delete_credit_note(reference_code, x_factus_token)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
