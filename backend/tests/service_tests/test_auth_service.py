from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import app.services.auth_service as auth_module
from app.api.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotFoundException,
)
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest


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

        assert result.message == "Cadastro realizado com sucesso."
        user_repo.get_by_email.assert_called_once_with("user@example.com")
        created = user_repo.create.call_args[0][0]
        assert created.email == "user@example.com"
        assert created.full_name == "John Doe"
        assert created.password_hash == "hashed-password"

    def test_register_email_already_exists_returns_generic(self, auth_service, user_repo):
        """P1-2: e-mail já existente NÃO revela o conflito (mesmo 201 genérico)."""
        user_repo.get_by_email.return_value = make_user()

        result = auth_service.register(register_payload())

        assert result.message == "Cadastro realizado com sucesso."
        user_repo.create.assert_not_called()


class TestLogin:
    def test_login_success(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = make_user()

        result = auth_service.login(SimpleNamespace(username="user@example.com", password="secret123"))

        assert result.access_token == "access-token"
        assert result.token_type == "bearer"
        assert result.refresh_token == "refresh-token"
        user_repo.get_by_email.assert_called_once_with("user@example.com")

    def test_login_wrong_password(self, auth_service, user_repo):
        auth_module.verify_password.return_value = False
        user_repo.get_by_email.return_value = make_user()

        with pytest.raises(InvalidCredentialsException):
            auth_service.login(SimpleNamespace(username="user@example.com", password="wrong-password"))

    def test_login_user_not_found(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsException):
            auth_service.login(SimpleNamespace(username="user@example.com", password="secret123"))

    def test_login_inactive_user(self, auth_service, user_repo):
        user_repo.get_by_email.return_value = make_user(is_active=False)

        with pytest.raises(InactiveUserException):
            auth_service.login(SimpleNamespace(username="user@example.com", password="secret123"))


class TestMe:
    def test_me_success(self, auth_service):
        user = make_user()

        assert auth_service.me(user) is user

    def test_me_none_user(self, auth_service):
        with pytest.raises(UserNotFoundException):
            auth_service.me(None)


class TestRefresh:
    def test_refresh_success_rotates(self, auth_service, user_repo):
        # Token armazenado ativo (não revogado, não expirado) -> rotação.
        stored = Mock(name="stored")
        stored.revoked = False
        stored.expires_at = datetime(2030, 1, 1, tzinfo=UTC)
        stored.jti = "jti-1"
        stored.user_id = 1
        stored.family_id = "fam-1"

        auth_service.refresh_repo.get_by_token_hash.return_value = stored

        with patch(
            "app.services.auth_service.decode_token",
            return_value={"sub": "1", "type": "refresh", "jti": "jti-1"},
        ):
            user_repo.get_by_id.return_value = make_user()
            result = auth_service.refresh("old-refresh-token")

        assert result.access_token == "access-token"
        assert result.refresh_token == "refresh-token"
        user_repo.get_by_id.assert_called_once_with(1)
        # O token antigo foi revogado (rotação) e um novo foi persistido na família.
        auth_service.refresh_repo.revoke.assert_called_once_with(stored)
        assert auth_service.session.add.called

    def test_refresh_rejects_access_token(self, auth_service, user_repo):
        with patch("app.services.auth_service.decode_token", return_value={"sub": "1", "type": "access"}):
            with pytest.raises(InvalidTokenException):
                auth_service.refresh("an-access-token")

        user_repo.get_by_id.assert_not_called()

    def test_refresh_invalid_user(self, auth_service, user_repo):
        with patch("app.services.auth_service.decode_token", return_value={"sub": "999", "type": "refresh", "jti": "x"}):
            user_repo.get_by_id.return_value = None
            with pytest.raises(InvalidTokenException):
                auth_service.refresh("old-refresh-token")

    def test_refresh_expired_token(self, auth_service, user_repo):

        from jose import ExpiredSignatureError

        with patch(
            "app.services.auth_service.decode_token",
            side_effect=ExpiredSignatureError("expired"),
        ):
            with pytest.raises(TokenExpiredException):
                auth_service.refresh("expired-refresh-token")

        user_repo.get_by_id.assert_not_called()

    def test_refresh_rejected_when_stored_token_revoked(self, auth_service, user_repo):
        """P1-1: refresh já revogado (= reuso) derruba a família inteira."""
        stored = Mock(name="stored")
        stored.revoked = True
        stored.family_id = "fam-1"
        auth_service.refresh_repo.get_by_token_hash.return_value = stored

        user_repo.get_by_id.return_value = make_user()

        with patch(
            "app.services.auth_service.decode_token",
            return_value={"sub": "1", "type": "refresh", "jti": "jti-1"},
        ):
            with pytest.raises(TokenExpiredException):
                auth_service.refresh("old-refresh-token")

        auth_service.refresh_repo.revoke_family.assert_called_once_with("fam-1")
        auth_service.session.commit.assert_called()

    def test_refresh_rejected_when_token_unknown(self, auth_service, user_repo):
        """P1-1: token que nunca emitimos é rejeitado."""
        auth_service.refresh_repo.get_by_token_hash.return_value = None
        user_repo.get_by_id.return_value = make_user()

        with patch(
            "app.services.auth_service.decode_token",
            return_value={"sub": "1", "type": "refresh", "jti": "jti-1"},
        ):
            with pytest.raises(InvalidTokenException):
                auth_service.refresh("forged-refresh-token")


class TestLogout:
    def test_logout_revokes_token(self, auth_service):
        """P1-1: logout revoga o refresh token apresentado."""
        stored = Mock(name="stored")
        stored.revoked = False
        auth_service.refresh_repo.get_by_token_hash.return_value = stored

        assert auth_service.logout("some-refresh-token") is None
        auth_service.refresh_repo.revoke.assert_called_once_with(stored)
        auth_service.session.commit.assert_called()

    def test_logout_no_token_does_nothing(self, auth_service):
        assert auth_service.logout(None) is None
        auth_service.refresh_repo.get_by_token_hash.assert_not_called()

    def test_revoke_all_for_user(self, auth_service):
        auth_service.revoke_all_for_user(1)
        auth_service.refresh_repo.revoke_all_for_user.assert_called_once_with(1)
        auth_service.session.commit.assert_called()
