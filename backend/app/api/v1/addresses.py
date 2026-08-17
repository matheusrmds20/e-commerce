from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.services.address_service import AddressService

address_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserId = Annotated[int, Query(description="ID do usuário dono do endereço")]


def get_address_service(db: DbSession) -> AddressService:
    return AddressService(db)


@address_router.post(
    "/create",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo endereço para o usuário",
)
def create_address(
    data: AddressCreate, user_id: UserId, db: DbSession
) -> AddressResponse:
    return get_address_service(db).create(data, user_id)


@address_router.get(
    "/list",
    response_model=list[AddressResponse],
    summary="Lista todos os endereços do usuário",
)
def list_addresses(user_id: UserId, db: DbSession) -> list:
    return get_address_service(db).get_by_user_id(user_id)


@address_router.get(
    "/get/{address_id}",
    response_model=AddressResponse,
    summary="Busca um endereço pelo ID",
)
def get_address(
    address_id: int, user_id: UserId, db: DbSession
) -> AddressResponse:
    return get_address_service(db).get_by_id(user_id, address_id)


@address_router.get(
    "/default",
    response_model=AddressResponse,
    summary="Busca o endereço padrão do usuário",
)
def get_default_address(user_id: UserId, db: DbSession) -> AddressResponse:
    return get_address_service(db).get_actual_address_default(user_id)


@address_router.get(
    "/zip/{zip_code}",
    response_model=AddressResponse,
    summary="Busca um endereço pelo CEP",
)
def get_address_by_zip_code(
    zip_code: str, user_id: UserId, db: DbSession
) -> AddressResponse:
    return get_address_service(db).get_by_zip_code(user_id, zip_code)


@address_router.patch(
    "/default/set/{address_id}",
    response_model=AddressResponse,
    summary="Define um endereço como padrão",
)
def set_default_address(
    address_id: int, user_id: UserId, db: DbSession
) -> AddressResponse:
    return get_address_service(db).set_default(user_id, address_id)


@address_router.patch(
    "/update/{address_id}",
    response_model=AddressResponse,
    summary="Atualiza um endereço",
)
def update_address(
    address_id: int, data: AddressUpdate, user_id: UserId, db: DbSession
) -> AddressResponse:
    return get_address_service(db).update(address_id, data, user_id)


@address_router.delete(
    "/delete/{address_id}",
    response_model=AddressResponse,
    summary="Exclui um endereço",
)
def delete_address(
    address_id: int, user_id: UserId, db: DbSession
) -> AddressResponse:
    return get_address_service(db).delete(address_id, user_id)
