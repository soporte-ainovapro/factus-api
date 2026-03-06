"""
Unit tests for FactusLookupGateway.

All HTTP calls are mocked — no real network requests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.src.infrastructure.gateways.factus_lookup_gateway import FactusLookupGateway
from app.src.domain.models.lookup import Municipality, Tax, Unit, NumberingRange

BASE_URL = "https://api-sandbox.factus.com.co"
TOKEN = "fake-factus-token"


def make_gateway() -> FactusLookupGateway:
    return FactusLookupGateway(base_url=BASE_URL)


def mock_response(status_code: int, json_body: dict) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.is_success = 200 <= status_code < 300
    r.json.return_value = json_body
    r.text = str(json_body)

    def raise_for_status():
        if not r.is_success:
            from httpx import HTTPStatusError, Request, Response
            raise HTTPStatusError(
                message=f"HTTP {status_code}",
                request=MagicMock(),
                response=MagicMock(status_code=status_code),
            )

    r.raise_for_status = raise_for_status
    return r


# ---------------------------------------------------------------------------
# get_municipalities()
# ---------------------------------------------------------------------------

class TestGetMunicipalities:
    @pytest.mark.asyncio
    async def test_returns_list_of_municipalities(self):
        gateway = make_gateway()
        api_data = [
            {"id": 1, "name": "Bogotá", "code": "11001", "department": "Cundinamarca"},
            {"id": 2, "name": "Medellín", "code": "05001", "department": "Antioquia"},
        ]
        fake_resp = mock_response(200, {"data": api_data})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.get_municipalities(TOKEN)

        assert len(result) == 2
        assert isinstance(result[0], Municipality)
        assert result[0].name == "Bogotá"
        assert result[0].code == "11001"
        assert result[0].department == "Cundinamarca"

    @pytest.mark.asyncio
    async def test_sends_authorization_header(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {"data": []})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            await gateway.get_municipalities(TOKEN)

        headers = mock_client.get.call_args.kwargs["headers"]
        assert headers["Authorization"] == f"Bearer {TOKEN}"

    @pytest.mark.asyncio
    async def test_handles_nested_data_structure(self):
        """Some Factus endpoints wrap data in data.data."""
        gateway = make_gateway()
        api_data = [{"id": 1, "name": "Cali", "code": "76001", "department": "Valle"}]
        # Nested structure: {"data": {"data": [...]}}
        fake_resp = mock_response(200, {"data": {"data": api_data}})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.get_municipalities(TOKEN)

        assert len(result) == 1
        assert result[0].name == "Cali"

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self):
        gateway = make_gateway()
        fake_resp = mock_response(401, {"message": "Unauthenticated"})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception):
                await gateway.get_municipalities(TOKEN)


# ---------------------------------------------------------------------------
# get_tax_types()
# ---------------------------------------------------------------------------

class TestGetTaxTypes:
    @pytest.mark.asyncio
    async def test_returns_list_of_taxes(self):
        gateway = make_gateway()
        api_data = [
            {"id": 1, "name": "IVA", "code": "01", "description": "Impuesto al valor agregado"},
        ]
        fake_resp = mock_response(200, {"data": api_data})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.get_tax_types(TOKEN)

        assert len(result) == 1
        assert isinstance(result[0], Tax)
        assert result[0].code == "01"
        assert result[0].name == "IVA"

    @pytest.mark.asyncio
    async def test_passes_name_filter_as_query_param(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {"data": []})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            await gateway.get_tax_types(TOKEN, name="IVA")

        params = mock_client.get.call_args.kwargs["params"]
        assert params == {"name": "IVA"}

    @pytest.mark.asyncio
    async def test_no_params_when_name_is_none(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, {"data": []})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            await gateway.get_tax_types(TOKEN)

        params = mock_client.get.call_args.kwargs["params"]
        assert params is None


# ---------------------------------------------------------------------------
# get_units()
# ---------------------------------------------------------------------------

class TestGetUnits:
    @pytest.mark.asyncio
    async def test_returns_list_of_units(self):
        gateway = make_gateway()
        api_data = [{"id": 70, "name": "Unidad", "code": "EA"}]
        fake_resp = mock_response(200, {"data": api_data})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.get_units(TOKEN)

        assert len(result) == 1
        assert isinstance(result[0], Unit)
        assert result[0].code == "EA"


# ---------------------------------------------------------------------------
# get_numbering_ranges()
# ---------------------------------------------------------------------------

class TestGetNumberingRanges:
    @pytest.mark.asyncio
    async def test_returns_list_of_numbering_ranges(self):
        gateway = make_gateway()
        api_data = [
            {
                "id": 1,
                "document": "01",
                "prefix": "SETT",
                "from": 1,
                "to": 1000,
                "current": 5,
                "resolution_number": "18760000001",
                "technical_key": "abc123",
                "is_active": True,
            }
        ]
        fake_resp = mock_response(200, {"data": api_data})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.get_numbering_ranges(TOKEN)

        assert len(result) == 1
        nr = result[0]
        assert isinstance(nr, NumberingRange)
        assert nr.prefix == "SETT"
        assert nr.from_number == 1
        assert nr.to_number == 1000
        assert nr.is_active is True
