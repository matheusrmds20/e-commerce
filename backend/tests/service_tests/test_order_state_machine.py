"""Testes da máquina de estados de ``orders.status``.

Cobre as regras de negócio acordadas:
  1. O admin transita livremente pelo fluxo normal, mas não reabre pedido
     fechado (cancelado/reembolsado).
  2. O cliente só pode cancelar, e apenas de um estado em aberto
     (PENDING/PROCESSING).
"""

import pytest

from app.api.exceptions import InvalidStateTransitionException
from app.models.order import OrderStatus
from app.services.order_state_machine import (
    assert_admin_transition,
    assert_client_transition,
)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
class TestAdminTransition:
    def test_fluxo_normal(self):
        """O admin percorre o fluxo normal sem barreiras."""
        assert_admin_transition(OrderStatus.PENDING, OrderStatus.PROCESSING)
        assert_admin_transition(OrderStatus.PROCESSING, OrderStatus.SHIPPED)
        assert_admin_transition(OrderStatus.SHIPPED, OrderStatus.DELIVERED)
        assert_admin_transition(OrderStatus.DELIVERED, OrderStatus.COMPLETED)

    def test_cancelamento_e_reembolso_permitidos(self):
        assert_admin_transition(OrderStatus.PENDING, OrderStatus.CANCELLED)
        assert_admin_transition(OrderStatus.COMPLETED, OrderStatus.REFUNDED)
        assert_admin_transition(OrderStatus.SHIPPED, OrderStatus.CANCELLED)

    def test_nao_reabre_pedido_cancelado(self):
        """Cancelado é estado final: não volta a ser ativo."""
        with pytest.raises(InvalidStateTransitionException):
            assert_admin_transition(OrderStatus.CANCELLED, OrderStatus.PROCESSING)

        with pytest.raises(InvalidStateTransitionException):
            assert_admin_transition(OrderStatus.CANCELLED, OrderStatus.COMPLETED)

    def test_nao_reabre_pedido_reembolsado(self):
        with pytest.raises(InvalidStateTransitionException):
            assert_admin_transition(OrderStatus.REFUNDED, OrderStatus.PENDING)

    def test_reembolso_para_estado_fechado_permitido(self):
        """Cancelado → reembolsado (entre fechados) é permitido."""
        assert_admin_transition(OrderStatus.CANCELLED, OrderStatus.REFUNDED)


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------
class TestClientTransition:
    def test_pode_cancelar_de_pending(self):
        assert_client_transition(OrderStatus.PENDING, OrderStatus.CANCELLED)

    def test_pode_cancelar_de_processing(self):
        assert_client_transition(OrderStatus.PROCESSING, OrderStatus.CANCELLED)

    def test_nao_pode_cancelar_de_shipped(self):
        """Depois de enviado, o cliente não cancela (US/atendimento sim)."""
        with pytest.raises(InvalidStateTransitionException):
            assert_client_transition(OrderStatus.SHIPPED, OrderStatus.CANCELLED)

    def test_nao_pode_cancelar_de_delivered_e_completed(self):
        with pytest.raises(InvalidStateTransitionException):
            assert_client_transition(OrderStatus.DELIVERED, OrderStatus.CANCELLED)
        with pytest.raises(InvalidStateTransitionException):
            assert_client_transition(OrderStatus.COMPLETED, OrderStatus.CANCELLED)

    def test_nao_pode_mudar_para_outro_status(self):
        """O cliente não seta status que não seja cancelamento (R3)."""
        for destino in (
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.COMPLETED,
            OrderStatus.REFUNDED,
        ):
            with pytest.raises(InvalidStateTransitionException):
                assert_client_transition(OrderStatus.PENDING, destino)

    def test_nao_pode_cancelar_pedido_ja_cancelado(self):
        with pytest.raises(InvalidStateTransitionException):
            assert_client_transition(OrderStatus.CANCELLED, OrderStatus.CANCELLED)
