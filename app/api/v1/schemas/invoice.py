from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

class InvoiceResponse(BaseModel):
    number: str
    prefix: str
    cufe: str
    qr_url: str
    status: str
    message: Optional[str] = None

class DownloadResponse(BaseModel):
    file_name: str
    file_content: str  # Base64
    extension: str

class InvoiceDataResponse(BaseModel):
    """
    Represents the full data of an invoice retrieved from Factus API.
    It can contain 'company', 'customer', 'bill', 'items', etc.
    """
    status: str
    message: Optional[str] = None
    data: Dict[str, Any]

class DeleteInvoiceResponse(BaseModel):
    status: str
    message: str

class SendEmailRequest(BaseModel):
    email: EmailStr
    pdf_base_64_encoded: Optional[str] = None

class SendEmailResponse(BaseModel):
    status: str
    message: str

class InvoiceEvent(BaseModel):
    number: str
    cude: str
    event_code: str
    event_name: str
    effective_date: str
    effective_time: str

class InvoiceEventsResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: List[InvoiceEvent]
