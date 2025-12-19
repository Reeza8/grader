from sqlalchemy import select
from User.models import User
from utils.utils import is_valid_phone, is_valid_email
from passlib.context import CryptContext



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class ResetPasswordUseCase:
    def __init__(self, session, passwordGenerator):
        self.session = session
        self.passwordGenerator = passwordGenerator

    async def execute(self, userId: int, index: str):
        index = index.strip()

        isPhone = is_valid_phone(index)
        isEmail = is_valid_email(index)

        if not isPhone and not isEmail:
            raise ValueError("INVALID_INDEX")

        result = await self.session.execute(
            select(User).where(User.id == userId)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("USER_NOT_FOUND")

        if isEmail:
            if not user.email:
                raise ValueError("EMAIL_NOT_SET")
            if user.email != index:
                raise ValueError("EMAIL_MISMATCH")

        if isPhone:
            if not user.phone_number:
                raise ValueError("PHONE_NOT_SET")
            if user.phone_number != index:
                raise ValueError("PHONE_MISMATCH")

        newPassword = self.passwordGenerator()
        user.password_hash = pwd_context.hash(newPassword)

        await self.session.commit()

        return {
            "user_id": user.id,
            "name": user.name,
            "new_password": newPassword  # فقط برای ارسال (نه log)
        }
