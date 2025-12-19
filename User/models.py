from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    MANAGER = "manager"


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    phone_number = Column(String(13), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    role = Column(Enum(UserRole, name="role"),nullable=False, server_default=UserRole.TEACHER.value )

class VerifyCode(Base):
    __tablename__ = 'verify_code'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(6), unique=True, nullable=False)
    isUsed = Column(Boolean, nullable=False, default=False)
    index = Column(String(256), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship('User', foreign_keys=[user_id])