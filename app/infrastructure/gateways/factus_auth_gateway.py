import httpx
from app.domain.interfaces.auth_gateway import IAuthGateway
from app.domain.models.auth_token import AuthToken
from app.domain.exceptions import FactusAPIError
from app.core.config import settings

class FactusAuthGateway(IAuthGateway):
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret

    def _parse_error(self, response: httpx.Response, default: str) -> str:
        try:
            error_data = response.json()
            return (
                error_data.get("message")
                or error_data.get("error_description")
                or error_data.get("error")
                or default
            )
        except Exception:
            return response.text or f"HTTP {response.status_code}"

    def _status_code(self, response: httpx.Response) -> int:
        if response.status_code >= 500:
            return 502
        return response.status_code

    async def authenticate(self, email: str, password: str) -> AuthToken:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "password",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "username": email,
                    "password": password,
                },
                headers={"Accept": "application/json"}
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error de autenticación con Factus"),
                status_code=self._status_code(response)
            )

        data = response.json()
        return AuthToken(
            access_token=data["access_token"],
            token_type=data["token_type"],
            expires_in=data["expires_in"],
            refresh_token=data.get("refresh_token")
        )

    async def refresh_token(self, refresh_token: str) -> AuthToken:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
                headers={"Accept": "application/json"}
            )

        if not response.is_success:
            raise FactusAPIError(
                self._parse_error(response, "Error al refrescar el token de Factus"),
                status_code=self._status_code(response)
            )

        data = response.json()
        return AuthToken(
            access_token=data["access_token"],
            token_type=data["token_type"],
            expires_in=data["expires_in"],
            refresh_token=data.get("refresh_token")
        )
