from datetime import datetime, timedelta
from sqlalchemy import select
from User.models import User, VerifyCode
from utils.utils import is_valid_phone, is_valid_email
from utils.jwt import create_access_token


class VerifyLoginCodeUseCase:
    def __init__(self, session):
        self.session = session

    async def execute(self, index: str, input_code: str):
        index = index.strip()
        input_code = input_code.strip()

        is_phone = is_valid_phone(index)
        is_email = is_valid_email(index)

        if not is_phone and not is_email:
            raise ValueError("INVALID_INDEX")

        user_query = select(User).where(
            User.phone_number == index if is_phone else User.email == index
        )
        result = await self.session.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("USER_NOT_FOUND")

        code_query = (
            select(VerifyCode)
            .where(VerifyCode.user_id == user.id)
            .order_by(VerifyCode.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(code_query)
        verify_code = result.scalar_one_or_none()

        if not verify_code:
            raise ValueError("CODE_NOT_FOUND")

        if verify_code.code != input_code:
            raise ValueError("INVALID_CODE")

        if verify_code.isUsed or verify_code.created_at < datetime.utcnow() - timedelta(minutes=2):
            raise ValueError("CODE_EXPIRED")

        verify_code.isUsed = True
        await self.session.commit()

        name = user.name or "admin"
        token = create_access_token(
            user.id,
            name,
            user.role.value
        )

        return {
            "token": token,
            "index": index
        }
