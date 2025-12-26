import jwt
from datetime import datetime
from sqlalchemy import select
from User.models import User, UserRole, Role
from utils.config import settings


class RefreshAccessTokenUseCase:
    def __init__(self, session, accessTokenService):
        self.session = session
        self.accessTokenService = accessTokenService

    async def execute(self, refreshToken: str):
        try:
            payload = jwt.decode(
                refreshToken,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("REFRESH_TOKEN_EXPIRED")
        except jwt.InvalidTokenError:
            raise ValueError("INVALID_REFRESH_TOKEN")

        if payload.get("type") != "refresh":
            raise ValueError("INVALID_TOKEN_TYPE")

        userId = payload.get("user_id")
        if not userId:
            raise ValueError("INVALID_REFRESH_TOKEN")

        user = await self.session.get(User, userId)

        if not user:
            raise ValueError("USER_NOT_FOUND")

        if not user.is_active:
            raise ValueError("USER_INACTIVE")

        rolesQuery = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == userId,
                (UserRole.expire_at.is_(None)) |
                (UserRole.expire_at > datetime.utcnow())
            )
        )
        rolesResult = await self.session.execute(rolesQuery)
        roles = [row[0] for row in rolesResult.all()]

        if not roles:
            raise ValueError("NO_ACTIVE_ROLE")

        user = await self.session.get(User, userId)
        if not user:
            raise ValueError("USER_NOT_FOUND")

        accessToken = self.accessTokenService(
            user_id=user.id,
            name=user.name,
            roles=roles,
        )

        return {
            "access_token": accessToken
        }
