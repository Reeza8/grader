from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import json

class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        excluded_paths = ["/docs", "/redoc", "/openapi.json"]

        if any(request.url.path.startswith(path) for path in excluded_paths):
            return await call_next(request)

        response = await call_next(request)

        if response.headers.get("X-RAW-RESPONSE") == "1":
            return response

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
            status_code = data.pop("code", response.status_code)
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

        new_response = JSONResponse(
            status_code=status_code,
            content=custom_response
        )

        for key, value in response.headers.items():
            if key.lower() != "content-length":
                new_response.headers[key] = value

        return new_response
