from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class RegisterRequest(BaseModel):


    email: EmailStr = Field(..., description="E-mail do usuário")
    full_name: str = Field(..., min_length=3, max_length=255, description="Nome completo")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Senha com no mínimo 8 caracteres (letra + número)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not any(c.isalpha() for c in password):
            raise ValueError("A senha deve conter ao menos uma letra.")
        if not any(c.isdigit() for c in password):
            raise ValueError("A senha deve conter ao menos um número.")
        return password


class LoginRequest(BaseModel):


    email: EmailStr = Field(..., description="E-mail do usuário")
    password: str = Field(..., description="Senha do usuário")


class TokenResponse(BaseModel):


    access_token: str = Field(..., description="Token JWT de acesso (curta validade)")
    token_type: str = Field(default="bearer", description="Tipo de token")


class AuthResponse(BaseModel):


    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):

    message: str
