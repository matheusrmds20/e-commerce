from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


class ProductCreate(BaseModel):


    category_id: int = Field(description="ID da categoria do produto")
    title: str = Field(..., min_length=3, max_length=255, description="Nome do produto")
    slug: str = Field(..., min_length=3, max_length=300, description="Slug do produto")
    description: str = Field(..., min_length=3, max_length=500, description="Descrição do produto")
    price: float = Field(..., ge=0, description="Preço do produto")
    image_url: str | None = Field(None, max_length=500, description="URL da imagem do produto")
    is_active: bool = Field(True, description="Ativo")
    is_featured: bool = Field(False, description="Destaque")
    is_bestseller: bool = Field(False, description="Melhor vendido")
    author: str = Field(..., min_length=3, max_length=255, description="Autor do produto")
    isbn: str | None = Field(None, max_length=20, description="ISBN do produto")
    publisher: str | None = Field(None, max_length=150, description="Editora do produto")
    publication_year: int | None = Field(None, description="Ano de publicação do produto")
    pages: int | None = Field(None, ge=1, description="Número de páginas do produto")
    language: str | None = Field(None, max_length=50, description="Idioma do produto")
    synopsis: str | None = Field(None, max_length=500, description="Sinopse do produto")
    discount_pct: int | None = Field(None, ge=0, le=100, description="Percentual de desconto")
    stock_qty: int = Field(..., ge=0, description="Quantidade de estoque do produto")

    @field_validator("price")
    @classmethod
    def validate_price(cls, price: float) -> float:
        if price < 0:
            raise ValueError("O preço deve ser positivo.")
        return price


class ProductUpdate(BaseModel):


    category_id: int | None = None
    title: str | None = Field(None, min_length=3, max_length=255)
    slug: str | None = Field(None, min_length=3, max_length=300)
    description: str | None = Field(None, min_length=3, max_length=500)
    price: float | None = Field(None, ge=0)
    image_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    is_featured: bool | None = None
    is_bestseller: bool | None = None
    author: str | None = Field(None, min_length=3, max_length=255)
    isbn: str | None = Field(None, max_length=20)
    publisher: str | None = Field(None, max_length=150)
    publication_year: int | None = Field(None, ge=1000, le=2100)
    pages: int | None = Field(None, ge=1)
    language: str | None = Field(None, max_length=50)
    synopsis: str | None = Field(None, max_length=500)
    discount_pct: int | None = Field(None, ge=0, le=100)
    stock_qty: int | None = Field(None, ge=0)


class ProductResponse(BaseModel):
    id: int
    category_id: int
    title: str
    slug: str
    description: str
    price: float
    image_url: str | None
    is_active: bool
    # Defaults para manter o contrato retrocompatível: payloads que ainda não
    # enviam as flags de curadoria continuam válidos (produto sem destaque).
    is_featured: bool = False
    is_bestseller: bool = False
    author: str
    isbn: str | None
    publisher: str | None
    publication_year: int | None
    pages: int | None
    language: str | None
    synopsis: str | None
    discount_pct: int | None
    stock_qty: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
