from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic import BaseModel, field_validator
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
import re


class LoginRequest(BaseModel):
    index: str
    roles: list[str]


class EditStudent(BaseModel):
    id: int
    name: str


class VerifyCodeRequest(BaseModel):
    index: str
    code: str


class EditPasswordRequest(BaseModel):
    password: str
    repeatPassword: str
    previousPassword: Optional[str] = None

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.repeatPassword:
            raise ValueError("رمز عبور و تکرار آن یکسان نیستند.")
        return self


class EditNameRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("نام نمی‌تواند خالی باشد.")
        if len(value) < 3:
            raise ValueError("نام باید حداقل 3 کاراکتر داشته باشد.")
        return value


class LoginPasswordRequest(BaseModel):
    index: str
    password: str

    class Config:
        populate_by_name = True




class ResetPasswordResponse(BaseModel):
    name: str
    user_id: int

class ResetPasswordRequest(BaseModel):
    index: str

class LoginResponse(BaseModel):
    index: str

    class Config:
        from_attributes = True


class VerifyCodeResponse(BaseModel):
    token: str
    index: str


class EditPasswordResponse(BaseModel):
    name: str | None
    user_id: int


class EditNameResponse(BaseModel):
    name: str
    user_id: int


class LoginPasswordResponse(BaseModel):
    token: str
    index: str


class ResetPasswordResponse(BaseModel):
    user_id: int
    name: str


class AddUserRequest(BaseModel):
    index: str
    password: str
    name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        password_regex = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$")
        if not password_regex.match(v):
            raise ValueError("رمز عبور باید حداقل ۸ کاراکتر و شامل حروف و اعداد باشد.")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("نام نمی‌تواند خالی باشد.")
        if len(value) < 3:
            raise ValueError("نام باید حداقل 3 کاراکتر داشته باشد.")
        return value


class AddUserResponse(BaseModel):
    index: str
    id: int


class UserResponse(BaseModel):
    id: int
    name: str | None

class GetMyProfileResponse(BaseModel):
    id: int
    name: str | None
    email: str| None
    phone_number: str| None
    created_at: str
    roles: list[str]

