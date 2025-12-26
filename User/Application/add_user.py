from sqlalchemy import select
from utils.utils import is_valid_phone, is_valid_email
from User.models import User, Role, UserRole
from passlib.context import CryptContext



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AddUserUseCase:
    def __init__(self, session):
        self.session = session

    async def execute(self, currentUser, index: str, password: str):
        # if not currentUser.hasRole("admin"):
        #     raise ValueError("ACCESS_DENIED")

        index = index.strip()

        isPhone = is_valid_phone(index)
        isEmail = is_valid_email(index)

        if not isPhone and not isEmail:
            raise ValueError("INVALID_INDEX")

        result = await self.session.execute(
            select(User).where(
                User.phone_number == index if isPhone else User.email == index
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("USER_ALREADY_EXISTS")

        user = User(
            name=index,
            phone_number=index if isPhone else None,
            email=index if isEmail else None,
            password_hash=pwd_context.hash(password),
        )

        self.session.add(user)
        await self.session.commit()

        return {
            "id": user.id,
            "index": index,
        }