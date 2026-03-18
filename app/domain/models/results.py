"""
Modelos de resultado de dominio para operaciones de facturación.

Estos modelos representan las respuestas de las operaciones de facturación
en términos del negocio, sin depender de ningún proveedor específico.
Los adaptadores de los proveedores mapean sus respuestas a estos modelos.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


class InvoiceResult(BaseModel):
    """Resultado de emitir una factura electrónica."""
    number: str
    prefix: str
    cufe: str
    qr_url: str
    status: str
    message: Optional[str] = None


class DownloadResult(BaseModel):
    """Resultado de descargar un documento (PDF o XML)."""
    file_name: str
    file_content: str   # Contenido en Base64
    extension: str      # "pdf" o "xml"


class InvoiceDataResult(BaseModel):
    """Datos completos de una factura consultada."""
    status: str
    message: Optional[str] = None
    data: Dict[str, Any]


class DeleteInvoiceResult(BaseModel):
    """Resultado de eliminar una factura no validada."""
    status: str
    message: str


class SendEmailResult(BaseModel):
    """Resultado de enviar una factura por correo."""
    status: str
    message: str


class InvoiceEvent(BaseModel):
    """Evento RADIAN asociado a una factura."""
    number: str
    cude: str
    event_code: str
    event_name: str
    effective_date: str
    effective_time: str


class InvoiceEventsResult(BaseModel):
    """Lista de eventos RADIAN de una factura."""
    status: str
    message: Optional[str] = None
    data: List[InvoiceEvent]
