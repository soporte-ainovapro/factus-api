import asyncio
import logging
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.services.providers.factus.factus_auth_service import FactusAuthService

logger = logging.getLogger(__name__)

class FactusTokenManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FactusTokenManager, cls).__new__(cls)
            cls._instance.access_token = None
            cls._instance.refresh_token_val = None
            cls._instance.expires_at = None
            cls._instance.auth_service = FactusAuthService(
                base_url=settings.FACTUS_BASE_URL,
                client_id=settings.FACTUS_CLIENT_ID,
                client_secret=settings.FACTUS_CLIENT_SECRET,
            )
        return cls._instance

    async def get_token(self) -> str:
        """Obtiene un token válido, autenticándose o refrescándolo si es necesario."""
        async with self._lock:
            # Si tenemos token y no ha expirado (damos 5 minutos de margen)
            if self.access_token and self.expires_at:
                if datetime.now(timezone.utc) < (self.expires_at - timedelta(minutes=5)):
                    return self.access_token

            # Si tenemos refresh_token pero el access_token expiró
            if self.refresh_token_val:
                try:
                    logger.info("Refrescando token de Factus...")
                    auth_data = await self.auth_service.refresh_token(self.refresh_token_val)
                    self._update_token_data(auth_data)
                    return self.access_token
                except Exception as e:
                    logger.error(f"Error refrescando token: {e}. Intentando login completo...")
                    self.access_token = None
                    self.refresh_token_val = None

            # Login completo
            logger.info("Iniciando nueva sesión en Factus...")
            auth_data = await self.auth_service.authenticate(
                settings.FACTUS_USERNAME, settings.FACTUS_PASSWORD
            )
            self._update_token_data(auth_data)
            return self.access_token

    def _update_token_data(self, auth_data):
        self.access_token = auth_data.access_token
        self.refresh_token_val = auth_data.refresh_token
        # expires_in viene en segundos
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=auth_data.expires_in)

token_manager = FactusTokenManager()
