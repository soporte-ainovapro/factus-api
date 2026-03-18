"""
Integration tests for auth endpoints.
With API Key auth, there is no longer a local /login endpoint.
Tests verify /factus/login and /factus/refresh require X-API-Key.
"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import verify_api_key
from app.domain.models.auth_token import AuthToken
from app.infrastructure.gateways.factus_auth_gateway import FactusAuthGateway

TEST_API_KEY = "test-api-key-for-pytest"
VALID_API_KEY_HEADER = {"X-API-Key": TEST_API_KEY}

FACTUS_TOKEN = AuthToken(
    access_token="factus-access",
    token_type="Bearer",
    expires_in=3600,
    refresh_token="factus-refresh",
)


def get_auth_client() -> TestClient:
    """TestClient with API Key dependency bypassed."""
    app.dependency_overrides[verify_api_key] = lambda: TEST_API_KEY
    return TestClient(app)


class TestFactusLogin:
    def test_factus_login_success(self):
        from app.api.v1.routers.auth import get_auth_gateway

        mock_gw = AsyncMock(spec=FactusAuthGateway)
        mock_gw.authenticate = AsyncMock(return_value=FACTUS_TOKEN)

        app.dependency_overrides[verify_api_key] = lambda: TEST_API_KEY
        app.dependency_overrides[get_auth_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/auth/factus/login",
            json={"email": "sandbox@factus.com.co", "password": "sandbox2024%"},
            headers=VALID_API_KEY_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "factus-access"
        assert body["refresh_token"] == "factus-refresh"

    def test_factus_login_requires_api_key(self):
        """Without X-API-Key header, the endpoint must return 403."""
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/auth/factus/login",
            json={"email": "sandbox@factus.com.co", "password": "sandbox2024%"},
        )
        # 401 Unauthorized — missing API Key
        assert response.status_code == 401

    def test_factus_login_invalid_api_key(self):
        """An incorrect API Key must return 403."""
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/auth/factus/login",
            json={"email": "sandbox@factus.com.co", "password": "sandbox2024%"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 403

    def test_factus_login_invalid_email(self):
        client = get_auth_client()
        response = client.post(
            "/api/auth/factus/login",
            json={"email": "not-an-email", "password": "pass"},
            headers=VALID_API_KEY_HEADER,
        )
        app.dependency_overrides.clear()
        assert response.status_code == 422


class TestFactusRefresh:
    def test_refresh_requires_api_key(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/auth/factus/refresh",
            json={"refresh_token": "some-token"},
        )
        assert response.status_code == 401

    def test_refresh_missing_body(self):
        client = get_auth_client()
        response = client.post(
            "/api/auth/factus/refresh",
            json={},
            headers=VALID_API_KEY_HEADER,
        )
        app.dependency_overrides.clear()
        assert response.status_code == 422

    def test_refresh_success(self):
        from app.api.v1.routers.auth import get_auth_gateway

        mock_gw = AsyncMock(spec=FactusAuthGateway)
        mock_gw.refresh_token = AsyncMock(return_value=FACTUS_TOKEN)

        app.dependency_overrides[verify_api_key] = lambda: TEST_API_KEY
        app.dependency_overrides[get_auth_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/auth/factus/refresh",
            json={"refresh_token": "factus-refresh"},
            headers=VALID_API_KEY_HEADER,
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "factus-access"
