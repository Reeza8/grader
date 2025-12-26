from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    phone_number = Column(String(13), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, nullable=False, server_default="true")

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    assigned_at = Column(DateTime, server_default=func.now())
    expire_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("UserRole", back_populates="role")


class VerifyCode(Base):
    __tablename__ = 'verify_code'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(6), nullable=False)
    isUsed = Column(Boolean, nullable=False, default=False)
    index = Column(String(256), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now(), nullable=False)

    user = relationship('User', foreign_keys=[user_id])