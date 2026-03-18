from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models.invoice import Invoice
from app.domain.models.results import (
    InvoiceResult, DownloadResult, InvoiceDataResult,
    DeleteInvoiceResult, InvoiceEventsResult
)


class SendEmailRequest:
    """Solicitud para enviar factura por email (sin dependencia de FastAPI schemas)."""
    def __init__(self, email: str, pdf_base_64_encoded: Optional[str] = None):
        self.email = email
        self.pdf_base_64_encoded = pdf_base_64_encoded


class IInvoiceGateway(ABC):

    @abstractmethod
    async def create_invoice(self, invoice: Invoice, token: str) -> InvoiceResult:
        """Envía una factura a la API del proveedor y retorna el resultado de validación."""
        pass

    @abstractmethod
    async def download_pdf(self, number: str, token: str) -> DownloadResult:
        """Descarga el PDF de una factura."""
        pass

    @abstractmethod
    async def download_xml(self, number: str, token: str) -> DownloadResult:
        """Descarga el XML de una factura."""
        pass

    @abstractmethod
    async def get_invoice(self, number: str, token: str) -> InvoiceDataResult:
        """Obtiene los datos completos de una factura."""
        pass

    @abstractmethod
    async def delete_invoice(self, reference_code: str, token: str) -> DeleteInvoiceResult:
        """Elimina una factura no validada."""
        pass

    @abstractmethod
    async def send_email(self, number: str, request: SendEmailRequest, token: str) -> None:
        """Envía la factura por correo al destinatario."""
        pass

    @abstractmethod
    async def get_invoice_events(self, number: str, token: str) -> InvoiceEventsResult:
        """Obtiene los eventos RADIAN asociados a una factura."""
        pass
