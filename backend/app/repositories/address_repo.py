
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.address import Address
from app.repositories.base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    def __init__(self, db: Session) -> None:
        super().__init__(Address, db)


    def get_by_user_id(self, user_id: int) -> list[Address]:
        return self.session.query(Address).filter(Address.user_id == user_id).all()


    def get_by_zip_code(self, user_id: int, zip_code: str) -> Address:
        return self.session.query(Address).filter(
            Address.zip_code == zip_code,
            Address.is_active.is_(True),
            Address.user_id == user_id
        ).first()


    def get_actual_address_default(self, user_id: int) -> Address:
        return self.session.query(Address).filter(
            Address.is_default.is_(True),
            Address.user_id == user_id
        ).first()


    def set_default(self, user_id: int, address_id: int) -> Address:
        with self.session.begin():

            new_default = self.get_by_id(address_id)

            if new_default.user_id != user_id:
                raise ValueError("Address is not owned by user")

            self.session.execute(
                update(Address)
                .where(Address.user_id == user_id)
                .values(is_default=False)
            )

            new_default.is_default = True

            self.session.flush()
            self.session.refresh(new_default)
            return new_default
