from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Factus API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    FACTUS_BASE_URL: str
    FACTUS_CLIENT_ID: str
    FACTUS_CLIENT_SECRET: str

    # Clave compartida con backend-app-baiji para autenticación servicio a servicio
    FACTUS_INTERNAL_API_KEY: str

    # Proveedor de facturación activo (factus | siigo | ...)
    BILLING_PROVIDER: str = "factus"

settings = Settings()
