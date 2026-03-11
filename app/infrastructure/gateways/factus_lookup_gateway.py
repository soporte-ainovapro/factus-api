import httpx
from typing import List, Optional
from app.domain.interfaces.lookup_gateway import ILookupGateway
from app.domain.models.lookup import (
    Municipality, Unit, Tax, NumberingRange, Country, Acquirer
)
from app.domain.exceptions import FactusAPIError

class FactusLookupGateway(ILookupGateway):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def _get(
        self,
        endpoint: str,
        token: str | None = None,
        params: dict | None = None
    ) -> List[dict]:

        headers = {"Accept": "application/json"}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                params=params
            )

            if not response.is_success:
                status_code = 502 if response.status_code >= 500 else response.status_code
                try:
                    msg = response.json().get("message") or response.text
                except Exception:
                    msg = response.text
                raise FactusAPIError(msg or f"HTTP {response.status_code}", status_code=status_code)

            json_response = response.json()
            data = json_response.get("data", [])

            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            if not isinstance(data, list):
                raise FactusAPIError(f"Unexpected API structure: {data}", status_code=502)

            return data

    async def _get_object(
        self,
        endpoint: str,
        token: str | None = None,
        params: dict | None = None
    ) -> dict:

        headers = {"Accept": "application/json"}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                params=params
            )

            if not response.is_success:
                status_code = 502 if response.status_code >= 500 else response.status_code
                try:
                    msg = response.json().get("message") or response.text
                except Exception:
                    msg = response.text
                raise FactusAPIError(msg or f"HTTP {response.status_code}", status_code=status_code)

            json_response = response.json()
            data = json_response.get("data", {})

            if not isinstance(data, dict):
                raise FactusAPIError(f"Unexpected API structure: {data}", status_code=502)

            return data

    async def get_municipalities(
        self,
        token: str
    ) -> List[Municipality]:

        data = await self._get(
            "v1/municipalities",
            token=token
        )

        return [Municipality(**item) for item in data]

    async def get_tax_types(
        self,
        token: str,
        name: str | None = None
    ) -> List[Tax]:

        params = {"name": name} if name else None

        data = await self._get(
            "v1/tributes/products",
            token=token,
            params=params
        )

        return [Tax(**item) for item in data]

    async def get_units(
        self,
        token: str
    ) -> List[Unit]:

        data = await self._get(
            "v1/measurement-units",
            token=token
        )

        return [Unit(**item) for item in data]

    async def get_numbering_ranges(
        self,
        token: str
    ) -> List[NumberingRange]:

        data = await self._get(
            "v1/numbering-ranges",
            token=token
        )

        return [NumberingRange(**item) for item in data]

    async def get_countries(
        self,
        token: str,
        name: Optional[str] = None
    ) -> List[Country]:

        params = {"name": name} if name else None

        data = await self._get(
            "v1/countries",
            token=token,
            params=params
        )

        return [Country(**item) for item in data]

    async def get_acquirer(
        self,
        token: str,
        identification_document_id: int,
        identification_number: str
    ) -> Acquirer:

        data = await self._get_object(
            "v1/dian/acquirer",
            token=token,
            params={
                "identification_document_id": identification_document_id,
                "identification_number": identification_number
            }
        )

        return Acquirer(**data)
