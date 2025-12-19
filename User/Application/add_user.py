from sqlalchemy import select
from User.models import User, UserRole
from utils.utils import is_valid_phone, is_valid_email


class AddUserUseCase:
    def __init__(self, session, pwdContext):
        self.session = session
        self.pwdContext = pwdContext

    async def execute(self, index: str, password: str, role: str):
        index = index.strip()

        isPhone = is_valid_phone(index)
        isEmail = is_valid_email(index)

        if not isPhone and not isEmail:
            raise ValueError("INVALID_INDEX")

        userQuery = select(User).where(
            User.phone_number == index if isPhone else User.email == index
        )
        result = await self.session.execute(userQuery)
        existingUser = result.scalar_one_or_none()

        if existingUser:
            raise ValueError("USER_ALREADY_EXISTS")

        try:
            userRole = UserRole(role)
        except ValueError:
            raise ValueError("INVALID_ROLE")

        userData = {
            "name": index,
            "password_hash": self.pwdContext.hash(password),
            "role": userRole,
            "phone_number": index if isPhone else None,
            "email": index if isEmail else None,
        }

        user = User(**userData)
        self.session.add(user)
        await self.session.flush()
        await self.session.commit()

        return {
            "id": user.id,
            "name": user.name,
            "index": index,
            "role": user.role.value,
        }
