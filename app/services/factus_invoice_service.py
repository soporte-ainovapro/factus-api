import httpx
import logging
from typing import Any, Dict, Optional

from app.core.exceptions import FactusAPIError
from app.schemas.invoice import Invoice, SendEmailRequest
from app.schemas.results import (
    InvoiceResult, DownloadResult, InvoiceDataResult,
    DeleteInvoiceResult, InvoiceEventsResult
)
from app.services.factus_code_maps import (
    DOCUMENT_TYPE_TO_FACTUS_ID,
    LEGAL_ORGANIZATION_TO_FACTUS_ID,
    ITEM_TRIBUTE_TO_FACTUS_ID,
    CUSTOMER_TRIBUTE_TO_FACTUS_ID,
    PAYMENT_FORM_TO_FACTUS_CODE,
    DOCUMENT_TYPE_TO_FACTUS_BILL_CODE,
    UNIT_MEASURE_TO_FACTUS_ID,
    STANDARD_CODE_TO_FACTUS_ID,
    PAYMENT_METHOD_TO_FACTUS_CODE
)

logger = logging.getLogger(__name__)


class FactusInvoiceService:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._muni_cache: Dict[str, int] = {}  # code (DANE) -> id (Factus)

    # ── Error parsing ────────────────────────────────────────────────────────

    def _parse_error(self, response: httpx.Response, default: str) -> str:
        """
        Extrae un mensaje de error legible de la respuesta de Factus.

        Factus usa dos formatos de error:
        - 422 Validación: {"message": "...", "data": {"errors": {"field": ["msg"]}}}
        - 409 Conflicto:  {"status": "Conflict", "errors": [{"message": "...", ...}]}
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
                    parts.append(str(msgs))
            return "; ".join(parts)

        nested_errors = data.get("data", {}).get("errors") if isinstance(data.get("data"), dict) else None
        if isinstance(nested_errors, dict) and nested_errors:
            field_errors = _fmt_dict_errors(nested_errors)
            return f"{top_message} — {field_errors}" if top_message else field_errors

        errors = data.get("errors")
        if isinstance(errors, dict) and errors:
            field_errors = _fmt_dict_errors(errors)
            return f"{top_message} — {field_errors}" if top_message else field_errors

        if isinstance(errors, list) and errors:
            messages = [e.get("message", "") for e in errors if isinstance(e, dict) and e.get("message")]
            if messages:
                return "; ".join(messages)

        return top_message or default

    def _status_code(self, response: httpx.Response) -> int:
        return 502 if response.status_code >= 500 else response.status_code

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _resolve_municipality_id(self, code: str, token: str) -> int:
        """
        Resuelve el ID de Factus para un municipio dado su código DANE.
        Utiliza un caché en memoria para evitar llamadas redundantes.
        """
        if code in self._muni_cache:
            return self._muni_cache[code]

        logger.info(f"Municipality {code} not in cache, fetching from Factus...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/municipalities",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"}
            )

        if not response.is_success:
            logger.warning(f"Could not fetch municipalities: {response.text}")
            # Si falla el lookup, devolvemos el código tal cual (podría ser ya un ID)
            # o lanzamos error si somos estrictos. Intentemos ser tolerantes por ahora.
            try:
                return int(code)
            except Exception:
                return 0

        data = response.json()
        munis = data.get("data", [])
        if isinstance(munis, dict):
            munis = munis.get("data", [])

        for m in munis:
            m_code = m.get("code")
            m_id = m.get("id")
            m_name = m.get("name")
            if m_code:
                self._muni_cache[m_code] = m_id
                if m_code == code:
                    logger.info(f"Resolved municipality: {m_name} (ID: {m_id}, DANE: {m_code})")

        return self._muni_cache.get(code) or (int(code) if code.isdigit() else 0)

    # ── Payload mapping ──────────────────────────────────────────────────────

    async def _map_customer(self, invoice: Invoice, token: str) -> dict:
        """Traduce el Customer canónico al formato que Factus espera."""
        cust_doc_type = invoice.customer.document_type.value if hasattr(invoice.customer.document_type, 'value') else invoice.customer.document_type
        customer_doc_id = DOCUMENT_TYPE_TO_FACTUS_ID.get(cust_doc_type)

        if customer_doc_id is None:
            # Tolerancia: si ya es un dígito, lo usamos directamente
            if str(cust_doc_type).isdigit():
                customer_doc_id = int(cust_doc_type)
            else:
                raise FactusAPIError(
                    f"Tipo de documento no soportado por Factus: {cust_doc_type}",
                    status_code=400
                )

        NIT_DOC_ID = DOCUMENT_TYPE_TO_FACTUS_ID.get("NIT", 6)
        if customer_doc_id == NIT_DOC_ID and not invoice.customer.dv:
            raise FactusAPIError(
                "El cliente con NIT debe tener el dígito de verificación (DV) configurado",
                status_code=400
            )

        org_type = invoice.customer.organization_type.value if hasattr(invoice.customer.organization_type, 'value') else invoice.customer.organization_type
        tribute = invoice.customer.tribute.value if hasattr(invoice.customer.tribute, 'value') else invoice.customer.tribute

        customer: Dict[str, Any] = {
            "identification_document_id": customer_doc_id,
            "identification": invoice.customer.identification,
            "legal_organization_id": LEGAL_ORGANIZATION_TO_FACTUS_ID.get(org_type, 2), # Default Natural
            "tribute_id": CUSTOMER_TRIBUTE_TO_FACTUS_ID.get(tribute, 21), # Default No aplica
            "names": invoice.customer.names or invoice.customer.company or "",
        }

        if invoice.customer.address:
            customer["address"] = invoice.customer.address
        if invoice.customer.email:
            customer["email"] = invoice.customer.email
        if invoice.customer.phone:
            customer["phone"] = invoice.customer.phone
        if invoice.customer.municipality_code:
            # Resolvemos el código DANE a ID de Factus
            customer["municipality_id"] = await self._resolve_municipality_id(invoice.customer.municipality_code, token)
        if invoice.customer.dv:
            customer["dv"] = invoice.customer.dv
        if invoice.customer.company:
            customer["company"] = invoice.customer.company
        if invoice.customer.trade_name:
            customer["trade_name"] = invoice.customer.trade_name

        return customer

    def _map_items(self, invoice: Invoice) -> list:
        """Traduce los items canónicos al formato que Factus espera."""
        items = []
        for item in invoice.items:
            item_payload: Dict[str, Any] = {
                "code_reference": item.code_reference,
                "name": item.name,
                "quantity": item.quantity,
                "discount_rate": str(item.discount_rate),
                "price": str(item.price),
                "tax_rate": str(item.tax_rate),
                "unit_measure_id": UNIT_MEASURE_TO_FACTUS_ID.get(item.unit_measure_code, 70),  # Por defecto Unidad
                "standard_code_id": STANDARD_CODE_TO_FACTUS_ID.get(item.standard_code, 1), # Por defecto 1
                "is_excluded": 1 if item.is_excluded else 0,
                "tribute_id": ITEM_TRIBUTE_TO_FACTUS_ID.get(item.tribute.value if hasattr(item.tribute, 'value') else item.tribute, 1),
            }

            if item.scheme_id is not None:
                item_payload["scheme_id"] = item.scheme_id
            if item.note:
                item_payload["note"] = item.note
            if item.withholding_taxes:
                item_payload["withholding_taxes"] = [
                    {
                        "code": wt.code,
                        "withholding_tax_rate": str(wt.withholding_tax_rate)
                    }
                    for wt in item.withholding_taxes
                ]
            if item.mandate:
                item_payload["mandate"] = {
                    "identification_document_id": DOCUMENT_TYPE_TO_FACTUS_ID[item.mandate.document_type.value],
                    "identification": item.mandate.identification,
                }

            items.append(item_payload)
        return items

    async def _resolve_numbering_range_id(self, prefix: str, token: str) -> int:
        """
        Resuelve el numbering_range_id (entero) de Factus a partir del prefijo.
        Hace una llamada al endpoint de rangos de Factus y busca el activo con ese prefijo.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/numbering-ranges",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
                params={"filter[is_active]": 1}
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al obtener rangos de numeración"),
                status_code=self._status_code(response)
            )

        data = response.json()
        ranges = data.get("data", {})
        # Puede venir paginado
        if isinstance(ranges, dict):
            ranges = ranges.get("data", [])

        for rng in ranges:
            if rng.get("prefix") == prefix:
                return rng["id"]

        raise FactusAPIError(
            f"No se encontró un rango de numeración activo con prefijo '{prefix}' en Factus",
            status_code=422
        )

    async def _build_payload(self, invoice: Invoice, numbering_range_id: int, token: str) -> Dict[str, Any]:
        """Construye el payload completo para la API de Factus a partir del modelo canónico."""
        # Mapeamos payment_method_code si es un alias canónico (ej: "cash_payment" -> "10")
        raw_pm_code = invoice.payment_method_code.strip() if invoice.payment_method_code else ""
        pm_code = PAYMENT_METHOD_TO_FACTUS_CODE.get(raw_pm_code, raw_pm_code)

        payload: Dict[str, Any] = {
            "numbering_range_id": numbering_range_id,
            "document": DOCUMENT_TYPE_TO_FACTUS_BILL_CODE[invoice.document_type.value],
            "reference_code": invoice.reference_code,
            "payment_form": PAYMENT_FORM_TO_FACTUS_CODE[invoice.payment_form.value],
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
            payload["order_reference"] = {"reference_code": invoice.order_reference.reference_code}
            if invoice.order_reference.issue_date:
                payload["order_reference"]["issue_date"] = invoice.order_reference.issue_date.isoformat()

        if invoice.related_documents:
            payload["related_documents"] = [
                {"code": doc.code, "issue_date": doc.issue_date.isoformat(), "number": doc.number}
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

    async def create_invoice(self, invoice: Invoice, token: str) -> InvoiceResult:
        numbering_range_id = await self._resolve_numbering_range_id(
            invoice.numbering_range_prefix, token
        )
        payload = await self._build_payload(invoice, numbering_range_id, token)
        # logger.info(f"Sending invoice payload to Factus: {payload}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/bills/validate",
                json=payload,
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )

        if not response.is_success:
            logger.error(
                "Factus create_invoice failed — status=%s body=%s prefix=%s",
                response.status_code, response.text, invoice.numbering_range_prefix,
            )
            raise FactusAPIError(
                self._parse_error(response, "Error al validar la factura"),
                status_code=self._status_code(response)
            )

        response_json = response.json()
        data = response_json.get("data", {})
        bill = data.get("bill", {})
        numbering_range = data.get("numbering_range", {})

        return InvoiceResult(
            number=bill.get("number", ""),
            prefix=numbering_range.get("prefix", invoice.numbering_range_prefix),
            cufe=bill.get("cufe", ""),
            qr_url=bill.get("qr", ""),
            status=str(bill.get("status", "1")),
            message=response_json.get("message", "Success"),
        )

    async def _download(self, endpoint: str, number: str, token: str, extension: str) -> DownloadResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}/{number}",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al descargar el archivo"),
                status_code=self._status_code(response)
            )

        data = response.json().get("data", {})
        return DownloadResult(
            file_name=data.get("file_name", f"{number}.{extension}"),
            file_content=data.get(f"{extension}_base_64_encoded", ""),
            extension=extension,
        )

    async def download_pdf(self, number: str, token: str) -> DownloadResult:
        return await self._download("v1/bills/download-pdf", number, token, "pdf")

    async def download_xml(self, number: str, token: str) -> DownloadResult:
        return await self._download("v1/bills/download-xml", number, token, "xml")

    async def get_invoice(self, number: str, token: str) -> InvoiceDataResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/bills/show/{number}",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al obtener la factura"),
                status_code=self._status_code(response)
            )

        response_json = response.json()
        return InvoiceDataResult(**response_json)

    async def delete_invoice(self, reference_code: str, token: str) -> DeleteInvoiceResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/v1/bills/destroy/reference/{reference_code}",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al eliminar la factura"),
                status_code=self._status_code(response)
            )

        return DeleteInvoiceResult(**response.json())

    async def send_email(self, number: str, request: SendEmailRequest, token: str) -> None:
        payload: dict = {"email": request.email}
        if request.pdf_base_64_encoded:
            payload["pdf_base_64_encoded"] = request.pdf_base_64_encoded

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/bills/send-email/{number}",
                json=payload,
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al enviar el correo"),
                status_code=self._status_code(response)
            )

    async def get_invoice_events(self, number: str, token: str) -> InvoiceEventsResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/bills/{number}/radian/events",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al obtener eventos de la factura"),
                status_code=self._status_code(response)
            )

        return InvoiceEventsResult(**response.json())
