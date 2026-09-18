import pytest

from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


def make_address(**kwargs):
    fields = dict(
        id=1,
        user_id=1,
        street="Rua A",
        number="10",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01001000",
        is_default=False,
    )
    fields.update(kwargs)
    return Address(**fields)


def create_payload(**kwargs):
    fields = dict(
        street="Rua A",
        number="10",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01001000",
    )
    fields.update(kwargs)
    return AddressCreate(**fields)


class TestGet:
    def test_get_by_id_success(self, address_service, address_repo):
        address = make_address()
        address_repo.get_by_id.return_value = address

        assert address_service.get_by_id(1, 1) is address

    def test_get_by_id_not_found(self, address_service, address_repo):
        address_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            address_service.get_by_id(1, 99)

        assert str(exc.value) == "No address found with id 99"

    def test_get_by_id_not_owned(self, address_service, address_repo):
        address_repo.get_by_id.return_value = make_address(user_id=2)

        with pytest.raises(ValueError) as exc:
            address_service.get_by_id(1, 1)

        assert str(exc.value) == "Address is not owned by user"

    def test_get_by_user_id_success(self, address_service, address_repo):
        addresses = [make_address()]
        address_repo.get_by_user_id.return_value = addresses

        assert address_service.get_by_user_id(1) == addresses

    def test_get_by_user_id_empty(self, address_service, address_repo):
        address_repo.get_by_user_id.return_value = []

        with pytest.raises(ValueError) as exc:
            address_service.get_by_user_id(1)

        assert str(exc.value) == "No addresses found with user_id 1"

    def test_get_by_zip_code_success(self, address_service, address_repo):
        address = make_address()
        address_repo.get_by_zip_code.return_value = address

        assert address_service.get_by_zip_code(1, "01001000") is address

    def test_get_by_zip_code_empty(self, address_service, address_repo):
        address_repo.get_by_zip_code.return_value = []

        with pytest.raises(ValueError) as exc:
            address_service.get_by_zip_code(1, "99999999")

        assert str(exc.value) == "No address found with zip_code 99999999"

    def test_get_default_success(self, address_service, address_repo):
        address = make_address(is_default=True)
        address_repo.get_actual_address_default.return_value = address

        assert address_service.get_actual_address_default(1) is address

    def test_get_default_none(self, address_service, address_repo):
        address_repo.get_actual_address_default.return_value = None

        with pytest.raises(ValueError) as exc:
            address_service.get_actual_address_default(1)

        assert str(exc.value) == "No default address found"


class TestSetDefault:
    def test_success(self, address_service, address_repo):
        address = make_address(is_default=True)
        address_repo.set_default.return_value = address

        result = address_service.set_default(1, 1)

        assert result is address
        address_repo.set_default.assert_called_once_with(1, 1)

    def test_not_found(self, address_service, address_repo):
        address_repo.set_default.return_value = None

        with pytest.raises(ValueError) as exc:
            address_service.set_default(1, 99)

        assert str(exc.value) == "No address found with id 99"


class TestCreate:
    def test_success(self, address_service, address_repo):
        address = make_address()
        address_repo.get_by_zip_code.return_value = None
        address_repo.create.return_value = address

        result = address_service.create(create_payload(), 1)

        assert result is address
        created = address_repo.create.call_args[0][0]
        assert created.user_id == 1
        assert created.street == "Rua A"
        assert created.zip_code == "01001000"

    def test_owner_comes_from_argument_not_payload(self, address_service, address_repo):
        """O dono é sempre o ``user_id`` recebido (do token), não do payload.

        ``AddressCreate`` não tem mais ``user_id``; este teste garante que o
        service persiste o endereço sob o usuário autenticado.
        """
        address_repo.get_by_zip_code.return_value = None
        address_repo.create.side_effect = lambda address: address

        result = address_service.create(create_payload(), 7)

        assert result.user_id == 7

    def test_zip_code_already_exists(self, address_service, address_repo):
        address_repo.get_by_zip_code.return_value = make_address()

        with pytest.raises(ValueError) as exc:
            address_service.create(create_payload(), 1)

        assert "already exists" in str(exc.value)


class TestUpdate:
    def test_success(self, address_service, address_repo):
        address = make_address()
        address_repo.get_by_id.return_value = address
        address_repo.update.return_value = address

        result = address_service.update(1, AddressUpdate(street="Rua B"), 1)

        assert result is address
        assert address.street == "Rua B"
        address_repo.update.assert_called_once_with(address)

    def test_not_found(self, address_service, address_repo):
        address_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            address_service.update(99, AddressUpdate(street="Rua B"), 1)

        assert str(exc.value) == "No address found with id 99"

    def test_not_owned(self, address_service, address_repo):
        address_repo.get_by_id.return_value = make_address(user_id=2)

        with pytest.raises(ValueError) as exc:
            address_service.update(1, AddressUpdate(street="Rua B"), 1)

        assert str(exc.value) == "Address is not owned by user"


class TestDelete:
    def test_success(self, address_service, address_repo):
        address = make_address()
        address_repo.get_by_id.return_value = address

        result = address_service.delete(1, 1)

        assert result is address
        address_repo.delete.assert_called_once_with(address)

    def test_not_found(self, address_service, address_repo):
        address_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            address_service.delete(99, 1)

        assert str(exc.value) == "No address found with id 99"

    def test_not_owned(self, address_service, address_repo):
        address_repo.get_by_id.return_value = make_address(user_id=2)

        with pytest.raises(ValueError) as exc:
            address_service.delete(1, 1)

        assert str(exc.value) == "Address is not owned by user"
