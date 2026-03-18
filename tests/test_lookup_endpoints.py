"""
Integration tests for the lookup endpoints.

Uses FastAPI's TestClient (synchronous) with mocked gateways.
The local JWT auth dependency is overridden via dependency_overrides.
"""
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import verify_api_key
from app.domain.models.user import User
from app.domain.models.lookup import (
    Municipality, Tax, Unit, NumberingRange, Country, Acquirer,
)
from app.domain.exceptions import FactusAPIError
from app.infrastructure.gateways.factus_lookup_gateway import FactusLookupGateway

ADMIN_USER = User(username="admin", email="admin@example.com", full_name="Admin")
FACTUS_TOKEN_HEADER = {"x-factus-token": "fake-factus-token"}


def get_test_client() -> TestClient:
    app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/lookups/reference-tables
# ---------------------------------------------------------------------------

class TestGetReferenceTables:
    def test_returns_all_tables(self):
        client = get_test_client()
        response = client.get("/api/lookups/reference-tables")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        body = response.json()
        assert "identification_document_types" in body
        assert "payment_methods" in body
        assert "payment_forms" in body
        assert "legal_organization_types" in body
        assert "customer_tribute_types" in body
        assert len(body["identification_document_types"]) == 11

    def test_requires_local_jwt(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/lookups/reference-tables")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/lookups/municipalities
# ---------------------------------------------------------------------------

class TestGetMunicipalitiesEndpoint:
    def test_success(self):
        from app.api.v1.routers.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_municipalities = AsyncMock(return_value=[
            Municipality(id=1, name="Bogotá", code="11001", department="Cundinamarca"),
        ])

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/lookups/municipalities", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()[0]["name"] == "Bogotá"

    def test_propagates_factus_error(self):
        from app.api.v1.routers.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_municipalities = AsyncMock(
            side_effect=FactusAPIError("No autorizado", status_code=401)
        )

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/lookups/municipalities", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/lookups/taxes
# ---------------------------------------------------------------------------

class TestGetTaxesEndpoint:
    def test_success(self):
        from app.api.v1.routers.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_tax_types = AsyncMock(return_value=[
            Tax(id=1, name="IVA", code="01"),
        ])

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/lookups/taxes", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()[0]["code"] == "01"


# ---------------------------------------------------------------------------
# GET /api/lookups/countries
# ---------------------------------------------------------------------------

class TestGetCountriesEndpoint:
    def test_success(self):
        from app.api.v1.routers.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_countries = AsyncMock(return_value=[
            Country(id=1, code="CO", name="Colombia"),
        ])

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/lookups/countries", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 200
        assert response.json()[0]["code"] == "CO"

    def test_passes_name_filter(self):
        from app.api.v1.routers.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_countries = AsyncMock(return_value=[])

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        client.get("/api/lookups/countries?name=Colombia", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        mock_gw.get_countries.assert_awaited_once_with("fake-factus-token", name="Colombia")

    def test_propagates_factus_error(self):
        from app.api.v1.routers.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_countries = AsyncMock(
            side_effect=FactusAPIError("Token expirado", status_code=401)
        )

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get("/api/lookups/countries", headers=FACTUS_TOKEN_HEADER)

        app.dependency_overrides.clear()
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/lookups/acquirer
# ---------------------------------------------------------------------------

class TestGetAcquirerEndpoint:
    def test_success(self):
        from app.api.v1.routers.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_acquirer = AsyncMock(return_value=Acquirer(
            name="Empresa ABC",
            email="abc@empresa.com",
        ))

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get(
            "/api/lookups/acquirer?identification_document_id=6&identification_number=900123456",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Empresa ABC"
        assert body["email"] == "abc@empresa.com"

    def test_missing_required_params_returns_422(self):
        client = get_test_client()
        response = client.get("/api/lookups/acquirer", headers=FACTUS_TOKEN_HEADER)
        app.dependency_overrides.clear()
        assert response.status_code == 422

    def test_propagates_factus_404(self):
        from app.api.v1.routers.lookups import get_lookup_gateway

        mock_gw = AsyncMock(spec=FactusLookupGateway)
        mock_gw.get_acquirer = AsyncMock(
            side_effect=FactusAPIError("No encontrado", status_code=404)
        )

        app.dependency_overrides[verify_api_key] = lambda: "admin-api-key"
        app.dependency_overrides[get_lookup_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.get(
            "/api/lookups/acquirer?identification_document_id=6&identification_number=000000000",
            headers=FACTUS_TOKEN_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 404
