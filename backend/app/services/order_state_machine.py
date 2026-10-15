
from app.api.exceptions import InvalidStateTransitionException
from app.models.order import OrderStatus


_ESTADOS_ABERTOS: frozenset[OrderStatus] = frozenset(
    {OrderStatus.PENDING, OrderStatus.PROCESSING}
)


_ESTADOS_TERMINAIS: frozenset[OrderStatus] = frozenset(
    {OrderStatus.CANCELLED, OrderStatus.REFUNDED}
)


def assert_admin_transition(
    current: OrderStatus, target: OrderStatus
) -> None:

    if current in _ESTADOS_TERMINAIS and target not in _ESTADOS_TERMINAIS:
        raise InvalidStateTransitionException(current=current, target=target)


def assert_client_transition(
    current: OrderStatus, target: OrderStatus
) -> None:

    if target != OrderStatus.CANCELLED:
        raise InvalidStateTransitionException(current=current, target=target)

    if current not in _ESTADOS_ABERTOS:
        raise InvalidStateTransitionException(current=current, target=target)
