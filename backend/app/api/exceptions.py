"""Hierarquia de exceções da aplicação.

Estratégia:
- `BookCommerceException` é a base de todas as exceções conhecidas.
- Cada subclasse define um status_code e um código de erro padrão.
- Os handlers globais convertem essas exceções em respostas JSON
  padronizadas, garantindo consistência na API.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class BookCommerceException(Exception):
    """Exceção base da aplicação.

    Attributes:
        message: Mensagem de erro legível para o usuário.
        code: Código de erro interno (ex: 'EMAIL_ALREADY_EXISTS').
        status_code: Status HTTP a ser retornado.
    """

    def __init__(
        self,
        message: str,
        code: str = "BOOKCOMMERCE_ERROR",
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        """Converte a exceção em dicionário para resposta JSON."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }


# ---------------------------------------------------------------------------
# 400 - Bad Request
# ---------------------------------------------------------------------------


class BadRequestException(BookCommerceException):
    """Requisição malformada. O cliente deve corrigir e tentar novamente."""

    def __init__(self, message: str, code: str = "BAD_REQUEST") -> None:
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST)


class EmptyCartException(BadRequestException):
    """O carrinho está vazio e não pode ser usado no checkout."""

    def __init__(self) -> None:
        super().__init__("O carrinho está vazio.", code="EMPTY_CART")


class InvalidCouponException(BadRequestException):
    """O cupom informado é inválido, expirado ou não aplicável."""

    def __init__(self, message: str = "Cupom inválido ou expirado.") -> None:
        super().__init__(message, code="INVALID_COUPON")


class InvalidStateTransitionException(BadRequestException):
    """Transição de status inválida para pedidos."""

    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            f"Não é possível alterar o status de '{current}' para '{target}'.",
            code="INVALID_STATE_TRANSITION",
        )


# ---------------------------------------------------------------------------
# 401 - Unauthorized (autenticação)
# ---------------------------------------------------------------------------


class UnauthorizedException(BookCommerceException):
    """Credenciais ausentes, inválidas ou expiradas."""

    def __init__(self, message: str = "Não autenticado.", code: str = "UNAUTHORIZED") -> None:
        super().__init__(message, code, status.HTTP_401_UNAUTHORIZED)


class InvalidCredentialsException(UnauthorizedException):
    """E-mail ou senha incorretos."""

    def __init__(self) -> None:
        super().__init__("E-mail ou senha inválidos.", code="INVALID_CREDENTIALS")


class TokenExpiredException(UnauthorizedException):
    """Token JWT expirado."""

    def __init__(self) -> None:
        super().__init__("Sessão expirada. Faça login novamente.", code="TOKEN_EXPIRED")


class InvalidTokenException(UnauthorizedException):
    """Token JWT malformado ou inválido."""

    def __init__(self) -> None:
        super().__init__("Token inválido.", code="INVALID_TOKEN")


# ---------------------------------------------------------------------------
# 403 - Forbidden (autorização)
# ---------------------------------------------------------------------------


class ForbiddenException(BookCommerceException):
    """Usuário autenticado mas sem permissão para o recurso."""

    def __init__(self, message: str = "Acesso negado.", code: str = "FORBIDDEN") -> None:
        super().__init__(message, code, status.HTTP_403_FORBIDDEN)


class InsufficientPermissionException(ForbiddenException):
    """Usuário não possui o papel necessário."""

    def __init__(self) -> None:
        super().__init__(
            "Acesso restrito a administradores.", code="INSUFFICIENT_PERMISSION"
        )


class InactiveUserException(ForbiddenException):
    """Usuário desativado tenta acessar o sistema."""

    def __init__(self) -> None:
        super().__init__("Usuário desativado.", code="INACTIVE_USER")


# ---------------------------------------------------------------------------
# 404 - Not Found
# ---------------------------------------------------------------------------


class NotFoundException(BookCommerceException):
    """Recurso não encontrado."""

    def __init__(self, message: str = "Recurso não encontrado.", code: str = "NOT_FOUND") -> None:
        super().__init__(message, code, status.HTTP_404_NOT_FOUND)


class UserNotFoundException(NotFoundException):
    """Usuário não encontrado no banco."""

    def __init__(self, user_id: str | None = None) -> None:
        msg = f"Usuário '{user_id}' não encontrado." if user_id else "Usuário não encontrado."
        super().__init__(msg, code="USER_NOT_FOUND")


class ProductNotFoundException(NotFoundException):
    """Produto não encontrado no banco."""

    def __init__(self) -> None:
        super().__init__("Produto não encontrado.", code="PRODUCT_NOT_FOUND")


class CategoryNotFoundException(NotFoundException):
    """Categoria não encontrada no banco."""

    def __init__(self) -> None:
        super().__init__("Categoria não encontrada.", code="CATEGORY_NOT_FOUND")


class OrderNotFoundException(NotFoundException):
    """Pedido não encontrado no banco."""

    def __init__(self, order_id: str | None = None) -> None:
        msg = f"Pedido '{order_id}' não encontrado." if order_id else "Pedido não encontrado."
        super().__init__(msg, code="ORDER_NOT_FOUND")


class AddressNotFoundException(NotFoundException):
    """Endereço não encontrado no banco."""

    def __init__(self) -> None:
        super().__init__("Endereço não encontrado.", code="ADDRESS_NOT_FOUND")


# ---------------------------------------------------------------------------
# 409 - Conflict
# ---------------------------------------------------------------------------


class ConflictException(BookCommerceException):
    """Conflito com o estado atual do recurso."""

    def __init__(self, message: str, code: str = "CONFLICT") -> None:
        super().__init__(message, code, status.HTTP_409_CONFLICT)


class EmailAlreadyExistsException(ConflictException):
    """E-mail já cadastrado no sistema."""

    def __init__(self) -> None:
        super().__init__("E-mail já cadastrado.", code="EMAIL_ALREADY_EXISTS")


class InsufficientStockException(ConflictException):
    """Estoque insuficiente para concluir a operação."""

    def __init__(self, product_title: str, available: int) -> None:
        super().__init__(
            f"Estoque insuficiente para '{product_title}'. Disponível: {available}.",
            code="INSUFFICIENT_STOCK",
        )


class DuplicateReviewException(ConflictException):
    """Usuário já avaliou este produto."""

    def __init__(self) -> None:
        super().__init__(
            "Você já avaliou este produto.", code="DUPLICATE_REVIEW"
        )


class DuplicateWishlistException(ConflictException):
    """Produto já está na wishlist."""

    def __init__(self) -> None:
        super().__init__(
            "Produto já está na lista de desejos.", code="DUPLICATE_WISHLIST"
        )


# ---------------------------------------------------------------------------
# Handlers Globais
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos os handlers de exceção no app FastAPI."""

    @app.exception_handler(BookCommerceException)
    async def bookcommerce_exception_handler(
        request: Request, exc: BookCommerceException
    ) -> JSONResponse:
        """Converte BookCommerceException em resposta JSON padronizada."""
        if exc.status_code >= 500:
            logger.error(
                "Erro interno: %s - %s (path=%s)",
                exc.code,
                exc.message,
                request.url.path,
                exc_info=True,
            )
        else:
            logger.warning(
                "Erro %s: %s - %s (path=%s, user=%s)",
                exc.status_code,
                exc.code,
                exc.message,
                request.url.path,
                getattr(request.state, "user_id", None),
            )
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Formata erros de validação do Pydantic em resposta padronizada."""
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(part) for part in error["loc"] if part != "body"),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Erro de validação dos dados enviados.",
                    "details": errors,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handler genérico: loga e retorna 500 para erros inesperados.

        Em produção, NÃO expõe detalhes internos do erro.
        """
        logger.error(
            "Erro não tratado na rota %s: %s",
            request.url.path,
            str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Erro interno do servidor.",
                }
            },
        )