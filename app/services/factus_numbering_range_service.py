import httpx
import logging
from typing import Dict, Any, Optional

from app.schemas.numbering_range import (
    NumberingRangeResponse,
    NumberingRangeListResponse,
    NumberingRangeCreate,
    NumberingRangeUpdate,
    NumberingRangeDeleteResponse,
    NumberingRangeSoftwareResponse,
)
from app.core.exceptions import FactusAPIError

logger = logging.getLogger(__name__)

class FactusNumberingRangeService:
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

    def _get_headers(self, token: str) -> dict:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

    async def get_numbering_ranges(self, token: str, filters: Optional[Dict[str, Any]] = None) -> NumberingRangeListResponse:
        params = {}
        if filters:
            for key, value in filters.items():
                if value is not None:
                    params[f"filter[{key}]"] = value

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/numbering-ranges",
                headers=self._get_headers(token),
                params=params
            )
            
        if not response.is_success:
            logger.error("Factus get_numbering_ranges failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al obtener los rangos de numeración"), status_code=self._status_code(response))

        r_json = response.json()
        
        # Extract the inner array if the response is paginated to match the model
        if "data" in r_json and isinstance(r_json["data"], dict) and "data" in r_json["data"]:
            r_json["data"] = r_json["data"]["data"]
            
        return NumberingRangeListResponse(**r_json)

    async def get_numbering_range(self, id: int, token: str) -> NumberingRangeResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/numbering-ranges/{id}",
                headers=self._get_headers(token)
            )

        if not response.is_success:
            logger.error("Factus get_numbering_range failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al obtener el rango de numeración"), status_code=self._status_code(response))

        return NumberingRangeResponse(**response.json())

    async def create_numbering_range(self, range_data: NumberingRangeCreate, token: str) -> NumberingRangeResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/numbering-ranges",
                json=range_data.model_dump(),
                headers=self._get_headers(token)
            )

        if not response.is_success:
            logger.error("Factus create_numbering_range failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al crear el rango de numeración"), status_code=self._status_code(response))

        return NumberingRangeResponse(**response.json())

    async def update_numbering_range_consecutive(self, id: int, update_data: NumberingRangeUpdate, token: str) -> NumberingRangeResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self.base_url}/v1/numbering-ranges/{id}",
                json=update_data.model_dump(),
                headers=self._get_headers(token)
            )

        if not response.is_success:
            logger.error("Factus update_numbering_range_consecutive failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al actualizar el rango de numeración"), status_code=self._status_code(response))

        return NumberingRangeResponse(**response.json())

    async def delete_numbering_range(self, id: int, token: str) -> NumberingRangeDeleteResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/v1/numbering-ranges/{id}",
                headers=self._get_headers(token)
            )

        if not response.is_success:
            logger.error("Factus delete_numbering_range failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al eliminar el rango de numeración"), status_code=self._status_code(response))

        return NumberingRangeDeleteResponse(**response.json())

    async def get_software_numbering_ranges(self, token: str) -> NumberingRangeSoftwareResponse:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/dian/numbering-ranges",
                headers=self._get_headers(token)
            )

        if not response.is_success:
            logger.error("Factus get_software_numbering_ranges failed — status=%s body=%s", response.status_code, response.text)
            raise FactusAPIError(self._parse_error(response, "Error al obtener los rangos asociados al software"), status_code=self._status_code(response))

        return NumberingRangeSoftwareResponse(**response.json())
