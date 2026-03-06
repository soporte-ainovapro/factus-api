"""
Unit tests for FactusAuthGateway.

All HTTP calls are mocked via unittest.mock — no real network requests.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.src.infrastructure.gateways.factus_auth_gateway import FactusAuthGateway
from app.src.domain.models.auth_token import AuthToken

BASE_URL = "https://api-sandbox.factus.com.co"
CLIENT_ID = "test-client-id"
CLIENT_SECRET = "test-client-secret"

AUTH_TOKEN_RESPONSE = {
    "access_token": "fake-access-token",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "fake-refresh-token",
}


def make_gateway() -> FactusAuthGateway:
    return FactusAuthGateway(
        base_url=BASE_URL,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )


def mock_response(status_code: int, json_body: dict) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.is_success = 200 <= status_code < 300
    r.json.return_value = json_body
    r.text = str(json_body)
    return r


# ---------------------------------------------------------------------------
# authenticate()
# ---------------------------------------------------------------------------

class TestAuthenticate:
    @pytest.mark.asyncio
    async def test_returns_auth_token_on_success(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, AUTH_TOKEN_RESPONSE)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.authenticate("user@test.com", "password123")

        assert isinstance(result, AuthToken)
        assert result.access_token == "fake-access-token"
        assert result.token_type == "Bearer"
        assert result.expires_in == 3600
        assert result.refresh_token == "fake-refresh-token"

    @pytest.mark.asyncio
    async def test_posts_correct_grant_type(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, AUTH_TOKEN_RESPONSE)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            await gateway.authenticate("user@test.com", "secret")

        call_kwargs = mock_client.post.call_args
        sent_data = call_kwargs.kwargs["data"]
        assert sent_data["grant_type"] == "password"
        assert sent_data["username"] == "user@test.com"
        assert sent_data["password"] == "secret"
        assert sent_data["client_id"] == CLIENT_ID
        assert sent_data["client_secret"] == CLIENT_SECRET

    @pytest.mark.asyncio
    async def test_raises_on_http_error_with_message(self):
        gateway = make_gateway()
        fake_resp = mock_response(401, {"message": "Credenciales inválidas"})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception, match="Credenciales inválidas"):
                await gateway.authenticate("bad@test.com", "wrong")

    @pytest.mark.asyncio
    async def test_raises_on_http_error_with_error_description(self):
        gateway = make_gateway()
        fake_resp = mock_response(400, {"error_description": "Invalid credentials"})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception, match="Invalid credentials"):
                await gateway.authenticate("bad@test.com", "wrong")

    @pytest.mark.asyncio
    async def test_handles_missing_refresh_token(self):
        """Factus may omit refresh_token — should not crash."""
        gateway = make_gateway()
        payload = {**AUTH_TOKEN_RESPONSE}
        del payload["refresh_token"]
        fake_resp = mock_response(200, payload)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.authenticate("user@test.com", "pass")

        assert result.refresh_token is None


# ---------------------------------------------------------------------------
# refresh_token()
# ---------------------------------------------------------------------------

class TestRefreshToken:
    @pytest.mark.asyncio
    async def test_returns_new_auth_token(self):
        gateway = make_gateway()
        new_token_resp = {**AUTH_TOKEN_RESPONSE, "access_token": "new-access-token"}
        fake_resp = mock_response(200, new_token_resp)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            result = await gateway.refresh_token("old-refresh-token")

        assert result.access_token == "new-access-token"

    @pytest.mark.asyncio
    async def test_posts_correct_grant_type_for_refresh(self):
        gateway = make_gateway()
        fake_resp = mock_response(200, AUTH_TOKEN_RESPONSE)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            await gateway.refresh_token("my-refresh-token")

        sent_data = mock_client.post.call_args.kwargs["data"]
        assert sent_data["grant_type"] == "refresh_token"
        assert sent_data["refresh_token"] == "my-refresh-token"

    @pytest.mark.asyncio
    async def test_raises_on_invalid_refresh_token(self):
        gateway = make_gateway()
        fake_resp = mock_response(401, {"message": "Token expirado"})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fake_resp)
        mock_async_ctx = MagicMock()
        mock_async_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_async_ctx):
            with pytest.raises(Exception, match="Token expirado"):
                await gateway.refresh_token("expired-token")


# ---------------------------------------------------------------------------
# _parse_error() — internal helper
# ---------------------------------------------------------------------------

class TestParseError:
    def test_prefers_message_field(self):
        gw = make_gateway()
        r = mock_response(400, {"message": "msg", "error_description": "desc"})
        assert gw._parse_error(r, "default") == "msg"

    def test_falls_back_to_error_description(self):
        gw = make_gateway()
        r = mock_response(400, {"error_description": "desc"})
        assert gw._parse_error(r, "default") == "desc"

    def test_falls_back_to_error_field(self):
        gw = make_gateway()
        r = mock_response(400, {"error": "err"})
        assert gw._parse_error(r, "default") == "err"

    def test_uses_default_when_no_known_field(self):
        gw = make_gateway()
        r = mock_response(500, {})
        assert gw._parse_error(r, "default message") == "default message"

    def test_handles_non_json_response(self):
        gw = make_gateway()
        r = MagicMock()
        r.json.side_effect = ValueError("not json")
        r.text = "Internal Server Error"
        result = gw._parse_error(r, "fallback")
        assert result == "Internal Server Error"
