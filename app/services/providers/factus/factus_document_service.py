import httpx
import logging
from typing import Any, Dict, Optional

from app.core.exceptions import FactusAPIError
from app.schemas.results import DownloadResult, DocumentDataResult, DeleteDocumentResult
from app.schemas.shared import SendEmailRequest
from app.services.providers.factus.factus_code_maps import (
    DOCUMENT_TYPE_TO_FACTUS_ID,
    LEGAL_ORGANIZATION_TO_FACTUS_ID,
    ITEM_TRIBUTE_TO_FACTUS_ID,
    CUSTOMER_TRIBUTE_TO_FACTUS_ID,
    UNIT_MEASURE_TO_FACTUS_ID,
    STANDARD_CODE_TO_FACTUS_ID,
)

logger = logging.getLogger(__name__)

class FactusBaseDocumentService:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._muni_cache: Dict[str, int] = {}

    def _parse_error(self, response: httpx.Response, default: str) -> str:
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

        nested_errors = (
            data.get("data", {}).get("errors")
            if isinstance(data.get("data"), dict)
            else None
        )
        if isinstance(nested_errors, dict) and nested_errors:
            field_errors = _fmt_dict_errors(nested_errors)
            return f"{top_message} — {field_errors}" if top_message else field_errors

        errors = data.get("errors")
        if isinstance(errors, dict) and errors:
            field_errors = _fmt_dict_errors(errors)
            return f"{top_message} — {field_errors}" if top_message else field_errors

        if isinstance(errors, list) and errors:
            messages = [
                e.get("message", "")
                for e in errors
                if isinstance(e, dict) and e.get("message")
            ]
            if messages:
                return "; ".join(messages)

        return top_message or default

    def _status_code(self, response: httpx.Response) -> int:
        return 502 if response.status_code >= 500 else response.status_code

    async def _resolve_municipality_id(self, code: str, token: str) -> int:
        if code in self._muni_cache:
            return self._muni_cache[code]

        logger.info(f"Municipality {code} not in cache, fetching from Factus...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/municipalities",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )

        if not response.is_success:
            logger.warning(f"Could not fetch municipalities: {response.text}")
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
                    logger.info(
                        f"Resolved municipality: {m_name} (ID: {m_id}, DANE: {m_code})"
                    )

        return self._muni_cache.get(code) or (int(code) if code.isdigit() else 0)

    async def _map_customer(self, doc_schema: Any, token: str) -> dict:
        cust_doc_type = (
            doc_schema.customer.document_type.value
            if hasattr(doc_schema.customer.document_type, "value")
            else doc_schema.customer.document_type
        )
        customer_doc_id = DOCUMENT_TYPE_TO_FACTUS_ID.get(cust_doc_type)

        if customer_doc_id is None:
            if str(cust_doc_type).isdigit():
                customer_doc_id = int(cust_doc_type)
            else:
                raise FactusAPIError(
                    f"Tipo de documento no soportado por Factus: {cust_doc_type}",
                    status_code=400,
                )

        NIT_DOC_ID = DOCUMENT_TYPE_TO_FACTUS_ID.get("NIT", 6)
        if customer_doc_id == NIT_DOC_ID and not doc_schema.customer.dv:
            raise FactusAPIError(
                "El cliente con NIT debe tener el dígito de verificación (DV) configurado",
                status_code=400,
            )

        org_type = (
            doc_schema.customer.organization_type.value
            if hasattr(doc_schema.customer.organization_type, "value")
            else doc_schema.customer.organization_type
        )
        tribute = (
            doc_schema.customer.tribute.value
            if hasattr(doc_schema.customer.tribute, "value")
            else doc_schema.customer.tribute
        )

        customer: Dict[str, Any] = {
            "identification_document_id": customer_doc_id,
            "identification": doc_schema.customer.identification,
            "legal_organization_id": LEGAL_ORGANIZATION_TO_FACTUS_ID.get(
                org_type, 2
            ),
            "tribute_id": CUSTOMER_TRIBUTE_TO_FACTUS_ID.get(
                tribute, 21
            ),
            "names": doc_schema.customer.names or doc_schema.customer.company or "",
        }

        if doc_schema.customer.address:
            customer["address"] = doc_schema.customer.address
        if doc_schema.customer.email:
            customer["email"] = doc_schema.customer.email
        if doc_schema.customer.phone:
            customer["phone"] = doc_schema.customer.phone
        if doc_schema.customer.municipality_code:
            customer["municipality_id"] = await self._resolve_municipality_id(
                doc_schema.customer.municipality_code, token
            )
        if doc_schema.customer.dv:
            customer["dv"] = doc_schema.customer.dv
        if doc_schema.customer.company:
            customer["company"] = doc_schema.customer.company
        if doc_schema.customer.trade_name:
            customer["trade_name"] = doc_schema.customer.trade_name

        return customer

    def _map_items(self, doc_schema: Any) -> list:
        items = []
        for item in doc_schema.items:
            item_payload: Dict[str, Any] = {
                "code_reference": item.code_reference,
                "name": item.name,
                "quantity": item.quantity,
                "discount_rate": str(item.discount_rate),
                "price": str(item.price),
                "tax_rate": str(item.tax_rate),
                "unit_measure_id": UNIT_MEASURE_TO_FACTUS_ID.get(
                    item.unit_measure_code, 70
                ),
                "standard_code_id": STANDARD_CODE_TO_FACTUS_ID.get(
                    item.standard_code, 1
                ),
                "is_excluded": 1 if item.is_excluded else 0,
                "tribute_id": ITEM_TRIBUTE_TO_FACTUS_ID.get(
                    item.tribute.value
                    if hasattr(item.tribute, "value")
                    else item.tribute,
                    1,
                ),
            }

            if item.scheme_id is not None:
                item_payload["scheme_id"] = item.scheme_id
            if item.note:
                item_payload["note"] = item.note
            if item.withholding_taxes:
                item_payload["withholding_taxes"] = [
                    {
                        "code": wt.code,
                        "withholding_tax_rate": str(wt.withholding_tax_rate),
                    }
                    for wt in item.withholding_taxes
                ]
            if item.mandate:
                item_payload["mandate"] = {
                    "identification_document_id": DOCUMENT_TYPE_TO_FACTUS_ID[
                        item.mandate.document_type.value
                    ],
                    "identification": item.mandate.identification,
                }

            items.append(item_payload)
        return items

    async def _resolve_numbering_range_id(self, prefix: str, token: str) -> int:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/numbering-ranges",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                params={"filter[is_active]": 1},
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al obtener rangos de numeración"),
                status_code=self._status_code(response),
            )

        data = response.json()
        ranges = data.get("data", {})
        if isinstance(ranges, dict):
            ranges = ranges.get("data", [])

        for rng in ranges:
            if rng.get("prefix") == prefix:
                return rng["id"]

        raise FactusAPIError(
            f"No se encontró un rango de numeración activo con prefijo '{prefix}' en Factus",
            status_code=422,
        )

    async def _download(
        self, endpoint: str, number: str, token: str, extension: str
    ) -> DownloadResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}/{number}",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al descargar el archivo"),
                status_code=self._status_code(response),
            )

        data = response.json().get("data", {})
        logger.info(f"DOWNLOAD_DEBUG: keys found in data: {list(data.keys())}")
        
        # Try multiple common keys for base64 content
        content = data.get(f"{extension}_base_64_encoded")
        if not content:
            content = data.get(f"{extension}_base64")
        if not content:
            content = data.get("base64_encoded")
        if not content:
            content = data.get("content")
            
        return DownloadResult(
            file_name=data.get("file_name", f"{number}.{extension}"),
            file_content=content or "",
            extension=extension,
        )

    async def _get_document(self, endpoint: str, token: str, error_msg: str) -> DocumentDataResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )
        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, error_msg), status_code=self._status_code(response))
        return DocumentDataResult(**response.json())

    async def _delete_document(self, endpoint: str, token: str, error_msg: str) -> DeleteDocumentResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/{endpoint}",
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )
        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, error_msg), status_code=self._status_code(response))
        return DeleteDocumentResult(**response.json())

    async def _send_email(self, endpoint: str, request: SendEmailRequest, token: str, error_msg: str) -> None:
        payload: dict = {"email": request.email}
        if request.pdf_base_64_encoded:
            payload["pdf_base_64_encoded"] = request.pdf_base_64_encoded
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/{endpoint}",
                json=payload,
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )
        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, error_msg), status_code=self._status_code(response))

    async def _get_documents(self, endpoint: str, token: str, error_msg: str, filters: Optional[Dict[str, Any]] = None) -> DocumentDataResult:
        params = {}
        if filters:
            for k, v in filters.items():
                if v is not None:
                    params[f"filter[{k}]"] = v

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            )

        if not response.is_success:
            raise FactusAPIError(self._parse_error(response, error_msg), status_code=self._status_code(response))

        return DocumentDataResult(**response.json())

