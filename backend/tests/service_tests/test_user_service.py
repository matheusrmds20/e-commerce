import pytest

import app.services.user_service as user_module
from app.api.exceptions import (
    BadRequestException,
    EmailAlreadyExistsException,
    UserNotFoundException,
)
from app.models.user import User, UserRole
from app.schemas.user import AdminUserCreate, UserUpdate


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


def admin_payload(**kwargs):
    fields = dict(email="user@example.com", full_name="John Doe", password="secret123")
    fields.update(kwargs)
    return AdminUserCreate(**fields)


class TestCreate:
    def test_create_success(self, user_service, user_repo):
        user = make_user()
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = user

        result = user_service.create(admin_payload())

        assert result is user
        created = user_repo.create.call_args[0][0]
        assert created.email == "user@example.com"
        assert created.role == UserRole.ADMIN
        assert created.password_hash == "hashed-password"

    def test_create_email_already_exists(self, user_service, user_repo):
        user_repo.get_by_email.return_value = make_user()

        with pytest.raises(EmailAlreadyExistsException):
            user_service.create(admin_payload())

        user_repo.create.assert_not_called()


class TestGet:
    def test_get_by_id_success(self, user_service, user_repo):
        user = make_user()
        user_repo.get_by_id.return_value = user

        assert user_service.get_by_id(1) is user

    def test_get_by_id_not_found(self, user_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            user_service.get_by_id(999)

    def test_get_by_email_success(self, user_service, user_repo):
        user = make_user()
        user_repo.get_by_email.return_value = user

        assert user_service.get_by_email("user@example.com") is user

    def test_get_by_email_not_found(self, user_service, user_repo):
        user_repo.get_by_email.return_value = None

        with pytest.raises(UserNotFoundException):
            user_service.get_by_email("missing@example.com")


class TestUpdate:
    def test_update_success(self, user_service, user_repo):
        user = make_user()
        user_repo.get_by_id.return_value = user
        user_repo.get_by_email.return_value = None
        user_repo.update.return_value = user

        result = user_service.update(1, UserUpdate(full_name="New Name"))

        assert result is user
        assert user.full_name == "New Name"
        user_repo.update.assert_called_once_with(user)

    def test_update_not_found(self, user_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            user_service.update(1, UserUpdate(full_name="New Name"))

    def test_update_email_conflict(self, user_service, user_repo):
        user = make_user()
        other = make_user(id=2, email="other@example.com")
        user_repo.get_by_id.return_value = user
        user_repo.get_by_email.return_value = other

        with pytest.raises(EmailAlreadyExistsException):
            user_service.update(1, UserUpdate(email="other@example.com"))


class TestChangePassword:
    def test_change_password_success(self, user_service, user_repo):
        user_repo.get_by_id.return_value = make_user()

        result = user_service.change_password(1, "old-pass", "new-pass-123")

        assert result.message == "Senha alterada com sucesso."
        user_repo.change_password.assert_called_once_with(1, "hashed-password")

    def test_change_password_wrong_current(self, user_service, user_repo):
        user_repo.get_by_id.return_value = make_user()
        user_module.verify_password.return_value = False

        with pytest.raises(BadRequestException) as exc:
            user_service.change_password(1, "wrong-pass", "new-pass-123")

        assert exc.value.code == "INVALID_CURRENT_PASSWORD"

    def test_change_password_user_not_found(self, user_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            user_service.change_password(1, "old-pass", "new-pass-123")


class TestDeactivate:
    def test_deactivate_success(self, user_service, user_repo):
        user = make_user()
        user_deactivated = make_user(is_active=False)
        user_repo.get_by_id.return_value = user
        user_repo.deactivate.return_value = user_deactivated

        result = user_service.deactivate(1)

        assert result is user_deactivated
        assert result.is_active is False
        user_repo.deactivate.assert_called_once_with(1)

    def test_deactivate_not_found(self, user_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            user_service.deactivate(1)
