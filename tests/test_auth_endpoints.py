"""
Integration tests for the auth endpoints.

Uses FastAPI's TestClient (synchronous) with mocked gateways.
The local JWT auth dependency is overridden in conftest.py.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.src.main import app
from app.src.api.deps import get_current_user
from app.src.domain.models.user import User
from app.src.domain.models.auth_token import AuthToken
from app.src.infrastructure.gateways.factus_auth_gateway import FactusAuthGateway

ADMIN_USER = User(username="admin", email="admin@example.com", full_name="Admin")
FACTUS_TOKEN = AuthToken(
    access_token="factus-access",
    token_type="Bearer",
    expires_in=3600,
    refresh_token="factus-refresh",
)


def get_test_client() -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    return TestClient(app)


class TestLocalLogin:
    def test_login_success(self):
        client = get_test_client()
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        app.dependency_overrides.clear()

    def test_login_wrong_password(self):
        client = get_test_client()
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401
        app.dependency_overrides.clear()

    def test_login_wrong_username(self):
        client = get_test_client()
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "unknown", "password": "admin123"},
        )
        assert response.status_code == 401
        app.dependency_overrides.clear()


class TestFactusLogin:
    def test_factus_login_success(self):
        from app.src.api.v1.endpoints.auth import get_auth_gateway

        mock_gw = AsyncMock(spec=FactusAuthGateway)
        mock_gw.authenticate = AsyncMock(return_value=FACTUS_TOKEN)

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_auth_gateway] = lambda: mock_gw

        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/factus/login",
            json={"email": "sandbox@factus.com.co", "password": "sandbox2024%"},
        )

        app.dependency_overrides.clear()
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["access_token"] == "factus-access"
        assert body["data"]["refresh_token"] == "factus-refresh"

    def test_factus_login_requires_local_jwt(self):
        # Clear overrides — auth dependency not bypassed
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/factus/login",
            json={"email": "sandbox@factus.com.co", "password": "sandbox2024%"},
        )
        assert response.status_code == 401

    def test_factus_login_invalid_email(self):
        client = get_test_client()
        response = client.post(
            "/api/v1/auth/factus/login",
            json={"email": "not-an-email", "password": "pass"},
        )
        app.dependency_overrides.clear()
        assert response.status_code == 422


class TestFactusRefresh:
    def test_refresh_requires_local_jwt(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/factus/refresh",
            json={"refresh_token": "some-token"},
        )
        assert response.status_code == 401

    def test_refresh_missing_body(self):
        client = get_test_client()
        response = client.post("/api/v1/auth/factus/refresh", json={})
        app.dependency_overrides.clear()
        assert response.status_code == 422
