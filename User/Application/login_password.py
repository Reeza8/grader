from sqlalchemy import select
from User.models import User
from utils.utils import is_valid_email, is_valid_phone


class LoginPasswordUseCase:
    def __init__(self, session, pwdContext, tokenService):
        self.session = session
        self.pwdContext = pwdContext
        self.tokenService = tokenService

    async def execute(self, index: str, rawPassword: str):
        index = index.strip()
        rawPassword = rawPassword.strip()

        isPhone = is_valid_phone(index)
        isEmail = is_valid_email(index)

        if not isPhone and not isEmail:
            raise ValueError("INVALID_INDEX")

        query = (
            select(User).where(User.phone_number == index)
            if isPhone
            else select(User).where(User.email == index)
        )

        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("USER_NOT_FOUND")

        if not user.password_hash:
            raise ValueError("PASSWORD_NOT_SET")

        if not self.pwdContext.verify(rawPassword, user.password_hash):
            raise ValueError("INVALID_PASSWORD")

        token = self.tokenService(
            user.id,
            user.name,
            user.role.value
        )

        return {
            "token": token,
            "index": index
        }
