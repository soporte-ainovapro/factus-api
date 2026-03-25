import httpx
import logging
from typing import Any, Dict, Optional

from app.core.exceptions import FactusAPIError
from app.schemas.invoice import Invoice
from app.schemas.shared import SendEmailRequest
from app.schemas.results import (
    DocumentResult,
    DownloadResult,
    DocumentDataResult,
    DeleteDocumentResult,
    DocumentEventsResult,
)
from app.services.providers.factus.factus_document_service import FactusBaseDocumentService
from app.services.providers.factus.factus_code_maps import (
    DOCUMENT_TYPE_TO_FACTUS_BILL_CODE,
    PAYMENT_FORM_TO_FACTUS_CODE,
    PAYMENT_METHOD_TO_FACTUS_CODE,
)

logger = logging.getLogger(__name__)

class FactusInvoiceService(FactusBaseDocumentService):

    # ── Payload mapping ──────────────────────────────────────────────────────

    async def _build_payload(
        self, invoice: Invoice, numbering_range_id: int, token: str
    ) -> Dict[str, Any]:
        """Construye el payload completo para la API de Factus a partir del modelo canónico."""
        raw_pm_code = (
            invoice.payment_method_code.strip() if invoice.payment_method_code else ""
        )
        pm_code = PAYMENT_METHOD_TO_FACTUS_CODE.get(raw_pm_code, raw_pm_code)

        payload: Dict[str, Any] = {
            "numbering_range_id": numbering_range_id,
            "document": DOCUMENT_TYPE_TO_FACTUS_BILL_CODE[invoice.document_type.value if hasattr(invoice.document_type, "value") else invoice.document_type],
            "reference_code": invoice.reference_code,
            "payment_form": PAYMENT_FORM_TO_FACTUS_CODE[invoice.payment_form.value if hasattr(invoice.payment_form, "value") else invoice.payment_form],
            "payment_method_code": pm_code,
        }

        if invoice.observation:
            payload["observation"] = invoice.observation
        if invoice.operation_type:
            payload["operation_type"] = invoice.operation_type
        if invoice.send_email is not None:
            payload["send_email"] = invoice.send_email
        if invoice.payment_due_date:
            payload["payment_due_date"] = invoice.payment_due_date.isoformat()

        if invoice.order_reference:
            payload["order_reference"] = {
                "reference_code": invoice.order_reference.reference_code
            }
            if invoice.order_reference.issue_date:
                payload["order_reference"]["issue_date"] = invoice.order_reference.issue_date.isoformat()

        if invoice.related_documents:
            payload["related_documents"] = [
                {
                    "code": doc.code,
                    "issue_date": doc.issue_date.isoformat(),
                    "number": doc.number,
                }
                for doc in invoice.related_documents
            ]

        if invoice.billing_period:
            bp = invoice.billing_period
            payload["billing_period"] = {
                "start_date": bp.start_date.isoformat(),
                "end_date": bp.end_date.isoformat(),
                "end_time": bp.end_time,
            }
            if bp.start_time:
                payload["billing_period"]["start_time"] = bp.start_time

        if invoice.establishment:
            payload["establishment"] = invoice.establishment.model_dump()

        if invoice.allowance_charges:
            payload["allowance_charges"] = [
                {
                    "concept_type": ac.concept_type,
                    "is_surcharge": ac.is_surcharge,
                    "reason": ac.reason,
                    "base_amount": str(ac.base_amount),
                    "amount": str(ac.amount),
                }
                for ac in invoice.allowance_charges
            ]

        payload["customer"] = await self._map_customer(invoice, token)
        payload["items"] = self._map_items(invoice)

        return payload

    # ── Gateway methods ──────────────────────────────────────────────────────

    async def create_invoice(self, invoice: Invoice, token: str) -> DocumentResult:
        numbering_range_id = await self._resolve_numbering_range_id(
            invoice.numbering_range_prefix, token
        )
        payload = await self._build_payload(invoice, numbering_range_id, token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/bills/validate",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )

        if not response.is_success:
            logger.error(
                "Factus create_invoice failed — status=%s body=%s prefix=%s",
                response.status_code,
                response.text,
                invoice.numbering_range_prefix,
            )
            raise FactusAPIError(
                self._parse_error(response, "Error al validar la factura"),
                status_code=self._status_code(response),
            )

        response_json = response.json()
        data = response_json.get("data", {})
        bill = data.get("bill", {})
        numbering_range = data.get("numbering_range", {})

        return DocumentResult(
            id=str(bill.get("id")) if bill.get("id") else None,
            number=bill.get("number", ""),
            prefix=numbering_range.get("prefix", invoice.numbering_range_prefix),
            cufe=bill.get("cufe", ""),
            qr_url=bill.get("qr", ""),
            status=str(bill.get("status", "1")),
            message=response_json.get("message", "Success"),
        )

    async def download_pdf(self, number: str, token: str) -> DownloadResult:
        return await self._download("v1/bills/download-pdf", number, token, "pdf")

    async def download_xml(self, number: str, token: str) -> DownloadResult:
        return await self._download("v1/bills/download-xml", number, token, "xml")

    async def get_invoices(self, token: str, filters: Optional[Dict[str, Any]] = None) -> DocumentDataResult:
        return await self._get_documents("v1/bills", token, "Error al obtener las facturas", filters)

    async def get_invoice(self, number: str, token: str) -> DocumentDataResult:
        return await self._get_document(f"v1/bills/show/{number}", token, "Error al obtener la factura")

    async def delete_invoice(self, reference_code: str, token: str) -> DeleteDocumentResult:
        return await self._delete_document(f"v1/bills/destroy/reference/{reference_code}", token, "Error al eliminar la factura")

    async def send_email(self, number: str, request: SendEmailRequest, token: str) -> None:
        await self._send_email(f"v1/bills/send-email/{number}", request, token, "Error al enviar el correo")

    async def get_email_content(self, number: str, token: str) -> DocumentDataResult:
        return await self._get_document(f"v1/bills/{number}/email-content", token, "Error al obtener contenido de correo")

    async def register_implicit_acceptance(self, number: str, event_data: dict, token: str) -> DocumentDataResult:
        event_type = "034"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/bills/radian/events/update/{number}/{event_type}",
                json=event_data,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al registrar la aceptación tácita"),
                status_code=self._status_code(response),
            )

        return DocumentDataResult(**response.json())

    async def get_invoice_events(self, number: str, token: str) -> DocumentEventsResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/bills/{number}/radian/events",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al obtener eventos de la factura"),
                status_code=self._status_code(response),
            )

        return DocumentEventsResult(**response.json())
