from abc import ABC, abstractmethod
from app.domain.models.invoice import Invoice
from app.api.v1.schemas.invoice import InvoiceResponse, DownloadResponse, InvoiceDataResponse, DeleteInvoiceResponse, SendEmailRequest, SendEmailResponse, InvoiceEventsResponse

class IInvoiceGateway(ABC):
    @abstractmethod
    async def create_invoice(self, invoice: Invoice, token: str) -> InvoiceResponse:
        """
        Sends an invoice to the external API (Factus) and returns the validation response.
        """
        pass

    @abstractmethod
    async def download_pdf(self, number: str, token: str) -> DownloadResponse:
        """
        Downloads the PDF of an invoice.
        """
        pass

    @abstractmethod
    async def download_xml(self, number: str, token: str) -> DownloadResponse:
        """
        Downloads the XML of an invoice.
        """
        pass

    @abstractmethod
    async def get_invoice(self, number: str, token: str) -> InvoiceDataResponse:
        """
        Gets the full data of an invoice by its number.
        """
        pass

    @abstractmethod
    async def delete_invoice(self, reference_code: str, token: str) -> DeleteInvoiceResponse:
        """
        Deletes an unvalidated invoice by its reference code.
        """
        pass

    @abstractmethod
    async def send_email(self, number: str, request: SendEmailRequest, token: str) -> SendEmailResponse:
        """
        Sends the invoice by email to the specified recipient.
        """
        pass

    @abstractmethod
    async def get_invoice_events(self, number: str, token: str) -> InvoiceEventsResponse:
        """
        Gets the Radian events associated with an invoice by its number.
        """
        pass
