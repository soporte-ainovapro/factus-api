"""
Modelos de resultado de dominio para operaciones de facturación.

Estos modelos representan las respuestas de las operaciones de facturación
en términos del negocio, sin depender de ningún proveedor específico.
Los adaptadores de los proveedores mapean sus respuestas a estos modelos.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class DocumentResult(BaseModel):
    """Resultado de emitir una factura electrónica u otro documento."""

    id: Optional[str] = None
    number: str
    prefix: str
    cufe: str
    qr_url: str
    status: str
    message: Optional[str] = None


class DownloadResult(BaseModel):
    """Resultado de descargar un documento (PDF o XML)."""

    file_name: str
    file_content: str  # Contenido en Base64
    extension: str  # "pdf" o "xml"


class DocumentDataResult(BaseModel):
    """Datos completos de una factura consultada."""

    status: str
    message: Optional[str] = None
    data: Dict[str, Any]


class DeleteDocumentResult(BaseModel):
    """Resultado de eliminar una factura no validada."""

    status: str
    message: str


class DocumentEvent(BaseModel):
    """Evento RADIAN asociado a una factura."""

    number: str
    cude: str
    event_code: str
    event_name: str
    effective_date: str
    effective_time: str


class DocumentEventsResult(BaseModel):
    """Lista de eventos RADIAN de una factura."""

    status: str
    message: Optional[str] = None
    data: List[DocumentEvent]
