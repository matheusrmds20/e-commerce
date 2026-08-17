import pytest
from pydantic import ValidationError

from app.schemas.user import (
    AdminUserCreate,
    ChangePasswordRequest,
    CustomerUserCreate,
    UserUpdate,
)


class TestUserSchemas:
    def test_role_defaults(self):
        admin = AdminUserCreate(email="admin@example.com", full_name="Admin", password="senha123")
        customer = CustomerUserCreate(
            email="customer@example.com", full_name="Customer", password="senha123"
        )

        assert admin.role.value == "admin"
        assert customer.role.value == "customer"

    def test_user_update_invalid_password(self):
        with pytest.raises(ValidationError):
            UserUpdate(password="somenteletras")

    def test_change_password_valid(self):
        data = ChangePasswordRequest(current_password="velha123", new_password="nova1234")

        assert data.new_password == "nova1234"

    def test_change_password_invalid(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(current_password="velha123", new_password="12345678")
