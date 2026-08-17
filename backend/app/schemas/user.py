
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):


    email: EmailStr = Field(..., description="E-mail do usuário")
    full_name: str = Field(..., min_length=3, max_length=255, description="Nome completo")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Senha do usuário"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not any(c.isalpha() for c in password):
            raise ValueError("A senha deve conter ao menos uma letra.")
        if not any(c.isdigit() for c in password):
            raise ValueError("A senha deve conter ao menos um número.")
        return password


class AdminUserCreate(UserCreate):


    role: UserRole = Field(UserRole.ADMIN, description="Tipo de usuário")


class CustomerUserCreate(UserCreate):


    role: UserRole = Field(UserRole.CUSTOMER, description="Tipo de usuário")


class PasswordResetRequest(BaseModel):


    token: str = Field(..., description="Token de recuperação de senha")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="Nova senha"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, new_password: str) -> str:
        if not any(c.isalpha() for c in new_password):
            raise ValueError("A nova senha deve conter ao menos uma letra.")
        if not any(c.isdigit() for c in new_password):
            raise ValueError("A nova senha deve conter ao menos um número.")
        return new_password


class ForgotPasswordRequest(BaseModel):


    email: EmailStr = Field(..., description="E-mail do usuário")


class ChangePasswordRequest(BaseModel):

    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="Nova senha"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, new_password: str) -> str:
        if not any(c.isalpha() for c in new_password):
            raise ValueError("A nova senha deve conter ao menos uma letra.")
        if not any(c.isdigit() for c in new_password):
            raise ValueError("A nova senha deve conter ao menos um número.")
        return new_password


class UserUpdate(BaseModel):

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8, max_length=128)
    full_name: str | None = Field(None, min_length=3, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str | None) -> str | None:
        if password is None:
            return None
        if not any(c.isalpha() for c in password):
            raise ValueError("A senha deve conter ao menos uma letra.")
        if not any(c.isdigit() for c in password):
            raise ValueError("A senha deve conter ao menos um número.")
        return password


class UserResponse(BaseModel):


    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
