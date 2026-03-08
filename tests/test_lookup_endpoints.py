"""
Integration tests for the lookup endpoints.

Uses FastAPI's TestClient (synchronous) with mocked gateways.
The local JWT auth dependency is overridden via dependency_overrides.
"""
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.src.main import app
from app.src.api.deps import get_current_user
from app.src.domain.models.user import User
from app.src.domain.models.lookup import (
    Municipality, Tax, Unit, NumberingRange, Country, Acquirer,
)
from app.src.domain.exceptions import FactusAPIError
from app.src.infrastructure.gateways.factus_lookup_gateway import FactusLookupGateway

ADMIN_USER = User(username="admin", email="admin@example.com", full_name="Admin")
FACTUS_TOKEN_HEADER = {"x-factus-token": "fake-factus-token"}


def get_test_client() -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/v1/lookups/reference-tables
# ---------------------------------------------------------------------------

class TestGetReferenceTables:
    def test_returns_all_tables(self):
        client = get_test_client()
        response = client.get("/api/v1/lookups/reference-tables")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert "identification_document_types" in data
        assert "payment_methods" in data
        assert "payment_forms" in data
        assert len(data["identification_document_types"]) == 11

    def test_requires_local_jwt(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/v1/lookups/reference-tables")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/lookups/municipalities
# ---------------------------------------------------------------------------

class TestGetMunicipalitiesEndpoint:
    def test_success(self):
        from app.src.api.v1.endpoints.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_municipalities = AsyncMock(return_value=[
            Municipality(id=1, name="Bogotá", code="11001", department="Cundinamarca"),
        ])

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/lookups/municipalities", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()["data"][0]["name"] == "Bogotá"

    def test_propagates_factus_error(self):
        from app.src.api.v1.endpoints.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_municipalities = AsyncMock(
            side_effect=FactusAPIError("No autorizado", status_code=401)
        )

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/lookups/municipalities", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/lookups/taxes
# ---------------------------------------------------------------------------

class TestGetTaxesEndpoint:
    def test_success(self):
        from app.src.api.v1.endpoints.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_tax_types = AsyncMock(return_value=[
            Tax(id=1, name="IVA", code="01"),
        ])

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/lookups/taxes", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()["data"][0]["code"] == "01"


# ---------------------------------------------------------------------------
# GET /api/v1/lookups/countries
# ---------------------------------------------------------------------------

class TestGetCountriesEndpoint:
    def test_success(self):
        from app.src.api.v1.endpoints.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_countries = AsyncMock(return_value=[
            Country(id=1, code="CO", name="Colombia"),
        ])

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/lookups/countries", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()["data"][0]["code"] == "CO"

    def test_passes_name_filter(self):
        from app.src.api.v1.endpoints.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_countries = AsyncMock(return_value=[])

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        client.get("/api/v1/lookups/countries?name=Colombia", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        mock_gw.get_countries.assert_awaited_once_with("fake-factus-token", name="Colombia")

    def test_propagates_factus_error(self):
        from app.src.api.v1.endpoints.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_countries = AsyncMock(
            side_effect=FactusAPIError("Token expirado", status_code=401)
        )

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/v1/lookups/countries", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/lookups/acquirer
# ---------------------------------------------------------------------------

class TestGetAcquirerEndpoint:
    def test_success(self):
        from app.src.api.v1.endpoints.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_acquirer = AsyncMock(return_value=Acquirer(
            name="Empresa ABC",
            email="abc@empresa.com",
        ))

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get(
            "/api/v1/lookups/acquirer?identification_document_id=6&identification_number=900123456",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["name"] == "Empresa ABC"
        assert body["data"]["email"] == "abc@empresa.com"

    def test_missing_required_params_returns_422(self):
        client = get_test_client()
        response = client.get("/api/v1/lookups/acquirer", headers=FACTUS_TOKEN_HEADER)
        app.dependency_overrides.clear()
        assert response.status_code == 422

    def test_propagates_factus_404(self):
        from app.src.api.v1.endpoints.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_acquirer = AsyncMock(
            side_effect=FactusAPIError("No encontrado", status_code=404)
        )

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get(
            "/api/v1/lookups/acquirer?identification_document_id=6&identification_number=000000000",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 404
