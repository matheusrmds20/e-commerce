

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageMeta(BaseModel):
    """Metadados de paginação de uma listagem."""

    page: int = Field(..., description="Página atual (1-indexed)")
    per_page: int = Field(..., description="Quantidade de itens por página")
    total: int = Field(..., description="Total de itens")
    total_pages: int = Field(..., description="Total de páginas")


class Page(BaseModel, Generic[T]):
    """Envelope de paginação padrão.

    Exemplo de resposta:
    ```json
    {
        "data": [...],
        "meta": {
            "page": 1,
            "per_page": 20,
            "total": 150,
            "total_pages": 8
        }
    }
    ```
    """

    data: List[T]
    meta: PageMeta


class PaginationParams(BaseModel):
    """Parâmetros de paginação usados como query string."""

    page: int = Field(1, ge=1, description="Número da página (começa em 1)")
    per_page: int = Field(20, ge=1, le=100, description="Itens por página (max 100)")



class HealthResponse(BaseModel):
    """Resposta do endpoint de health check."""

    status: str
    app: str
    version: str