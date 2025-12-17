from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from passlib.context import CryptContext
import random
from User.Schema.UserSchema import LoginRequest, LoginResponse, VerifyCodeRequest, verifyCodeResponse
from db import get_async_session
from User.models import User, VerifyCode
from User.Schema.UserSchema import (
    EditPasswordRequest, EditPasswordResponse,
    EditNameRequest, EditNameResponse,
    LoginPasswordRequest, LoginPasswordResponse,
    AddUserRequest, AddUserResponse
)
from utils.jwt import create_access_token
from utils.utils import my_response, is_valid_email, is_valid_phone


router = APIRouter(prefix='/userApi', tags=["Auth"])

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@router.post("/login/")
async def login(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    index = login_data.index.strip()

    is_phone = is_valid_phone(index)
    is_email = is_valid_email(index)

    if not is_phone and not is_email:
        raise HTTPException(status_code=400, detail="فرمت ورودی نامعتبر است")

    # بررسی محدودیت 2 دقیقه‌ای
    latest_code_query = select(VerifyCode).where(
        VerifyCode.index == index
    ).order_by(
        VerifyCode.createdAt.desc()
    ).limit(1)
    result = await session.execute(latest_code_query)
    recent_code = result.scalar_one_or_none()

    if recent_code and recent_code.createdAt > datetime.utcnow() - timedelta(minutes=2):
        raise HTTPException(status_code=429, detail="لطفاً تا ۲ دقیقه دیگر دوباره تلاش کنید")

    # ساخت یا گرفتن کاربر
    user_query = select(User).where(
        User.phone_number == index if is_phone else User.email == index
    )
    result = await session.execute(user_query)
    user = result.scalar_one_or_none()

    if not user:
        user_data = {"name": index, "password_hash": ""}
        if is_phone:
            user_data["phone_number"] = index
        else:
            user_data["email"] = index

        user = User(**user_data)
        session.add(user)
        await session.flush()

        # TODO: ارسال پیامک یا ایمیل با index و code و flowCode=2

    code = f"{random.randint(100000, 999999)}"
    verify_code = VerifyCode(index=index, code=code, user_id=user.id)
    session.add(verify_code)
    await session.commit()

    res_data = LoginResponse(index=index)

    return my_response(
        status_code=200,
        message="لطفا کد تایید ارسال شده را وارد کنید",
        data=res_data
    )


@router.post("/verifyCodeLogin/")
async def verify_code_login(
    request_data: VerifyCodeRequest,
    session: AsyncSession = Depends(get_async_session)
):
    index = request_data.index.strip()
    input_code = request_data.code.strip()

    is_phone = is_valid_phone(index)
    is_email = is_valid_email(index)

    if not is_phone and not is_email:
        raise HTTPException(status_code=400, detail="فرمت ورودی نامعتبر است")

    user_query = select(User).where(
        User.phone_number == index if is_phone else User.email == index
    )
    result = await session.execute(user_query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="کاربری با این اطلاعات یافت نشد")

    code_query = select(VerifyCode).where(
        VerifyCode.user_id == user.id
    ).order_by(
        VerifyCode.createdAt.desc()
    ).limit(1)
    result = await session.execute(code_query)
    verify_code = result.scalar_one_or_none()

    if not verify_code:
        raise HTTPException(status_code=404, detail="کد تأیید برای این کاربر یافت نشد")

    if verify_code.code != input_code:
        raise HTTPException(status_code=400, detail="کد تأیید اشتباه است")

    if verify_code.isUsed or verify_code.createdAt < datetime.utcnow() - timedelta(minutes=2):
        raise HTTPException(status_code=400, detail="کد تأیید منقضی شده یا قبلاً استفاده شده است")

    verify_code.isUsed = True
    await session.commit()
    name = user.name or "admin"
    token = create_access_token(user.id, name)

    res_data = verifyCodeResponse(
        token=token,
        index=index,
    )

    return my_response(
        status_code=200,
        message="با موفقیت وارد شدید",
        data=res_data
    )


@router.put("/editPassword/")
async def edit_password(
    request: Request,
    request_data: EditPasswordRequest,
    session: AsyncSession = Depends(get_async_session)
):
    current_user = request.scope.get("user")
    user_id = current_user["user_id"]

    result = await session.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")

    if db_user.password_hash:
        if not request_data.previousPassword:
            raise HTTPException(status_code=400, detail="رمز عبور قبلی باید ارسال شود")

        if not pwd_context.verify(request_data.previousPassword, db_user.password_hash):
            raise HTTPException(status_code=400, detail="رمز عبور پیشین اشتباه است")

    db_user.password_hash = pwd_context.hash(request_data.password)
    await session.commit()

    res_data = EditPasswordResponse(
        name=db_user.name,
        user_id=db_user.id    )

    return my_response(200, "رمز عبور با موفقیت ویرایش شد", res_data)


@router.put("/editName/")
async def edit_name(
    request: Request,
    request_data: EditNameRequest,
    session: AsyncSession = Depends(get_async_session)
):
    current_user = request.scope["user"]
    user_id = current_user["user_id"]

    result = await session.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")

    db_user.name = request_data.name.strip()
    await session.commit()

    res_data = EditNameResponse(
        name=db_user.name,
        user_id=db_user.id,
    )

    return my_response(200, "نام با موفقیت ویرایش شد", res_data)


@router.post("/loginPassword/")
async def login_password(
    request_data: LoginPasswordRequest,
    session: AsyncSession = Depends(get_async_session)
):
    index = request_data.index.strip()
    raw_password = request_data.password.strip()

    is_phone = is_valid_phone(index)
    is_email = is_valid_email(index)

    if not is_phone and not is_email:
        raise HTTPException(status_code=400, detail="فرمت ورودی نامعتبر است")

    query = select(User).where(User.phone_number == index) if is_phone else select(User).where(User.email == index)
    result = await session.execute(query)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")

    if not pwd_context.verify(raw_password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="رمز عبور اشتباه است")

    token = create_access_token(db_user.id,  db_user.name)

    res_data = LoginPasswordResponse(token=token, index=index)

    return my_response(200, "ورود توسط رمز عبور با موفقیت انجام شد", res_data)


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


@router.post("/addUser/")
async def add_user(
        data : AddUserRequest,
        session: AsyncSession = Depends(get_async_session)
):
    index = data.index.strip()

    is_phone = is_valid_phone(index)
    is_email = is_valid_email(index)

    if not is_phone and not is_email:
        raise HTTPException(status_code=400, detail="فرمت ورودی نامعتبر است")

    user_query = select(User).where(
        User.phone_number == index if is_phone else User.email == index ,
    )
    result = await session.execute(user_query)
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(status_code=400, detail="کاربر دیگری با اطلاعات ورودی وجود دارد")

    user_data = {"name": index, "password_hash": pwd_context.hash(data.password)}
    if is_phone:
        user_data["phone_number"] = index
    else:
        user_data["email"] = index

    user = User(**user_data)
    session.add(user)
    await session.flush()
    await session.commit()

    res_data = AddUserResponse(
        name=data.name,
        id=user.id,
        password= data.password,
        index=data.index
    )

    return my_response(
        status_code=200,
        message="کاربر با موفقیت ایجاد شد",
        data=res_data
    )