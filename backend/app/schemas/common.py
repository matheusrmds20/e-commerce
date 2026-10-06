

from typing import Generic, TypeVar

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

    data: list[T]
    meta: PageMeta


class PaginationParams(BaseModel):
    """Parâmetros de paginação usados como query string."""

    page: int = Field(1, ge=1, description="Número da página (começa em 1)")
    per_page: int = Field(20, ge=1, le=100, description="Itens por página (max 100)")



class DependencyHealth(BaseModel):
    """Status de uma dependência checada pelo health check."""

    name: str = Field(..., description="Nome da dependência (ex.: database")
    status: str = Field(..., description="Status da dependência (ok | error")
    detail: str | None = Field(
        None, description="Mensagem de erro/contexto quando não estiver ok"
    )


class HealthResponse(BaseModel):
    """Resposta do endpoint de health check.

    - ``status``: "ok" se a API e todas as dependências responderem; "error"
      caso contrário.
    - ``app``/``version``: identidade da aplicação.
    - ``dependencies``: resultado individual de cada dependência (ex.: banco).
    """

    status: str
    app: str
    version: str
    dependencies: list[DependencyHealth] = Field(
        default_factory=list,
        description="Resultado de cada dependência checada",
    )
