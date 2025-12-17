from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
import jwt
from datetime import datetime, timezone
from utils.utils import my_response as apiResponse
from dotenv import load_dotenv
import os

load_dotenv(".env")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

LOGIN_EXEMPT_URLS = [
    '/user/userApi/login/',
    '/user/userApi/verifyCodeLogin/',
    '/user/userApi/loginPassword/',
    '/user/userApi/addUser/',
    '/blog/blogApi/getBlogs/',
    '/blog/blogApi/getBlog/',
    '/blog/blogApi/media/',
    '/docs/',
    '/docs',
    '/openapi.json',
    '/blog/categoryApi/getCategories/',
    '/question/questionApi/getQuestions/',
    '/question/questionApi/addConsultantRequest/',
    '/question/questionApi/addContact/',
]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not any(path.startswith(p) for p in LOGIN_EXEMPT_URLS) and path != '/':
            authentication = await self.check_authentication(request)
            if not authentication["authenticated"]:
                return JSONResponse(
                    status_code=401,
                    content=apiResponse(
                        status_code=401,
                        message="کاربر احراز هویت نشده است، توکن وارد نشده است",
                        data=None
                    )
                )

            try:
                payload = await self.decodeJWTToken(authentication.get("token"))
            except jwt.ExpiredSignatureError:
                return JSONResponse(
                    status_code=401,
                    content=apiResponse(
                        status_code=401,
                        message="توکن منقضی شده است",
                        data=None
                    )
                )
            except jwt.InvalidTokenError:
                return JSONResponse(
                    status_code=401,
                    content=apiResponse(
                        status_code=401,
                        message="توکن معتبر نمی‌باشد",
                        data=None
                    )
                )
            except Exception:
                return JSONResponse(
                    status_code=401,
                    content=apiResponse(
                        status_code=401,
                        message="خطا در پردازش توکن",
                        data=None
                    )
                )

            if not payload.get("user_id"):
                return JSONResponse(
                    status_code=401,
                    content=apiResponse(
                        status_code=401,
                        message="توکن معتبر نمی‌باشد",
                        data=None
                    )
                )

            request.scope.update({'user': payload})

        response = await call_next(request)
        return response

    async def decodeJWTToken(self, rawToken: str) -> dict:
        token = rawToken.replace("Bearer ", "").strip()
        decoded_token: dict = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        if decoded_token.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            raise jwt.ExpiredSignatureError
        return decoded_token

    async def check_authentication(self, request: Request):
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return {"authenticated": False, "token": None}

        token_parts = auth_header.split(" ")
        if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
            return {"authenticated": False, "token": None}

        return {"authenticated": True, "token": token_parts[1]}
