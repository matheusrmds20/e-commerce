from app.models.address import Address
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
            raise ValueError(f"No address found with id {address_id}")

        if address.user_id != user_id:
            raise ValueError("Address is not owned by user")


        return address

    def get_by_user_id(self, user_id: int) -> list:
        addresses = self.repo.get_by_user_id(user_id)

        if not addresses:
            raise ValueError(f"No addresses found with user_id {user_id}")


        return addresses

    def get_by_zip_code(self, user_id: int, zip_code: str) -> dict:
        adress = self.repo.get_by_zip_code(user_id, zip_code)

        if not adress:
            raise ValueError(f"No address found with zip_code {zip_code}")

        return adress



    def get_actual_address_default(self, user_id: int) -> dict:
        adress = self.repo.get_actual_address_default(user_id)

        if adress is None:
            raise ValueError(f"No default address found")
        
        return adress

    def set_default(self, user_id: int, address_id: int) -> dict:
        address = self.repo.set_default(user_id, address_id)

        if address is None:
            raise ValueError(f"No address found with id {address_id}")
        
        return address

    def create(self, data, user_id: int) -> dict:
        
        with self.session.begin():
            address_already_exists = self.repo.get_by_zip_code(user_id, data.zip_code)

            if address_already_exists:
                raise ValueError(f"Address with zip_code {data.zip_code} already exists")

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
                raise ValueError(f"No address found with id {adress_id}")

            if address.user_id != user_id:
                raise ValueError("Address is not owned by user")


            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(address, field, value)

            self.repo.update(address)

            return address

    def delete(self, adress_id: int, user_id: int) -> dict:


        with self.session.begin():

            address = self.repo.get_by_id(adress_id)
            if address is None:
                raise ValueError(f"No address found with id {adress_id}")

            if address.user_id != user_id:
                raise ValueError("Address is not owned by user")

            self.repo.delete(address)
            return address