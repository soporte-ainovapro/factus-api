import httpx
from typing import List
from app.src.domain.interfaces.lookup_gateway import ILookupGateway
from app.src.domain.models.lookup import (
    Municipality, Unit, Tax, NumberingRange
)

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

            response.raise_for_status()

            json_response = response.json()
            data = json_response.get("data", [])

            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            if not isinstance(data, list):
                raise Exception(f"Unexpected API structure: {data}")

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
