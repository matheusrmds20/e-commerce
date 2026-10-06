"""Testes do fluxo de envio de e-mail de confirmação de pedido (service).

Cobre:
- ``OrderService.send_confirmation_email`` (agendamento da task no Celery).
- Regras de domínio: pedido inexistente, pedido não-completado e pedido de
  outro usuário (proteção contra IDOR).
- O payload serializável montado por ``build_order_details`` usado na task.

A task Celery é PATCHADA (``app.services.order_service.send_order_confirmation_email``)
— nenhum Redis/broker real. Cada teste captura a chamada a ``.delay``.

Os métodos são ``async`` e NÃO há pytest-asyncio no projeto, então cada teste
chama a coroutine com ``asyncio.run()``.
"""
import asyncio
from unittest.mock import Mock, patch

import pytest

from app.api.exceptions import (
    BadRequestException,
    ForbiddenException,
    OrderNotFoundException,
)
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User, UserRole
from app.utils.email import build_order_details


def make_user(**kwargs):
    fields = dict(
        id=1,
        email="user@example.com",
        full_name="John Doe",
        password_hash="hashed",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    fields.update(kwargs)
    return User(**fields)


def make_order(**kwargs):
    fields = dict(
        id=10,
        user_id=1,
        address_id=1,
        subtotal=100.0,
        discount_amount=0.0,
        shipping_cost=10.0,
        total=110.0,
        status=OrderStatus.COMPLETED,
    )
    fields.update(kwargs)
    return Order(**fields)


def make_item(**kwargs):
    fields = dict(id=1, order_id=10, product_id=1, quantity=2, price=50.0)
    fields.update(kwargs)
    return OrderItem(**fields)


def _order_completed_com_user_items():
    """Pedido COMPLETO, com itens e produto, e usuário vinculado."""
    user = make_user()
    product = Product(
        id=1,
        category_id=1,
        title="Livro Teste",
        slug="livro-teste",
        description="D",
        author="Autor",
        price=50.0,
        stock_qty=10,
        is_active=True,
    )
    item = make_item()
    order = make_order()
    item.products = product
    order.order_items = [item]
    order.users = user
    return user, order


class TestBuildOrderDetails:
    """O payload do e-mail deve ser PLENAMENTE serializável pelo Celery."""

    def test_monta_dict_de_primitivos(self):
        _, order = _order_completed_com_user_items()

        payload = build_order_details(order)

        assert payload == {
            "total": 110.0,
            "subtotal": 100.0,
            "items": [{"name": "Livro Teste", "quantity": 2, "price": 50.0}],
        }
        # Nenhum objeto não-serializável (SQLAlchemy) no payload.
        assert all(
            isinstance(v, (int, float, str, bool, list, dict)) or v is None
            for v in payload.values()
        )

    def test_itens_ausentes_gera_lista_vazia(self):
        order = make_order()
        order.order_items = []
        assert build_order_details(order)["items"] == []


class TestSendConfirmationEmail:
    def test_delay_recebe_dados_corretos(self, order_service, order_repo):
        user, order = _order_completed_com_user_items()
        order_repo.get_by_id.return_value = order

        with patch(
            "app.services.order_service.send_order_confirmation_email"
        ) as task:
            task.delay.return_value = Mock(id="task_abc123")

            resultado = asyncio.run(order_service.send_confirmation_email(10, user))

        assert resultado["status"] == "success"
        assert resultado["sended"] == "task_abc123"
        task.delay.assert_called_once_with(10, "user@example.com", build_order_details(order))

    def test_pedido_nao_completado_recusa(self, order_service, order_repo):
        user, order = _order_completed_com_user_items()
        order.status = OrderStatus.PENDING
        order_repo.get_by_id.return_value = order

        with patch(
            "app.services.order_service.send_order_confirmation_email"
        ) as task:
            with pytest.raises(BadRequestException):
                asyncio.run(order_service.send_confirmation_email(10, user))
        task.delay.assert_not_called()

    def test_pedido_inexistente_recusa(self, order_service, order_repo):
        order_repo.get_by_id.return_value = None
        user = make_user()

        with patch(
            "app.services.order_service.send_order_confirmation_email"
        ) as task:
            with pytest.raises(OrderNotFoundException):
                asyncio.run(order_service.send_confirmation_email(999, user))
        task.delay.assert_not_called()

    def test_pedido_de_outro_usuario_recusa_idor(self, order_service, order_repo):
        """Só o dono do pedido pode disparar o e-mail (proteje IDOR)."""
        _, order = _order_completed_com_user_items()  # owner user_id=1
        order_repo.get_by_id.return_value = order
        outro_usuario = make_user(id=2, email="outro@example.com")

        with patch(
            "app.services.order_service.send_order_confirmation_email"
        ) as task:
            with pytest.raises(ForbiddenException):
                asyncio.run(order_service.send_confirmation_email(10, outro_usuario))
        task.delay.assert_not_called()
