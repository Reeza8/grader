from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import jwt
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

from utils.utils import my_response as apiResponse

load_dotenv(".env")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"

LOGIN_EXEMPT_URLS = [
    "/user/userApi/login/",
    "/user/userApi/verifyCodeLogin/",
    "/user/userApi/loginPassword/",
    "/user/userApi/addUser/",
    "/user/userApi/refresh/",
    "/docs/",
    "/docs",
    "/openapi.json",
]


class CurrentUser:
    def __init__(self, userId: int, roles: list[str]):
        self.userId = userId
        self.roles = roles

    def hasRole(self, role: str) -> bool:
        return role in self.roles


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not any(path.startswith(p) for p in LOGIN_EXEMPT_URLS) and path != "/":
            authHeader = request.headers.get("authorization")
            if not authHeader:
                return self._unauthorized("توکن ارسال نشده است")
            tokenParts = authHeader.split(" ")
            if len(tokenParts) != 2 or tokenParts[0].lower() != "bearer":
                return self._unauthorized("فرمت توکن نامعتبر است")

            try:
                payload = self._decode_jwt(tokenParts[1])

                if payload.get("type") != "access":
                    return self._unauthorized("نوع توکن نامعتبر است")

            except jwt.ExpiredSignatureError:
                return self._unauthorized("توکن منقضی شده است")
            except jwt.InvalidTokenError:
                return self._unauthorized("توکن معتبر نمی‌باشد")
            except Exception:
                return self._unauthorized("خطا در پردازش توکن")

            userId = payload.get("user_id")
            roles = payload.get("roles")

            if not userId or not isinstance(roles, list):
                return self._unauthorized("توکن معتبر نمی‌باشد")

            request.scope["current_user"] = CurrentUser(
                userId=userId,
                roles=roles,
            )

        return await call_next(request)

    def _decode_jwt(self, token: str) -> dict:
        decoded = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        exp = decoded.get("exp")
        if not exp or exp < datetime.now(timezone.utc).timestamp():
            raise jwt.ExpiredSignatureError

        return decoded

    def _unauthorized(self, message: str):
        response = apiResponse(
            status_code=401,
            message=message,
            data=None,
        )
        response.headers["X-RAW-RESPONSE"] = "1"
        return response
