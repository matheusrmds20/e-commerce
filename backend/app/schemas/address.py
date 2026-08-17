from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class AddressCreate(BaseModel):

    user_id: int = Field(..., description="ID do usuário")
    street: str = Field(..., min_length=1, max_length=255, description="Logradouro")
    number: str = Field(..., min_length=1, max_length=20, description="Número")
    complement: str | None = Field(None, max_length=100, description="Complemento")
    neighborhood: str = Field(..., min_length=1, max_length=150, description="Bairro")
    city: str = Field(..., min_length=1, max_length=150, description="Cidade")
    state: str = Field(..., min_length=2, max_length=2, description="UF (2 letras)")
    zip_code: str = Field(..., min_length=8, max_length=9, description="CEP")
    is_default: bool = Field(False, description="Endereço padrão")


class AddressUpdate(BaseModel):


    street: str | None = Field(None, min_length=1, max_length=255, description="Logradouro")
    number: str | None = Field(None, min_length=1, max_length=20, description="Número")
    complement: str | None = Field(None, max_length=100, description="Complemento")
    neighborhood: str | None = Field(None, min_length=1, max_length=150, description="Bairro")
    city: str | None = Field(None, min_length=1, max_length=150, description="Cidade")
    state: str | None = Field(None, min_length=2, max_length=2, description="UF (2 letras)")
    zip_code: str | None = Field(None, min_length=8, max_length=9, description="CEP")
    is_default: bool | None = Field(None, description="Endereço padrão")


class AddressResponse(BaseModel):



    id: int
    user_id: int
    street: str
    number: str
    complement: str | None
    neighborhood: str
    city: str
    state: str
    zip_code: str
    is_default: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)