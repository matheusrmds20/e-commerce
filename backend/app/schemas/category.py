from pydantic import BaseModel, Field, ConfigDict


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Nome da categoria")
    slug: str = Field(..., min_length=3, max_length=120, description="Slug da categoria")
    image_url: str | None = Field(None, max_length=500, description="URL da imagem da categoria")
    description: str | None = Field(None, max_length=500, description="Descrição da categoria")
    is_active: bool = Field(True, description="Ativo")
    parent_id: int | None = Field(None, description="ID da categoria pai")


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=100)
    slug: str | None = Field(None, min_length=3, max_length=120)
    image_url: str | None = Field(None, max_length=500)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    parent_id: int | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool
    parent_id: int | None

    model_config = ConfigDict(from_attributes=True)
