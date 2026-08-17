import pytest

import app.services.auth_service as auth_module
from app.api.exceptions import (
    EmailAlreadyExistsException,
    InactiveUserException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest


def make_user(**kwargs):
    fields = dict(
        id=1,
        email="user@example.com",
        full_name="John Doe",
        password_hash="hashed-password",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    fields.update(kwargs)
    return User(**fields)


def register_payload(**kwargs):
    fields = dict(
        email="user@example.com",
        full_name="John Doe",
        password="secret123",
    )
    fields.update(kwargs)
    return RegisterRequest(**fields)


class TestRegister:
    def test_register_success(self, auth_service, user_repo):
        user = make_user()
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = user

        result = auth_service.register(register_payload())

        assert result is user
        user_repo.get_by_email.assert_called_once_with("user@example.com")
        created = user_repo.create.call_args[0][0]
        assert created.email == "user@example.com"
        assert created.full_name == "John Doe"
        assert created.password_hash == "hashed-password"

    def test_register_email_already_exists(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = make_user()

        with pytest.raises(EmailAlreadyExistsException):
            auth_service.register(register_payload())

        user_repo.create.assert_not_called()


class TestLogin:
    def test_login_success(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = make_user()

        result = auth_service.login(LoginRequest(email="user@example.com", password="secret123"))

        assert result.access_token == "access-token"
        assert result.token_type == "bearer"
        user_repo.get_by_email.assert_called_once_with("user@example.com")

    def test_login_wrong_password(self, auth_service, user_repo):
        auth_module.verify_password.return_value = False
        user_repo.get_by_email.return_value = make_user()

        with pytest.raises(InvalidCredentialsException):
            auth_service.login(LoginRequest(email="user@example.com", password="wrong-password"))

    def test_login_user_not_found(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsException):
            auth_service.login(LoginRequest(email="user@example.com", password="secret123"))

    def test_login_inactive_user(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = make_user(is_active=False)

        with pytest.raises(InactiveUserException):
            auth_service.login(LoginRequest(email="user@example.com", password="secret123"))


class TestMe:
    def test_me_success(self, auth_service):
        user = make_user()

        assert auth_service.me(user) is user

    def test_me_none_user(self, auth_service):
        with pytest.raises(UserNotFoundException):
            auth_service.me(None)
