from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.src.core.config import settings
from app.src.domain.models.user import TokenData, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# En una implementación real, esto consultaría una base de datos.
# Para este ejemplo, usaremos un usuario "mock".
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Factus Admin",
        "email": "admin@example.com",
        "hashed_password": "", # No la usaremos aquí directamente
        "disabled": False,
    }
}

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user_dict = fake_users_db.get(token_data.username)
    if user_dict is None:
        raise credentials_exception
    return User(**user_dict)
