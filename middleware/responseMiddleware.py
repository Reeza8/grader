from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import json

class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # مسیرهای مستثنی (مستندات)
        excluded_paths = ["/docs", "/redoc", "/openapi.json"]

        # بررسی اینکه آیا مسیر فعلی جزو مسیرهای مستثنی است یا نه
        if any(request.url.path.startswith(path) for path in excluded_paths):
            return await call_next(request)

        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return response

        content = b""
        async for chunk in response.body_iterator:
            content += chunk

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return response

        if isinstance(data, dict):
            status_code = data.pop("code", 200)
            message = data.pop("message", "عملیات با موفقیت انجام شد.")
            payload = data.get("data", None)
        else:
            status_code = 500
            message = "خروجی دیکشنری نیست! با پشتیبانی تماس بگیرید"
            payload = data

        is_success = 200 <= status_code < 300

        custom_response = {
            "status": is_success,
            "code": status_code,
            "message": message,
            "data": payload
        }

        return JSONResponse(status_code=status_code, content=custom_response)
