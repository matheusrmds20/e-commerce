import pytest
from pydantic import ValidationError

from app.schemas.address import AddressCreate


class TestAddressCreate:
    def valid_payload(self, **kwargs):
        fields = dict(
            user_id=1,
            street="Rua A",
            number="10",
            neighborhood="Centro",
            city="São Paulo",
            state="SP",
            zip_code="01001000",
        )
        fields.update(kwargs)
        return fields

    def test_valid(self):
        data = AddressCreate(**self.valid_payload())

        assert data.state == "SP"

    @pytest.mark.parametrize("state", ["S", "SPO"])
    def test_invalid_state(self, state):
        with pytest.raises(ValidationError):
            AddressCreate(**self.valid_payload(state=state))

    @pytest.mark.parametrize("zip_code", ["0100", "0100100000"])
    def test_invalid_zip_code(self, zip_code):
        with pytest.raises(ValidationError):
            AddressCreate(**self.valid_payload(zip_code=zip_code))
