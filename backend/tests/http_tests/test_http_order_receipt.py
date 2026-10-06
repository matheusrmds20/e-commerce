"""Testes HTTP do endpoint de download do comprovante PDF.

Cobre:
- ``GET /api/v1/orders/{order_id}/comprovante`` (baixar pelo nº do pedido)
- Autenticação obrigatória (401)
- Acesso ao próprio pedido (200, arquivo PDF)
- Proibido para pedido de outro usuário (403, anti-IDOR)
- Comprovante ainda não gerado (404)

O ``OrderService`` é mockado na factory da rota (``get_order_service``). No teste
de sucesso, o service retorna um caminho de um PDF real criado no disco para o
``FileResponse`` servir.
"""
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


def _fake_pdf(tmp_path) -> str:
    """Cria um PDF mínimo no disco e retorna seu caminho."""
    p = tmp_path / "comprovante_order_7.pdf"
    p.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    return str(p)


class TestDownloadReceipt:
    def test_require_auth(self, client):
        response = client.get(f"{PREFIX}/7/comprovante")
        assert response.status_code == 401

    def test_success_downloads_pdf(self, client, auth_user, tmp_path):
        auth_user(1)
        pdf_path = _fake_pdf(tmp_path)
        svc = Mock(name="order_service")
        svc.get_receipt_path.return_value = pdf_path

        with patch("app.api.v1.orders.get_order_service", return_value=svc):
            response = client.get(f"{PREFIX}/7/comprovante")

        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert "comprovante_order_7.pdf" in response.headers.get(
            "content-disposition", ""
        )
        assert response.content.startswith(b"%PDF-")
        svc.get_receipt_path.assert_called_once_with(7, 1)

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
