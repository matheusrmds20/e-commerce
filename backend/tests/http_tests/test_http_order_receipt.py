
from unittest.mock import Mock, patch

import pytest

from app.api.exceptions import ForbiddenException, NotFoundException

PREFIX = "/api/v1/orders"


@pytest.fixture
def auth_user():
    """Usuário autenticado injetado no lugar de ``get_current_user``."""
    from app.api.deps import get_current_user
    from app.main import app

    def _definir(user_id: int = 1):
        user = Mock(name="user")
        user.id = user_id
        user.email = "user@example.com"
        user.is_active = True
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _definir
    app.dependency_overrides.pop(get_current_user, None)


class TestDownloadReceipt:
    def test_require_auth(self, client):
        response = client.get(f"{PREFIX}/7/comprovante")
        assert response.status_code == 401

    def test_success_downloads_pdf(self, client, auth_user, tmp_path):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_receipt_path.return_value = "comprovantes/comprovante_order_7.pdf"

        with patch("app.api.v1.orders.get_order_service", return_value=svc), patch(
            "app.utils.storage.download_receipt",
            return_value=b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
        ) as download:
            response = client.get(f"{PREFIX}/7/comprovante")

        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert "comprovante_order_7.pdf" in response.headers.get(
            "content-disposition", ""
        )
        assert response.content.startswith(b"%PDF-")
        svc.get_receipt_path.assert_called_once_with(7, 1)
        download.assert_called_once_with("comprovantes/comprovante_order_7.pdf")

    def test_forbidden_for_other_user(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_receipt_path.side_effect = ForbiddenException(
            "Order is not owned by user"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/7/comprovante")

        assert response.status_code == 403
        from helpers import assert_error
        assert_error(response, 403)

    def test_not_found_when_not_generated(self, client, auth_user):
        auth_user(1)
        svc = Mock(name="order_service")
        svc.get_receipt_path.side_effect = NotFoundException(
            "Receipt not generated yet for order 7", code="RECEIPT_NOT_FOUND"
        )

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/7/comprovante")

        assert response.status_code == 404
