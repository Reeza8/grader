import jwt
from datetime import datetime, timedelta
from utils.config import settings


ACCESS_TOKEN_MINUTES = 30
REFRESH_TOKEN_DAYS = 90


def create_access_token(user_id: int, name: str, roles: list[str]) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    payload = {
        "user_id": user_id,
        "name": name,
        "roles": roles,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS)
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
