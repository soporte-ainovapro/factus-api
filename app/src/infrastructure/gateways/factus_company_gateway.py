import httpx
import logging
from app.src.domain.interfaces.company_gateway import ICompanyGateway
from app.src.domain.models.company import CompanyResponse, CompanyUpdate, CompanyLogoUpdateResponse
from app.src.domain.exceptions import FactusAPIError

logger = logging.getLogger(__name__)

class FactusCompanyGateway(ICompanyGateway):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

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
        if response.status_code >= 500:
            return 502
        return response.status_code

    async def get_company(self, token: str) -> CompanyResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/company",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            
        if not response.is_success:
            logger.error("Factus get_company failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al obtener la empresa"), status_code=self._status_code(response))

        return CompanyResponse(**response.json())

    async def update_company(self, company: CompanyUpdate, token: str) -> CompanyResponse:
        payload = company.model_dump(exclude_unset=True)
        # Ensure company, trade_name, and registration_code are explicitly passed even if None
        # They were marked as Optional in API docs example body
        for field in ["company", "trade_name", "registration_code"]:
            if field not in payload and getattr(company, field, None) is None:
                payload[field] = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self.base_url}/v1/company",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )

        if not response.is_success:
            logger.error("Factus update_company failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al actualizar la empresa"), status_code=self._status_code(response))

        return CompanyResponse(**response.json())

    async def update_company_logo(self, file_name: str, file_content: bytes, file_content_type: str, token: str) -> CompanyLogoUpdateResponse:
        files = {
            "image": (file_name, file_content, file_content_type)
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/company/logo",
                files=files,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )

        if not response.is_success:
            logger.error("Factus update_company_logo failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al actualizar el logo de la empresa"), status_code=self._status_code(response))

        return CompanyLogoUpdateResponse(**response.json())
