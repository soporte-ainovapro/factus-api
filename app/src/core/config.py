from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    PROJECT_NAME: str = "Factus API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    FACTUS_BASE_URL: str 
    FACTUS_CLIENT_ID: str 
    FACTUS_CLIENT_SECRET: str 
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

settings = Settings()
