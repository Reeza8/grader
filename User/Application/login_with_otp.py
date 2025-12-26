from datetime import datetime, timedelta
import random
from sqlalchemy import select
from User.models import User, VerifyCode
from utils.utils import is_valid_phone, is_valid_email


class LoginWithOTPUseCase:
    def __init__(self, session):
        self.session = session

    async def execute(self, index: str, role):
        index = index.strip()

        is_phone = is_valid_phone(index)
        is_email = is_valid_email(index)

        if not is_phone and not is_email:
            raise ValueError("INVALID_INDEX")

        # rate limit
        latest_code_query = (
            select(VerifyCode)
            .where(VerifyCode.index == index)
            .order_by(VerifyCode.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(latest_code_query)
        recent_code = result.scalar_one_or_none()

        if recent_code and recent_code.created_at > datetime.utcnow() - timedelta(minutes=2):
            raise ValueError("RATE_LIMIT")

        # find user
        user_query = select(User).where(
            User.phone_number == index if is_phone else User.email == index
        )
        result = await self.session.execute(user_query)
        user = result.scalar_one_or_none()

        # create user if not exists
        if not user:
            user = User(
                name=index,
                role=role,
                phone_number=index if is_phone else None,
                email=index if is_email else None,
                password_hash=""
            )
            self.session.add(user)
            await self.session.flush()
        else:
            if user.role != role:
                raise ValueError("ROLE_MISMATCH")

        # create verify code
        code = f"{random.randint(100000, 999999)}"
        verify_code = VerifyCode(
            index=index,
            code=code,
            user_id=user.id
        )

        self.session.add(verify_code)
        await self.session.commit()

        return index
