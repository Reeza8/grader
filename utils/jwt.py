import jwt
from datetime import datetime, timedelta
from utils.config import settings


def create_access_token(user_id: int, name:str, role:str) -> str:
    expire = datetime.utcnow() + timedelta(days=180)
    payload = {
        "user_id": user_id,
        "exp": expire,
        "name": name,
        "role": role,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
