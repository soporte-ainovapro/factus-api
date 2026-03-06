from pydantic import BaseModel

class AuthToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
