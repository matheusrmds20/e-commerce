import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse


class TestRegisterRequest:
    def test_valid(self):
        data = RegisterRequest(email="user@example.com", full_name="John Doe", password="senha123")

        assert data.password == "senha123"

    @pytest.mark.parametrize(
        "password",
        ["semnumero", "12345678", "1234567", "abcdefgh", "1234abcd"[:7]],
    )
    def test_invalid_password(self, password):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", full_name="John Doe", password=password)

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", full_name="John Doe", password="senha123")

    def test_short_name(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", full_name="ab", password="senha123")


class TestLoginRequest:
    def test_valid(self):
        data = LoginRequest(email="user@example.com", password="senha123")

        assert data.email == "user@example.com"


class TestTokenResponse:
    def test_default_token_type(self):
        token = TokenResponse(access_token="abc")

        assert token.token_type == "bearer"


class TestMessageResponse:
    def test_message(self):
        data = MessageResponse(message="ok")

        assert data.message == "ok"
