import string
import re
import random
from pydantic import BaseModel
from typing import Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
import secrets
from fastapi import Request, Depends, HTTPException
from passlib.context import CryptContext
from starlette.responses import JSONResponse
import jdatetime
from utils.common import CurrentUser



password_regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')
PHONE_REGEX = re.compile(r"^\+98\d{10}$")
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,4}$")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def generate_random_password(length=8):
    if length < 8:
        raise ValueError("حداقل طول رمز عبور باید ۸ کاراکتر باشد.")

    while True:
        chars = string.ascii_letters + string.digits
        password = ''.join(random.choices(chars, k=length))
        if password_regex.match(password):
            return password

def my_response(status_code: int, message: str = "", data: Optional[Any] = None) -> JSONResponse:
    if isinstance(data, BaseModel):
        data = data.dict()

    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "message": message,
            "data": data
        }
    )

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))

def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone))

async def http_exception_handler(request: Request, exc: HTTPException):
    response = my_response(
        status_code=exc.status_code,
        message=exc.detail,
        data=None,
    )
    response.headers["X-RAW-RESPONSE"] = "1"
    return response

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if "JSON decode error" in str(exc) or "Expecting value" in str(exc):
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content=my_response(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                message="ساختار ورودی ارسال‌شده نامعتبر است با پشتیبانی تماس بگیرید.",
                data=None
            )
        )
    errors = exc.errors()
    messages = []

    for error in errors:
        loc = error.get("loc", [])
        field_name = loc[-1] if loc else "نامشخص"
        err_type = error.get("type", "")
        msg = error.get("msg", "")

        model = getattr(exc, "model", None)

        label = field_name
        if model and hasattr(model, "model_fields"):
            field_info = model.model_fields.get(field_name)
            if field_info:
                label = field_info.alias or field_name  # 👈 استفاده از alias برای پیام فارسی
        if err_type == "missing":
            msg = f"{label} باید ارسال شود"
        else:
            msg = msg.replace("Value error, ", "")

        messages.append(msg)

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=my_response(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            message="؛ ".join(messages),
            data=None
        )
    )

def generate_random_password(length: int = 12) -> str:
    if length < 8:
        raise ValueError("Password length must be at least 8 characters")

    alphabet = (
        string.ascii_lowercase +
        string.ascii_uppercase +
        string.digits
    )

    return ''.join(secrets.choice(alphabet) for _ in range(length))


PERSIAN_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]

def to_jalali_str(dt, include_time: bool = False) -> str:
    # Convert Gregorian datetime to Jalali datetime
    jdate = jdatetime.datetime.fromgregorian(datetime=dt)

    # Build date part in Persian format
    date_part = f"{jdate.day} {PERSIAN_MONTHS[jdate.month - 1]} {jdate.year}"

    # Optionally append time
    if include_time:
        return f"{date_part} {jdate.strftime('%H:%M')}"

    return date_part




def get_current_user(request: Request) -> CurrentUser:
    payload = request.scope.get("user")

    if not payload:
        raise HTTPException(status_code=401, detail="UNAUTHENTICATED")

    userId = payload.get("user_id")
    roles = payload.get("roles", [])

    if not userId or not isinstance(roles, list):
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")

    return CurrentUser(
        userId=userId,
        roles=roles
    )