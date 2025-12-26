from sqlalchemy import select
from datetime import datetime
from User.models import User, UserRole, Role
from utils.utils import is_valid_email, is_valid_phone
from utils.utils import pwd_context


class LoginPasswordUseCase:
    def __init__(self, session, tokenService):
        self.session = session
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

        if not pwd_context.verify(rawPassword, user.password_hash):
            raise ValueError("INVALID_PASSWORD")

        rolesQuery = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user.id,
                (UserRole.expire_at.is_(None)) | (UserRole.expire_at > datetime.utcnow())
            )
        )
        rolesResult = await self.session.execute(rolesQuery)
        roles = [row[0] for row in rolesResult.all()]

        # if not roles:
        #     raise ValueError("NO_ACTIVE_ROLE")

        accessToken = self.tokenService["access"](
            user_id=user.id,
            name=user.name,
            roles=roles,
        )

        refreshToken = self.tokenService["refresh"](
            user_id=user.id
        )

        return {
            "access_token": accessToken,
            "refresh_token": refreshToken,
            "index": index,
        }
