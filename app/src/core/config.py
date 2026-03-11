from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    PROJECT_NAME: str = "Factus API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    FACTUS_BASE_URL: str
    FACTUS_CLIENT_ID: str
    FACTUS_CLIENT_SECRET: str

    # Clave compartida con backend-app-baiji para autenticación servicio a servicio
    FACTUS_INTERNAL_API_KEY: str

    # Mantenemos SECRET_KEY para firma JWT (auth legacy / testing)
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

settings = Settings()
