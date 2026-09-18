from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.services.address_service import AddressService

address_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]


def get_address_service(db: DbSession) -> AddressService:
    return AddressService(db)


def _traduzir_value_error(exc: ValueError) -> BadRequestException:
    """Traduz os ``ValueError`` do service em erros HTTP (senão viram 500)."""
    msg = str(exc)

    if "not owned by user" in msg:
        return ForbiddenException(msg)

    if "already exists" in msg:
        return ConflictException(msg, code="ADDRESS_ALREADY_EXISTS")

    if "No address" in msg:
        return NotFoundException(msg, code="ADDRESS_NOT_FOUND")

    return BadRequestException(msg)


@address_router.post(
    "/create",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo endereço para o usuário autenticado",
)
def create_address(
    data: AddressCreate, user: UserDb, db: DbSession
) -> AddressResponse:
    try:
        return get_address_service(db).create(data, user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@address_router.get(
    "/list",
    response_model=list[AddressResponse],
    summary="Lista os endereços do usuário autenticado",
)
def list_addresses(user: UserDb, db: DbSession) -> list:
    try:
        return get_address_service(db).get_by_user_id(user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@address_router.get(
    "/get/{address_id}",
    response_model=AddressResponse,
    summary="Busca um endereço pelo ID",
)
def get_address(
    address_id: int, user: UserDb, db: DbSession
) -> AddressResponse:
    try:
        return get_address_service(db).get_by_id(user.id, address_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@address_router.get(
    "/default",
    response_model=AddressResponse,
    summary="Busca o endereço padrão do usuário",
)
def get_default_address(user: UserDb, db: DbSession) -> AddressResponse:
    try:
        return get_address_service(db).get_actual_address_default(user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@address_router.get(
    "/zip/{zip_code}",
    response_model=AddressResponse,
    summary="Busca um endereço pelo CEP",
)
def get_address_by_zip_code(
    zip_code: str, user: UserDb, db: DbSession
) -> AddressResponse:
    try:
        return get_address_service(db).get_by_zip_code(user.id, zip_code)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@address_router.patch(
    "/default/set/{address_id}",
    response_model=AddressResponse,
    summary="Define um endereço como padrão",
)
def set_default_address(
    address_id: int, user: UserDb, db: DbSession
) -> AddressResponse:
    try:
        return get_address_service(db).set_default(user.id, address_id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@address_router.patch(
    "/update/{address_id}",
    response_model=AddressResponse,
    summary="Atualiza um endereço",
)
def update_address(
    address_id: int, data: AddressUpdate, user: UserDb, db: DbSession
) -> AddressResponse:
    try:
        return get_address_service(db).update(address_id, data, user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc


@address_router.delete(
    "/delete/{address_id}",
    response_model=AddressResponse,
    summary="Exclui um endereço",
)
def delete_address(
    address_id: int, user: UserDb, db: DbSession
) -> AddressResponse:
    try:
        return get_address_service(db).delete(address_id, user.id)
    except ValueError as exc:
        raise _traduzir_value_error(exc) from exc
