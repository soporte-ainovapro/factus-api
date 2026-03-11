import httpx
import logging
from typing import Any, Dict
from app.domain.interfaces.invoice_gateway import IInvoiceGateway
from app.domain.exceptions import FactusAPIError

logger = logging.getLogger(__name__)
from app.domain.models.invoice import Invoice
from app.api.v1.schemas.invoice import (
    InvoiceResponse, DownloadResponse, InvoiceDataResponse,
    DeleteInvoiceResponse, SendEmailRequest, SendEmailResponse, InvoiceEventsResponse
)

class FactusInvoiceGateway(IInvoiceGateway):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _parse_error(self, response: httpx.Response, default: str) -> str:
        """
        Extract a human-readable error message from a Factus error response.

        Factus uses two different error shapes:
        - 422 Validation: {"message": "...", "data": {"errors": {"field": ["msg", ...]}}}
        - 409 Conflict:   {"status": "Conflict", "errors": [{"message": "...", ...}]}
        """
        try:
            data = response.json()
        except Exception:
            return response.text or f"HTTP {response.status_code}"

        top_message = data.get("message", "")

        def _fmt_dict_errors(d: dict) -> str:
            parts = []
            for field, msgs in d.items():
                if isinstance(msgs, list):
                    parts.append(f"{field}: {', '.join(msgs)}")
                else:
                    # msgs is a plain string (e.g. Factus FAK24 rule messages)
                    parts.append(str(msgs))
            return "; ".join(parts)

        # 422-style: errors nested under data.errors (dict of field -> str|[messages])
        nested_errors = data.get("data", {}).get("errors") if isinstance(data.get("data"), dict) else None
        if isinstance(nested_errors, dict) and nested_errors:
            field_errors = _fmt_dict_errors(nested_errors)
            return f"{top_message} — {field_errors}" if top_message else field_errors

        # 422-style: errors at top level (dict of field -> str|[messages])
        errors = data.get("errors")
        if isinstance(errors, dict) and errors:
            field_errors = _fmt_dict_errors(errors)
            return f"{top_message} — {field_errors}" if top_message else field_errors

        # 409-style: errors is a list of objects with a "message" key
        if isinstance(errors, list) and errors:
            messages = [e.get("message", "") for e in errors if isinstance(e, dict) and e.get("message")]
            if messages:
                return "; ".join(messages)

        return top_message or default

    def _status_code(self, response: httpx.Response) -> int:
        if response.status_code >= 500:
            return 502
        return response.status_code

    async def create_invoice(self, invoice: Invoice, token: str) -> InvoiceResponse:

        payload: Dict[str, Any] = {
            "document": invoice.document,
            "reference_code": invoice.reference_code,
            "payment_form": invoice.payment_form,
            "payment_method_code": invoice.payment_method_code,
        }

        if invoice.numbering_range_id is not None:
            payload["numbering_range_id"] = invoice.numbering_range_id

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
                    "number": doc.number
                } for doc in invoice.related_documents
            ]

        if invoice.billing_period:
            payload["billing_period"] = {
                "start_date": invoice.billing_period.start_date.isoformat(),
                "end_date": invoice.billing_period.end_date.isoformat(),
                "end_time": invoice.billing_period.end_time
            }
            if invoice.billing_period.start_time:
                payload["billing_period"]["start_time"] = invoice.billing_period.start_time

        if invoice.establishment:
            payload["establishment"] = invoice.establishment.model_dump()

        if invoice.allowance_charges:
            payload["allowance_charges"] = [
                {
                    "concept_type": ac.concept_type,
                    "is_surcharge": ac.is_surcharge,
                    "reason": ac.reason,
                    "base_amount": str(ac.base_amount),
                    "amount": str(ac.amount)
                } for ac in invoice.allowance_charges
            ]

        # Customer
        # identification_document_id=6 es NIT y requiere DV obligatorio (regla FAK24)
        NIT_DOC_ID = 6
        if (
            invoice.customer.identification_document_id == NIT_DOC_ID
            and not invoice.customer.dv
        ):
            raise Exception(
                "El cliente con NIT debe tener el dígito de verificación (DV) configurado"
            )

        customer = {
            "identification_document_id": invoice.customer.identification_document_id,
            "identification": invoice.customer.identification,
            "legal_organization_id": invoice.customer.legal_organization_id,
            "tribute_id": invoice.customer.tribute_id
        }

        # names siempre debe ser string; Factus lo rechaza si es null
        customer["names"] = invoice.customer.names or invoice.customer.company or ""
        if invoice.customer.address: customer["address"] = invoice.customer.address
        if invoice.customer.email: customer["email"] = invoice.customer.email
        if invoice.customer.phone: customer["phone"] = invoice.customer.phone
        if invoice.customer.municipality_id: customer["municipality_id"] = invoice.customer.municipality_id
        if invoice.customer.dv: customer["dv"] = invoice.customer.dv
        if invoice.customer.company: customer["company"] = invoice.customer.company
        if invoice.customer.trade_name: customer["trade_name"] = invoice.customer.trade_name

        payload["customer"] = customer

        # Items
        payload["items"] = []
        for item in invoice.items:
            item_payload = {
                "code_reference": item.code_reference,
                "name": item.name,
                "quantity": item.quantity,
                "discount_rate": str(item.discount_rate),
                "price": str(item.price),
                "tax_rate": str(item.tax_rate),
                "unit_measure_id": item.unit_measure_id,
                "standard_code_id": item.standard_code_id,
                "is_excluded": item.is_excluded,
                "tribute_id": item.tribute_id
            }

            if item.scheme_id is not None:
                item_payload["scheme_id"] = item.scheme_id
            if item.note:
                item_payload["note"] = item.note
            if item.withholding_taxes is not None:
                item_payload["withholding_taxes"] = [
                    {
                        "code": wt.code,
                        "withholding_tax_rate": str(wt.withholding_tax_rate)
                    } for wt in item.withholding_taxes
                ]
            if item.mandate:
                item_payload["mandate"] = item.mandate.model_dump()
            
            payload["items"].append(item_payload)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/bills/validate",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )

        if not response.is_success:
            logger.error(
                "Factus create_invoice failed — status=%s body=%s payload=%s",
                response.status_code,
                response.text,
                payload,
            )
            raise FactusAPIError(self._parse_error(response, "Error al validar la factura"), status_code=self._status_code(response))

        response_json = response.json()
        data = response_json.get("data", {})
        bill = data.get("bill", {})
        numbering_range = data.get("numbering_range", {})

        return InvoiceResponse(
            number=bill.get("number", ""),
            prefix=numbering_range.get("prefix", ""),
            cufe=bill.get("cufe", ""),
            qr_url=bill.get("qr", ""),
            status=str(bill.get("status", "1")),
            message=response_json.get("message", "Success")
        )

    async def _download(self, endpoint: str, number: str, token: str, extension: str) -> DownloadResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}/{number}",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )

        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, "Error al descargar el archivo"), status_code=self._status_code(response))

        data = response.json().get("data", {})
        file_content = data.get(f"{extension}_base_64_encoded", "")
        return DownloadResponse(
            file_name=data.get("file_name", f"{number}.{extension}"),
            file_content=file_content,
            extension=extension
        )

    async def download_pdf(self, number: str, token: str) -> DownloadResponse:
        return await self._download("v1/bills/download-pdf", number, token, "pdf")

    async def download_xml(self, number: str, token: str) -> DownloadResponse:
        return await self._download("v1/bills/download-xml", number, token, "xml")

    async def get_invoice(self, number: str, token: str) -> InvoiceDataResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/bills/show/{number}",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            
        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, "Error al obtener la factura"), status_code=self._status_code(response))

        response_json = response.json()
        return InvoiceDataResponse(**response_json)

    async def delete_invoice(self, reference_code: str, token: str) -> DeleteInvoiceResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/v1/bills/destroy/reference/{reference_code}",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )

        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, "Error al eliminar la factura"), status_code=self._status_code(response))

        return DeleteInvoiceResponse(**response.json())

    async def send_email(self, number: str, request: SendEmailRequest, token: str) -> SendEmailResponse:
        payload: dict = {"email": request.email}
        if request.pdf_base_64_encoded:
            payload["pdf_base_64_encoded"] = request.pdf_base_64_encoded

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/bills/send-email/{number}",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )

        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, "Error al enviar el correo"), status_code=self._status_code(response))

        return SendEmailResponse(**response.json())

    async def get_invoice_events(self, number: str, token: str) -> InvoiceEventsResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/bills/{number}/radian/events",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )

        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, "Error al obtener eventos de la factura"), status_code=self._status_code(response))

        return InvoiceEventsResponse(**response.json())
