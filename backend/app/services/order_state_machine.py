"""Máquina de estados para ``orders.status``.

Centraliza as regras de transição de status de um pedido, separando o que o
**administrador** pode fazer do que o **cliente** pode fazer.

Regras de negócio acordadas:
  1. O administrador transita livremente pelo fluxo normal de status, mas não
     pode **reabrir** um pedido fechado (cancelado/reembolsado).
  2. O cliente só pode **cancelar** o próprio pedido, e apenas enquanto ele
     estiver em aberto (``PENDING``/``PROCESSING``).
  3. O cliente não deve setar outros status via ``OrderService.update`` (toda
     transição passa por ``assert_client_transition``).

Uso:

    from app.services.order_state_machine import (
        assert_admin_transition,
        assert_client_transition,
    )

    assert_admin_transition(order.status, OrderStatus.SHIPPED)
    assert_client_transition(order.status, OrderStatus.CANCELLED)

Cada função lança ``InvalidStateTransitionException`` quando a transição não é
permitida.
"""

from app.api.exceptions import InvalidStateTransitionException
from app.models.order import OrderStatus

# Estados "abertos": o pedido ainda pode ser cancelado pelo cliente/reaberto.
_ESTADOS_ABERTOS: frozenset[OrderStatus] = frozenset(
    {OrderStatus.PENDING, OrderStatus.PROCESSING}
)

# Estados terminais: um pedido fechado não volta para o fluxo ativo.
_ESTADOS_TERMINAIS: frozenset[OrderStatus] = frozenset(
    {OrderStatus.CANCELLED, OrderStatus.REFUNDED}
)


def assert_admin_transition(
    current: OrderStatus, target: OrderStatus
) -> None:
    """Valida uma transição de status feita por administrador.

    O admin tem liberdade sobre o fluxo normal (``PENDING → PROCESSING →
    SHIPPED → DELIVERED → COMPLETED``, cancelamentos e reembolsos), mas não
    pode **reabrir** um pedido já fechado — cancelado ou reembolsado é estado
    final e não volta a ser ativo.
    """
    if current in _ESTADOS_TERMINAIS and target not in _ESTADOS_TERMINAIS:
        raise InvalidStateTransitionException(current=current, target=target)


def assert_client_transition(
    current: OrderStatus, target: OrderStatus
) -> None:
    """Valida uma transição de status feita pelo cliente.

    Regra de negócio: o cliente só pode **cancelar** o próprio pedido e apenas
    a partir de um estado em aberto (``PENDING``/``PROCESSING``). Qualquer
    outra mudança de status é rejeitada.
    """
    if target != OrderStatus.CANCELLED:
        raise InvalidStateTransitionException(current=current, target=target)

    if current not in _ESTADOS_ABERTOS:
        raise InvalidStateTransitionException(current=current, target=target)
