import httpx
import logging
from typing import Any, Dict, Optional

from app.core.exceptions import FactusAPIError
from app.schemas.credit_note import CreditNote
from app.schemas.shared import SendEmailRequest
from app.schemas.results import (
    DocumentResult,
    DownloadResult,
    DocumentDataResult,
    DeleteDocumentResult,
)
from app.services.providers.factus.factus_document_service import FactusBaseDocumentService
from app.services.providers.factus.factus_code_maps import PAYMENT_FORM_TO_FACTUS_CODE, PAYMENT_METHOD_TO_FACTUS_CODE

logger = logging.getLogger(__name__)

class FactusCreditNoteService(FactusBaseDocumentService):
    async def _build_credit_note_payload(self, credit_note: CreditNote, numbering_range_id: int, token: str) -> Dict[str, Any]:
        raw_pm_code = credit_note.payment_method_code.strip() if credit_note.payment_method_code else ""
        pm_code = PAYMENT_METHOD_TO_FACTUS_CODE.get(raw_pm_code, raw_pm_code)

        payload: Dict[str, Any] = {
            "numbering_range_id": numbering_range_id,
            "reference_code": credit_note.reference_code,
            "correction_concept_code": credit_note.correction_concept_code,
            "customization_id": credit_note.customization_id,
            "bill_id": credit_note.bill_id,
            "payment_form": PAYMENT_FORM_TO_FACTUS_CODE[credit_note.payment_form.value] if hasattr(credit_note.payment_form, "value") else PAYMENT_FORM_TO_FACTUS_CODE[credit_note.payment_form],
            "payment_method_code": pm_code,
        }

        if credit_note.observation:
            payload["observation"] = credit_note.observation
        if credit_note.send_email is not None:
            payload["send_email"] = credit_note.send_email

        if credit_note.billing_period:
            bp = credit_note.billing_period
            payload["billing_period"] = {
                "start_date": bp.start_date.isoformat(),
                "end_date": bp.end_date.isoformat(),
                "end_time": bp.end_time,
            }
            if bp.start_time:
                payload["billing_period"]["start_time"] = bp.start_time

        if credit_note.establishment:
            payload["establishment"] = credit_note.establishment.model_dump()

        if credit_note.allowance_charges:
            payload["allowance_charges"] = [
                {
                    "concept_type": ac.concept_type,
                    "is_surcharge": ac.is_surcharge,
                    "reason": ac.reason,
                    "base_amount": str(ac.base_amount),
                    "amount": str(ac.amount),
                }
                for ac in credit_note.allowance_charges
            ]

        payload["customer"] = await self._map_customer(credit_note, token)
        payload["items"] = self._map_items(credit_note)

        return payload

    async def create_credit_note(self, credit_note: CreditNote, token: str) -> DocumentResult:
        numbering_range_id = await self._resolve_numbering_range_id(
            credit_note.numbering_range_prefix, token
        )
        payload = await self._build_credit_note_payload(credit_note, numbering_range_id, token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/credit-notes/validate",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )

        if not response.is_success:
            logger.error("Factus create_credit_note failed — status=%s body=%s prefix=%s", response.status_code, response.text, credit_note.numbering_range_prefix)
            raise FactusAPIError(
                self._parse_error(response, "Error al validar la nota crédito"),
                status_code=self._status_code(response),
            )

        response_json = response.json()
        
        def find_key_recursive(d: Any, target_key: str) -> Any:
            """Recursively search for a key in a potentially nested dictionary/list."""
            if isinstance(d, dict):
                if target_key in d and d[target_key]:
                    return d[target_key]
                for v in d.values():
                    found = find_key_recursive(v, target_key)
                    if found: return found
            elif isinstance(d, list):
                for item in d:
                    found = find_key_recursive(item, target_key)
                    if found: return found
            return None

        # Robust extraction
        bill_id = find_key_recursive(response_json, "id")
        number = find_key_recursive(response_json, "number")
        # In credit notes, sometimes it's under 'number' or 'number_bill' (if it's referring back)
        # But we want the number of the created document
        if not number:
            number = find_key_recursive(response_json, "number_bill")
            
        cufe = find_key_recursive(response_json, "cufe")
        qr = find_key_recursive(response_json, "qr") or find_key_recursive(response_json, "qr_url") or find_key_recursive(response_json, "public_url")
        status = find_key_recursive(response_json, "status") or "1"
        prefix = find_key_recursive(response_json, "prefix") or credit_note.numbering_range_prefix

        logger.info("RECURSIVE_SEARCH_RESULT: id=%s, number=%s, cufe=%s", bill_id, number, cufe)

        return DocumentResult(
            id=str(bill_id) if bill_id else None,
            number=str(number) if number else "",
            prefix=str(prefix),
            cufe=str(cufe) if cufe else "",
            qr_url=str(qr) if qr else "",
            status=str(status),
            message=response_json.get("message", "Success"),
        )
        
    async def get_credit_notes(self, token: str, filters: Optional[Dict[str, Any]] = None) -> DocumentDataResult:
        return await self._get_documents("v1/credit-notes", token, "Error al obtener las notas crédito", filters)

    async def get_credit_note(self, number: str, token: str) -> DocumentDataResult:
        return await self._get_document(f"v1/credit-notes/{number}", token, "Error al obtener la nota crédito")

    async def download_pdf(self, number: str, token: str) -> DownloadResult:
        return await self._download("v1/credit-notes/download-pdf", number, token, "pdf")

    async def download_xml(self, number: str, token: str) -> DownloadResult:
        return await self._download("v1/credit-notes/download-xml", number, token, "xml")

    async def get_email_content(self, number: str, token: str) -> DocumentDataResult:
        return await self._get_document(f"v1/credit-notes/{number}/email-content", token, "Error al obtener contenido de correo")

    async def delete_credit_note(self, reference_code: str, token: str) -> DeleteDocumentResult:
        return await self._delete_document(f"v1/credit-notes/reference/{reference_code}", token, "Error al eliminar la nota crédito")

    async def send_email(self, number: str, request: SendEmailRequest, token: str) -> None:
        await self._send_email(f"v1/credit-notes/send-email/{number}", request, token, "Error al enviar el correo")
