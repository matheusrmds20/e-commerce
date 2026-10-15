

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


    data: list[T]
    meta: PageMeta


class PaginationParams(BaseModel):


    page: int = Field(1, ge=1, description="Número da página (começa em 1)")
    per_page: int = Field(20, ge=1, le=100, description="Itens por página (max 100)")



class DependencyHealth(BaseModel):


    name: str = Field(..., description="Nome da dependência (ex.: database")
    status: str = Field(..., description="Status da dependência (ok | error")
    detail: str | None = Field(
        None, description="Mensagem de erro/contexto quando não estiver ok"
    )


class HealthResponse(BaseModel):

    status: str
    app: str
    version: str
    dependencies: list[DependencyHealth] = Field(
        default_factory=list,
        description="Resultado de cada dependência checada",
    )


def montar_pagina(data: list, page: int, per_page: int, total: int) -> dict:

    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        "data": data,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }
