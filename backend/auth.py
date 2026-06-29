import jwt
from datetime import datetime, timedelta, timezone
from backend.config import settings

def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes = settings.JWT_EXPIRATION_MINUTES)
    #sub (subject) is the actual JWT standard claim name for "who this token is about"
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    username = payload.get("sub")
    
    if username is None:
        raise jwt.InvalidTokenError("Token missing subject")
    
    return username