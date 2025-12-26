from sqlalchemy import select
from User.models import User
from passlib.context import CryptContext
from utils.utils import pwd_context




class EditPasswordUseCase:
    def __init__(self, session):
        self.session = session

    async def execute(
        self,
        userId: int,
        newPassword: str,
        previousPassword: str | None = None
    ):
        # business rule: minimum password length
        if len(newPassword) < 8:
            raise ValueError("PASSWORD_TOO_SHORT")

        result = await self.session.execute(
            select(User).where(User.id == userId)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("USER_NOT_FOUND")

        # if user already has a password, previous password is required
        if user.password_hash:
            if not previousPassword:
                raise ValueError("PREVIOUS_PASSWORD_REQUIRED")

            if not pwd_context.verify(previousPassword, user.password_hash):
                raise ValueError("INVALID_PREVIOUS_PASSWORD")

        # set new password
        user.password_hash = pwd_context.hash(newPassword)
        await self.session.commit()

        return {
            "user_id": user.id,
            "name": user.name
        }