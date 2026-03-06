"""
Shared fixtures and helpers for the test suite.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.src.main import app
from app.src.core.security import create_access_token
from app.src.api.deps import fake_users_db, get_current_user
from app.src.domain.models.user import User


# ---------------------------------------------------------------------------
# JWT helper
# ---------------------------------------------------------------------------

def make_local_token(username: str = "admin") -> str:
    """Return a valid local JWT for the given username."""
    return create_access_token(data={"sub": username})


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    """Synchronous TestClient that bypasses local auth by injecting a real user."""
    admin_user = User(**fake_users_db["admin"])

    # Override the auth dependency so tests don't need a real JWT
    app.dependency_overrides[get_current_user] = lambda: admin_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


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
# Minimal valid Invoice payload (dict form, used in endpoint tests)
# ---------------------------------------------------------------------------

VALID_INVOICE_PAYLOAD = {
    "document": "01",
    "reference_code": "REF-TEST-001",
    "payment_form": "1",
    "payment_method_code": "10",
    "customer": {
        "identification_document_id": 3,
        "identification": "900123456",
        "legal_organization_id": 1,
        "tribute_id": 21,
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
            "unit_measure_id": 70,
            "standard_code_id": 1,
            "is_excluded": 0,
            "tribute_id": 21,
        }
    ],
}
