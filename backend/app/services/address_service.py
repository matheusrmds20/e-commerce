from app.api.exceptions import (
    AddressForbiddenException,
    AddressLinkedToOrdersException,
    AddressNotFoundException,
    ConflictException,
)
from app.models.address import Address
from app.models.order import Order
from app.repositories.address_repo import AddressRepository
from app.repositories.user_repo import UserRepository


class AddressService:
    def __init__(self, db):
        self.repo = AddressRepository(db)
        self.user_repo = UserRepository(db)
        self.session = db


    def get_by_id(self, user_id: int, address_id: int) -> dict:

        address = self.repo.get_by_id(address_id)

        if address is None:
            raise AddressNotFoundException()

        if address.user_id != user_id:
            raise AddressForbiddenException()


        return address

    def get_by_user_id(self, user_id: int) -> list:
        # Usuário sem endereços é estado normal: devolve lista vazia (200).
        return self.repo.get_by_user_id(user_id)

    def get_by_zip_code(self, user_id: int, zip_code: str) -> dict:
        adress = self.repo.get_by_zip_code(user_id, zip_code)

        if not adress:
            raise AddressNotFoundException()

        return adress



    def get_actual_address_default(self, user_id: int) -> dict:
        adress = self.repo.get_actual_address_default(user_id)

        if adress is None:
            raise AddressNotFoundException()

        return adress

    def set_default(self, user_id: int, address_id: int) -> dict:
        address = self.repo.set_default(user_id, address_id)

        if address is None:
            raise AddressNotFoundException()

        return address

    def create(self, data, user_id: int) -> dict:

        with self.session.begin():
            address_already_exists = self.repo.get_by_zip_code(user_id, data.zip_code)

            if address_already_exists:
                raise ConflictException(
                    "Já existe um endereço com este CEP.",
                    code="ADDRESS_ALREADY_EXISTS",
                )

            new_address = self.repo.create(
                Address(
                    user_id=user_id,
                    street=data.street,
                    number=data.number,
                    complement=data.complement,
                    neighborhood=data.neighborhood,
                    city=data.city,
                    state=data.state,
                    zip_code=data.zip_code,
                    is_default=data.is_default,
                )
            )

            return new_address

    def update(self, adress_id: int, data, user_id: int) -> dict:


        with self.session.begin():

            address = self.repo.get_by_id(adress_id)

            if address is None:
                raise AddressNotFoundException()

            if address.user_id != user_id:
                raise AddressForbiddenException()


            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(address, field, value)

            self.repo.update(address)

            return address

    def delete(self, adress_id: int, user_id: int) -> dict:


        with self.session.begin():

            address = self.repo.get_by_id(adress_id)
            if address is None:
                raise AddressNotFoundException()

            if address.user_id != user_id:
                raise AddressForbiddenException()

            # Endereços usados em pedidos não podem ser excluídos: o pedido
            # guarda referência NOT NULL ao endereço de entrega e removê-lo
            # quebraria o histórico (IntegrityError no banco).
            tem_pedidos = (
                self.session.query(Order)
                .filter(Order.address_id == adress_id)
                .first()
                is not None
            )
            if tem_pedidos:
                raise AddressLinkedToOrdersException()

            self.repo.delete(address)
            return address
