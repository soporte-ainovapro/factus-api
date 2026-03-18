"""
Shared fixtures and helpers for the test suite.

With API Key auth, tests now inject a valid key via override or pass it
directly in HTTP headers. The old local JWT mechanism has been removed.
"""
import pytest
import os
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import verify_api_key
from app.core.config import settings

# Use a fixed test API key that matches what the deps.py will validate.
TEST_API_KEY = "test-api-key-for-pytest"


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    """
    Synchronous TestClient that bypasses API Key auth by overriding the
    verify_api_key dependency. Use this for endpoint tests that should
    not be blocked by auth.
    """
    app.dependency_overrides[verify_api_key] = lambda: TEST_API_KEY

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth() -> TestClient:
    """TestClient WITHOUT auth override — tests that verify 403 responses."""
    app.dependency_overrides.clear()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Common mock httpx response factory
# ---------------------------------------------------------------------------

def mock_httpx_response(status_code: int, json_body: dict) -> MagicMock:
    """Build a MagicMock that behaves like an httpx.Response."""
    response = MagicMock()
    response.status_code = status_code
    response.is_success = 200 <= status_code < 300
    response.json.return_value = json_body
    response.text = str(json_body)
    return response


# ---------------------------------------------------------------------------
# Minimal valid Invoice payload (canonical fields, used in endpoint tests)
# ---------------------------------------------------------------------------

VALID_INVOICE_PAYLOAD = {
    "numbering_range_prefix": "SETT",
    "document_type": "invoice",
    "reference_code": "REF-TEST-001",
    "payment_form": "cash",
    "payment_method_code": "10",
    "customer": {
        "document_type": "CC",
        "identification": "900123456",
        "organization_type": "person",
        "tribute": "ZZ",
        "names": "Juan Perez",
        "email": "juan@example.com",
    },
    "items": [
        {
            "code_reference": "ITEM-001",
            "name": "Producto de prueba",
            "quantity": 1,
            "price": "10000.00",
            "discount_rate": "0.00",
            "tax_rate": "19.00",
            "unit_measure_code": "94",
            "standard_code": "1",
            "is_excluded": False,
            "tribute": "IVA",
        }
    ],
}
