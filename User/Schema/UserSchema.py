from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
import re



class LoginRequest(BaseModel):
    index: str = Field(..., alias="ایمیل یا شماره تلفن", description="index.")

    class Config:
        populate_by_name = True


class EditStudent(BaseModel):
    id: int = Field(..., alias="شناسه دانش‌آموز", description="id.")
    name: str = Field(..., alias="نام دانش‌آموز", description="name.")

    class Config:
        populate_by_name = True


class VerifyCodeRequest(BaseModel):
    index: str = Field(..., alias="ایمیل یا شماره تلفن", description="index.")
    code: str = Field(..., alias="کد تایید", description="code.")

    class Config:
        populate_by_name = True


class EditPasswordRequest(BaseModel):
    password: str = Field(..., alias="رمز عبور جدید", description="password.")
    repeatPassword: str = Field(..., alias="تکرار رمز عبور", description="repeatPassword.")
    previousPassword: Optional[str] = Field(None, alias="رمز عبور پیشین", description="previousPassword.")

    class Config:
        populate_by_name = True

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        password_regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')
        if not password_regex.match(v):
            raise ValueError("رمز عبور باید حداقل ۸ کاراکتر و شامل حروف و اعداد باشد.")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.repeatPassword:
            raise ValueError("رمز عبور و تکرار آن یکسان نیستند.")
        return self


class EditNameRequest(BaseModel):
    name: str = Field(
        ...,
        alias="نام کاربر",
        description="name."
    )

    class Config:
        populate_by_name = True

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
    index: str = Field(..., alias="ایمیل یا شماره تلفن", description="index.")
    password: str = Field(..., alias="رمز عبور", description="password.")

    class Config:
        populate_by_name = True


class ResetPasswordRequest(BaseModel):
    index: str = Field(..., alias="ایمیل یا شماره تلفن", description="index.")

    class Config:
        populate_by_name = True


class LoginResponse(BaseModel):
    index: str

    class Config:
        from_attributes = True


class verifyCodeResponse(BaseModel):
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
    index: str = Field(..., alias="ایمیل یا شماره تلفن", description="index.")
    password: str = Field(..., alias="رمز عبور", description="password.")
    name: Optional[str] = Field(None, alias="نام", description="name.")

    class Config:
        populate_by_name = True

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        password_regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')
        if not password_regex.match(v):
            raise ValueError("رمز عبور باید حداقل ۸ کاراکتر و شامل حروف و اعداد باشد.")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("نام نمی‌تواند خالی باشد.")
        if len(value) < 3:
            raise ValueError("نام باید حداقل 3 کاراکتر داشته باشد.")
        return value


class AddUserResponse(BaseModel):
    index :str
    id: int
    name: str | None
    password: str

    class Config:
        populate_by_name = True

class UserResponse(BaseModel):
    id: int
    name: str | None