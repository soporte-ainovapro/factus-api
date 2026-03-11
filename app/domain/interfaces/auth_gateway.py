from abc import ABC, abstractmethod
from app.domain.models.auth_token import AuthToken

class IAuthGateway(ABC):
    @abstractmethod
    async def authenticate(self, email: str, password: str) -> AuthToken:
        """
        Authenticates with the external API and returns an AuthToken.
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """
        Refreshes the access token using a refresh token.
        """
        pass
