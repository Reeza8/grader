from db import engine, Base, get_async_session
from User.Api.UserApi import router as UserAdminRouter
# from Blog.Api.blogApi import router as blogUserRouter
from fastapi import FastAPI, Depends
from middleware.responseMiddleware import ResponseWrapperMiddleware
from middleware.authMiddleware import AuthMiddleware
from utils.utils import http_exception_handler, validation_exception_handler, my_response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



# @app.exception_handler(ValueError)
# async def value_error_exception_handler(request: Request, exc: ValueError):
#     print("aggggggggggggggggggggggggggggggg")
#     return JSONResponse(
#         status_code=400,
#         content={"detail": str(exc)}
#     )


# @app.exception_handler(RequestValidationError)
# async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
#     errors = []
#     print("ddddddddddddd")
#     for error in exc.errors():
#         msg = error.get("msg")
#         if not isinstance(msg, str):
#             msg = str(msg)
#         error["msg"] = msg
#         errors.append(error)
#
#     detail_message = "خطا در اعتبارسنجی ورودی‌ها"
#
#     return JSONResponse(
#         status_code=400,
#         content={
#             "detail": detail_message,
#             "errors": errors
#         }
#     )


app.add_middleware(AuthMiddleware)
app.add_middleware(ResponseWrapperMiddleware)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://aradhesabacc.com",
    "https://www.aradhesabacc.com",
    "https://api.aradhesabacc.com"
]

# اضافه کردن middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # آدرس‌هایی که مجاز هستند
    allow_credentials=True,     # اجازه ارسال کوکی/توکن
    allow_methods=["*"],        # چه متدهایی (GET, POST, PUT, DELETE, ...)
    allow_headers=["*"],        # چه هدرهایی
)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(UserAdminRouter, prefix="/user")
# app.include_router(blogUserRouter, prefix="/blog")


@app.get("/", tags=["Monitoring"])
async def health_check(session: AsyncSession = Depends(get_async_session)):
    health_data = {
        "status": "available",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {}
    }

    # 1. Check database connection
    try:
        await session.execute(text("SELECT 1"))  # استفاده از text() برای کوئری
        health_data["dependencies"]["database"] = {
            "status": "connected",
            "details": "Database connection is healthy"
        }
    except Exception as e:
        health_data["dependencies"]["database"] = {
            "status": "disconnected",
            "error": str(e)
        }
        health_data["status"] = "degraded"

    # 2. Add more checks as needed (cache, external services, etc.)
    # health_data["dependencies"]["cache"] = {...}
    # health_data["dependencies"]["storage"] = {...}

    # Determine overall status code
    status_code = 200 if health_data["status"] == "available" else 503

    return my_response(
        status_code=status_code,
        message="Service health status",
        data=health_data
    )

