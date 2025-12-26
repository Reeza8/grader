from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from User.Schema.UserSchema import LoginRequest, LoginResponse, VerifyCodeRequest, VerifyCodeResponse
from User.Application.login_with_otp import LoginWithOTPUseCase
from User.Application.verify_login_code import VerifyLoginCodeUseCase
from User.Application.login_password import LoginPasswordUseCase
from User.Application.add_user import AddUserUseCase
from User.Application.reset_password import ResetPasswordUseCase
from User.Application.edit_password import EditPasswordUseCase
from User.Application.refresh_access_token import RefreshAccessTokenUseCase

from db import get_async_session
from User.models import User
from User.Schema.UserSchema import (
    EditPasswordRequest, EditPasswordResponse,
    EditNameRequest, EditNameResponse,
    LoginPasswordRequest, LoginPasswordResponse,
    AddUserRequest, AddUserResponse, ResetPasswordRequest,ResetPasswordResponse,
    GetMyProfileResponse
)

from utils.jwt import create_access_token, create_refresh_token
from utils.utils import my_response, generate_random_password, get_current_user
from utils.utils import to_jalali_str


router = APIRouter(prefix='/userApi', tags=["Auth"])

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# @router.post("/login/")
# async def login(
#     login_data: LoginRequest,
#     session: AsyncSession = Depends(get_async_session)
# ):
#     index = login_data.index.strip()
#     role = login_data.role
#
#     is_phone = is_valid_phone(index)
#     is_email = is_valid_email(index)
#
#     if not is_phone and not is_email:
#         raise HTTPException(status_code=400, detail="فرمت ورودی نامعتبر است")
#
#     latest_code_query = (
#         select(VerifyCode)
#         .where(VerifyCode.index == index)
#         .order_by(VerifyCode.created_at.desc())
#         .limit(1)
#     )
#     result = await session.execute(latest_code_query)
#     recent_code = result.scalar_one_or_none()
#
#     if recent_code and recent_code.created_at > datetime.utcnow() - timedelta(minutes=2):
#         raise HTTPException(status_code=429, detail="لطفاً تا ۲ دقیقه دیگر دوباره تلاش کنید")
#
#     user_query = select(User).where(
#         User.phone_number == index if is_phone else User.email == index
#     )
#     result = await session.execute(user_query)
#     user = result.scalar_one_or_none()
#
#     if not user:
#         user_data = {
#             "name": index,
#             "password_hash": "",
#             "role": role,  # Role is set only on creation
#         }
#
#         if is_phone:
#             user_data["phone_number"] = index
#         else:
#             user_data["email"] = index
#
#         user = User(**user_data)
#         session.add(user)
#         await session.flush()
#     else:
#         # Role mismatch check
#         if user.role != role:
#             raise HTTPException(
#                 status_code=403,
#                 detail="نقش کاربر با اطلاعات ثبت‌شده مطابقت ندارد"
#             )
#
#     code = f"{random.randint(100000, 999999)}"
#     print(code)
#     verify_code = VerifyCode(index=index, code=code, user_id=user.id)
#     session.add(verify_code)
#     await session.commit()
#
#     return my_response(
#         status_code=200,
#         message="لطفا کد تایید ارسال شده را وارد کنید",
#         data=LoginResponse(index=index)
#     )


@router.post("/login/")
async def login(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    usecase = LoginWithOTPUseCase(session)

    try:
        index = await usecase.execute(
            login_data.index,
            login_data.role
        )
    except ValueError as e:
        error_map = {
            "INVALID_INDEX": (400, "فرمت ورودی نامعتبر است"),
            "RATE_LIMIT": (429, "لطفاً تا ۲ دقیقه دیگر دوباره تلاش کنید"),
            "ROLE_MISMATCH": (403, "نقش کاربر با اطلاعات ثبت‌شده مطابقت ندارد"),
        }
        status, message = error_map[str(e)]
        raise HTTPException(status_code=status, detail=message)

    return my_response(
        status_code=200,
        message="لطفا کد تایید ارسال شده را وارد کنید",
        data=LoginResponse(index=index)
    )


# @router.post("/verifyCodeLogin/")
# async def verify_code_login(
#     request_data: VerifyCodeRequest,
#     session: AsyncSession = Depends(get_async_session)
# ):
#     index = request_data.index.strip()
#     input_code = request_data.code.strip()
#
#     is_phone = is_valid_phone(index)
#     is_email = is_valid_email(index)
#
#     if not is_phone and not is_email:
#         raise HTTPException(status_code=400, detail="فرمت ورودی نامعتبر است")
#
#     user_query = select(User).where(
#         User.phone_number == index if is_phone else User.email == index
#     )
#     result = await session.execute(user_query)
#     user = result.scalar_one_or_none()
#
#     if not user:
#         raise HTTPException(status_code=404, detail="کاربری با این اطلاعات یافت نشد")
#
#     code_query = select(VerifyCode).where(
#         VerifyCode.user_id == user.id
#     ).order_by(
#         VerifyCode.created_at.desc()
#     ).limit(1)
#     result = await session.execute(code_query)
#     verify_code = result.scalar_one_or_none()
#
#     if not verify_code:
#         raise HTTPException(status_code=404, detail="کد تأیید برای این کاربر یافت نشد")
#
#     if verify_code.code != input_code:
#         raise HTTPException(status_code=400, detail="کد تأیید اشتباه است")
#
#     if verify_code.isUsed or verify_code.created_at < datetime.utcnow() - timedelta(minutes=2):
#         raise HTTPException(status_code=400, detail="کد تأیید منقضی شده یا قبلاً استفاده شده است")
#
#     verify_code.isUsed = True
#     await session.commit()
#     name = user.name or "admin"
#     token = create_access_token(user.id, name, user.role.value)
#
#     res_data = VerifyCodeResponse(
#         token=token,
#         index=index,
#     )
#
#     return my_response(
#         status_code=200,
#         message="با موفقیت وارد شدید",
#         data=res_data
#     )

@router.post("/verifyCodeLogin/")
async def verify_code_login(
    request_data: VerifyCodeRequest,
    session: AsyncSession = Depends(get_async_session)
):
    useCase = VerifyLoginCodeUseCase(session)

    try:
        result = await useCase.execute(
            request_data.index,
            request_data.code
        )
    except ValueError as e:
        error_map = {
            "INVALID_INDEX": (400, "فرمت ورودی نامعتبر است"),
            "USER_NOT_FOUND": (404, "کاربری با این اطلاعات یافت نشد"),
            "CODE_NOT_FOUND": (404, "کد تأیید برای این کاربر یافت نشد"),
            "INVALID_CODE": (400, "کد تأیید اشتباه است"),
            "CODE_EXPIRED": (400, "کد تأیید منقضی شده یا قبلاً استفاده شده است"),
        }

        status, message = error_map[str(e)]
        raise HTTPException(status_code=status, detail=message)

    return my_response(
        status_code=200,
        message="با موفقیت وارد شدید",
        data=VerifyCodeResponse(
            token=result["token"],
            index=result["index"]
        )
    )


# @router.put("/editPassword/")
# async def edit_password(
#     request: Request,
#     request_data: EditPasswordRequest,
#     session: AsyncSession = Depends(get_async_session)
# ):
#     current_user = request.scope.get("user")
#     user_id = current_user["user_id"]
#
#     result = await session.execute(select(User).where(User.id == user_id))
#     db_user = result.scalar_one_or_none()
#
#     if not db_user:
#         raise HTTPException(status_code=404, detail="کاربر یافت نشد")
#
#     if db_user.password_hash:
#         if not request_data.previousPassword:
#             raise HTTPException(status_code=400, detail="رمز عبور قبلی باید ارسال شود")
#
#         if not pwd_context.verify(request_data.previousPassword, db_user.password_hash):
#             raise HTTPException(status_code=400, detail="رمز عبور پیشین اشتباه است")
#
#     db_user.password_hash = pwd_context.hash(request_data.password)
#     await session.commit()
#
#     res_data = EditPasswordResponse(
#         name=db_user.name,
#         user_id=db_user.id    )
#
#     return my_response(200, "رمز عبور با موفقیت ویرایش شد", res_data)

@router.put("/editPassword/")
async def edit_password(
    request: Request,
    request_data: EditPasswordRequest,
    session: AsyncSession = Depends(get_async_session)
):
    currentUser = request.scope.get("user")
    userId = currentUser["user_id"]

    useCase = EditPasswordUseCase(
        session=session,
    )

    try:
        result = await useCase.execute(
            userId=userId,
            newPassword=request_data.password,
            previousPassword=request_data.previousPassword
        )
    except ValueError as e:
        errorMap = {
            "USER_NOT_FOUND": (404, "کاربر یافت نشد"),
            "PREVIOUS_PASSWORD_REQUIRED": (400, "رمز عبور قبلی باید ارسال شود"),
            "INVALID_PREVIOUS_PASSWORD": (400, "رمز عبور قبلی نادرست است"),
            "PASSWORD_TOO_SHORT": (400, "رمز عبور باید حداقل ۸ کاراکتر باشد"),
        }

        status, message = errorMap.get(
            str(e),
            (400, "خطای نامشخص")
        )
        raise HTTPException(status_code=status, detail=message)

    return my_response(
        status_code=200,
        message="رمز عبور با موفقیت ویرایش شد",
        data=EditPasswordResponse(
            user_id=result["user_id"],
            name=result["name"]
        )
    )


# no need for usecase, simple CRUD
@router.put("/editName/")
async def edit_username(
    request: Request,
    request_data: EditNameRequest,
    session: AsyncSession = Depends(get_async_session)
):
    currentUser = request.scope["user"]
    userId = currentUser["user_id"]

    result = await session.execute(
        select(User).where(User.id == userId)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")

    user.name = request_data.name.strip()
    await session.commit()

    return my_response(
        200,
        "نام با موفقیت ویرایش شد",
        EditNameResponse(
            name=user.name,
            user_id=user.id
        )
    )


@router.post("/loginPassword/")
async def login_password(
    request_data: LoginPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
):
    useCase = LoginPasswordUseCase(
        session=session,
        tokenService={
            "access": create_access_token,
            "refresh": create_refresh_token,
        }
    )

    try:
        result = await useCase.execute(
            request_data.index,
            request_data.password
        )
    except ValueError as e:
        errorMap = {
            "INVALID_INDEX": (400, "فرمت ورودی نامعتبر است"),
            "USER_NOT_FOUND": (404, "کاربر یافت نشد"),
            "PASSWORD_NOT_SET": (400, "رمز عبور تنظیم نشده است"),
            "INVALID_PASSWORD": (400, "رمز عبور اشتباه است"),
            "NO_ACTIVE_ROLE": (403, "کاربر نقش فعالی ندارد"),
        }
        status, message = errorMap[str(e)]
        raise HTTPException(status_code=status, detail=message)

    response = my_response(
        200,
        "ورود موفق",
        {
            "access_token": result["access_token"],
            "index": result["index"],
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return response



# @router.post("/resetPassword/", response_model=ResetPasswordResponse)
# async def reset_password(
#     request: Request,
#     request_data: ResetPasswordRequest,
#     session: AsyncSession = Depends(get_async_session)
# ):
#     current_user = request.scope["user"]
#     user_id = current_user["user_id"]
#
#     index = request_data.index.strip()
#     is_phone = is_valid_phone(index)
#     is_email = is_valid_email(index)
#
#     if not is_phone and not is_email:
#         raise HTTPException(status_code=400, detail="فرمت ورودی نامعتبر است")
#
#     result = await session.execute(select(User).where(User.id == user_id))
#     db_user = result.scalar_one_or_none()
#
#     if not db_user:
#         raise HTTPException(status_code=404, detail="کاربر یافت نشد")
#
#     new_password = generate_random_password()
#
#     if is_email:
#         if not db_user.email:
#             raise HTTPException(status_code=400, detail="آدرس ایمیل ثبت نشده است")
#         if db_user.email != index:
#             raise HTTPException(status_code=400, detail="ایمیل وارد شده نادرست است")
#
#     elif is_phone:
#         if not db_user.phone_number:
#             raise HTTPException(status_code=400, detail="شماره تلفن ثبت نشده است")
#         if db_user.phone_number != index:
#             raise HTTPException(status_code=400, detail="شماره تلفن وارد شده نادرست است")
#
#     db_user.password_hash = pwd_context.hash(new_password)
#     await session.commit()
#
#     # TODO: ارسال ایمیل یا SMS با new_password
#     # print(new_password)  ← برای تولید واقعی توصیه نمی‌شود.
#
#     res_data = ResetPasswordResponse(user_id=db_user.id, name=db_user.name)
#
#     return my_response(200, "رمز عبور جدید برای شما ارسال شد.", res_data)


@router.post("/resetPassword/")
async def reset_password(
    request: Request,
    request_data: ResetPasswordRequest,
    session: AsyncSession = Depends(get_async_session)
):
    currentUser = request.scope["user"]
    userId = currentUser["user_id"]
    useCase = ResetPasswordUseCase(
        session=session,
        passwordGenerator=generate_random_password
    )

    try:
        result = await useCase.execute(
            userId=userId,
            index=request_data.index
        )
    except ValueError as e:
        errorMap = {
            "INVALID_INDEX": (400, "فرمت ورودی نامعتبر است"),
            "USER_NOT_FOUND": (404, "کاربر یافت نشد"),
            "EMAIL_NOT_SET": (400, "آدرس ایمیل ثبت نشده است"),
            "EMAIL_MISMATCH": (400, "ایمیل وارد شده نادرست است"),
            "PHONE_NOT_SET": (400, "شماره تلفن ثبت نشده است"),
            "PHONE_MISMATCH": (400, "شماره تلفن وارد شده نادرست است"),
        }

        status, message = errorMap[str(e)]
        raise HTTPException(status_code=status, detail=message)

    # TODO: send new password via email or SMS
    # NEVER log the password

    return my_response(
        200,
        "رمز عبور جدید برای شما ارسال شد.",
        ResetPasswordResponse(
            user_id=result["user_id"],
            name=result["name"]
        )
    )


@router.post("/addUser/")
async def add_user(
    request: Request,
    data: AddUserRequest,
    session: AsyncSession = Depends(get_async_session),
):
    useCase = AddUserUseCase(session=session)
    currentUser = request.scope.get("current_user")

    try:
        result = await useCase.execute(
            currentUser=currentUser,
            index=data.index,
            password=data.password,
        )
    except ValueError as e:
        errorMap = {
            "INVALID_INDEX": (400, "فرمت ورودی نامعتبر است"),
            "USER_ALREADY_EXISTS": (400, "کاربر دیگری با اطلاعات ورودی وجود دارد"),
            "ACCESS_DENIED": (403, "دسترسی ندارید"),
        }

        status, message = errorMap.get(str(e), (400, "خطای نامشخص"))
        raise HTTPException(status_code=status, detail=message)

    return my_response(
        status_code=200,
        message="کاربر با موفقیت ایجاد شد",
        data=AddUserResponse(
            id=result["id"],
            index=result["index"],
        ),
    )

@router.get("/getMyProfile/")
async def get_my_profile(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    currentUser = request.scope.get("current_user")
    if not currentUser:
        return my_response(
            401,
            "کاربر احراز هویت نشده است",
            None
        )

    userId = currentUser.userId

    result = await session.execute(
        select(User).where(User.id == userId)
    )
    user = result.scalar_one_or_none()

    if not user:
        return my_response(
            404,
            "کاربر یافت نشد",
            None
        )

    return my_response(
        200,
        "پروفایل با موفقیت برگردانده شد",
        GetMyProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
            created_at=to_jalali_str(user.created_at),
            roles=currentUser.roles
        )
    )


@router.post("/refresh/")
async def refresh_token(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    refreshToken = request.cookies.get("refresh_token")
    if not refreshToken:
        raise HTTPException(status_code=401, detail="REFRESH_TOKEN_MISSING")

    useCase = RefreshAccessTokenUseCase(
        session=session,
        accessTokenService=create_access_token
    )

    try:
        result = await useCase.execute(refreshToken)
    except ValueError as e:
        errorMap = {
            "REFRESH_TOKEN_EXPIRED": (401, "رفرش توکن منقضی شده"),
            "INVALID_REFRESH_TOKEN": (401, "رفرش توکن نامعتبر است"),
            "INVALID_TOKEN_TYPE": (401, "نوع توکن نامعتبر است"),
            "NO_ACTIVE_ROLE": (403, "کاربر نقش فعالی ندارد"),
            "USER_NOT_FOUND": (404, "کاربر یافت نشد"),
            "USER_INACTIVE": (403, "حساب کاربری غیرفعال است"),
        }
        status, message = errorMap[str(e)]
        raise HTTPException(status_code=status, detail=message)

    return my_response(
        200,
        "توکن جدید صادر شد",
        result
    )
