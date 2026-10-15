from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.api.exceptions import (
    AddressForbiddenException,
    AddressNotFoundException,
    BadRequestException,
    CouponNotAssignedException,
    CouponNotFoundException,
    ForbiddenException,
    InsufficientStockException,
    InvalidCouponException,
    OrderNotFoundException,
    ProductNotFoundException,
    UserNotFoundException,
)
from app.models.address import Address
from app.models.cart import Cart
from app.models.coupon import Coupon, DiscountType
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderItemCreate, OrderUpdate


@pytest.fixture(autouse=True)
def _grant_coupon_ownership(user_coupon_repo, coupon_repo):

    user_coupon_repo.get_by_user_and_coupon.return_value = SimpleNamespace(
        used_at=None
    )

    user_coupon_repo.get_by_user_and_coupon_for_update.side_effect = (
        lambda uid, cid: user_coupon_repo.get_by_user_and_coupon.return_value
    )

    coupon_repo.get_by_id_for_update.side_effect = lambda cid: (
        coupon_repo.get_by_id.return_value
    )


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


def make_product(**kwargs):
    fields = dict(
        id=1,
        category_id=1,
        title="Livro",
        slug="livro",
        description="Descrição",
        author="Autor",
        price=50.0,
        stock_qty=10,
        is_active=True,
    )
    fields.update(kwargs)
    return Product(**fields)


def make_address(**kwargs):
    fields = dict(
        id=1,
        user_id=1,
        street="Rua A",
        number="10",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01001000",
    )
    fields.update(kwargs)
    return Address(**fields)


def make_order(**kwargs):
    fields = dict(
        id=1,
        user_id=1,
        address_id=1,
        subtotal=0.0,
        discount_amount=0.0,
        shipping_cost=0.0,
        total=0.0,
        status=OrderStatus.PENDING,
    )
    fields.update(kwargs)
    return Order(**fields)


def make_coupon(**kwargs):
    fields = dict(
        id=1,
        code="PROMO10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        valid_until=datetime.now() + timedelta(days=1),
        is_active=True,
        used_count=0,
    )
    fields.update(kwargs)
    return Coupon(**fields)


def make_order_item(**kwargs):
    fields = dict(id=1, order_id=1, product_id=1, quantity=2, price=50.0)
    fields.update(kwargs)
    return OrderItem(**fields)


def order_create_payload(**kwargs):
    fields = dict(
        address_id=1,
        items=[OrderItemCreate(product_id=1, quantity=2)],
    )
    fields.update(kwargs)
    return OrderCreate(**fields)


class TestGetByUserID:
    def test_success(self, order_service, user_repo, order_repo):
        user = make_user()
        orders = [make_order()]
        user_repo.get_by_id.return_value = user
        # O service usa `get_by_user_id_eager` (evita N+1 na serialização).
        order_repo.get_by_user_id_eager.return_value = orders

        assert order_service.get_by_user_id(1) == orders
        order_repo.get_by_user_id_eager.assert_called_once_with(1)

    def test_user_not_found(self, order_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            order_service.get_by_user_id(1)

    def test_paginado_usa_repo_paginado(
        self, order_service, user_repo, order_repo
    ):
        user_repo.get_by_id.return_value = make_user()
        order_repo.paginate_by_user_id.return_value = ([make_order()], 1)

        pagina = order_service.get_paginated_by_user_id(1, page=1, per_page=10)

        assert pagina["meta"]["total"] == 1
        assert pagina["meta"]["per_page"] == 10
        assert len(pagina["data"]) == 1
        order_repo.paginate_by_user_id.assert_called_once_with(1, 1, 10)


class TestCreate:
    def _setup(self, address_repo, product_repo, order_item_repo, order_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        order_repo.create.return_value = make_order()

    def test_success_no_coupon(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        self._setup(address_repo, product_repo, order_item_repo, order_repo)

        result = order_service.create(1, order_create_payload())

        assert result is not None
        created = order_repo.create.call_args[0][0]
        assert created.user_id == 1
        assert created.subtotal == 100.0
        assert created.discount_amount == 0.0
        assert created.total == 100.0
        coupon_repo.get_by_id.assert_not_called()

    def test_success_with_percentage_coupon(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        self._setup(address_repo, product_repo, order_item_repo, order_repo)
        coupon_repo.get_by_id.return_value = make_coupon()

        order_service.create(1, order_create_payload(coupon_id=1))

        created = order_repo.create.call_args[0][0]
        assert created.subtotal == 100.0
        assert created.discount_amount == 10.0
        assert created.total == 90.0

    def test_success_with_fixed_coupon(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        self._setup(address_repo, product_repo, order_item_repo, order_repo)
        coupon_repo.get_by_id.return_value = make_coupon(
            discount_type=DiscountType.FIXED,
            discount_value=15.0,
        )

        order_service.create(1, order_create_payload(coupon_id=1))

        created = order_repo.create.call_args[0][0]
        assert created.discount_amount == 15.0
        assert created.total == 85.0

    def test_success_with_max_discount_cap(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        self._setup(address_repo, product_repo, order_item_repo, order_repo)
        coupon_repo.get_by_id.return_value = make_coupon(
            discount_value=50.0,
            max_discount=20.0,
        )

        order_service.create(1, order_create_payload(coupon_id=1))

        created = order_repo.create.call_args[0][0]
        assert created.discount_amount == 20.0
        assert created.total == 80.0

    def test_address_not_found(self, order_service, address_repo):
        address_repo.get_by_id.return_value = None

        with pytest.raises(AddressNotFoundException):
            order_service.create(1, order_create_payload(address_id=99))

    def test_address_not_owned(self, order_service, address_repo):
        address_repo.get_by_id.return_value = make_address(user_id=2)

        with pytest.raises(AddressForbiddenException):
            order_service.create(1, order_create_payload())

    def test_empty_items(self, order_service, address_repo):
        address_repo.get_by_id.return_value = make_address()

        with pytest.raises(BadRequestException):
            order_service.create(1, order_create_payload(items=[]))

    def test_product_not_found(self, order_service, address_repo, product_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = None

        with pytest.raises(ProductNotFoundException):
            order_service.create(1, order_create_payload())

    def test_product_inactive(self, order_service, address_repo, product_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product(is_active=False)

        with pytest.raises(BadRequestException):
            order_service.create(1, order_create_payload())

    def test_insufficient_stock(self, order_service, address_repo, product_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product(stock_qty=1)

        with pytest.raises(InsufficientStockException):
            order_service.create(1, order_create_payload())

    def test_coupon_not_found(self, order_service, address_repo, product_repo, order_item_repo, coupon_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        coupon_repo.get_by_id.return_value = None

        with pytest.raises(CouponNotFoundException):
            order_service.create(1, order_create_payload(coupon_id=99))

    def test_coupon_inactive(self, order_service, address_repo, product_repo, order_item_repo, coupon_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        coupon_repo.get_by_id.return_value = make_coupon(is_active=False)

        with pytest.raises(InvalidCouponException):
            order_service.create(1, order_create_payload(coupon_id=1))

    def test_coupon_expired(self, order_service, address_repo, product_repo, order_item_repo, coupon_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        coupon_repo.get_by_id.return_value = make_coupon(
            valid_until=datetime.now() - timedelta(days=1)
        )

        with pytest.raises(InvalidCouponException):
            order_service.create(1, order_create_payload(coupon_id=1))

    def test_coupon_not_applicable(self, order_service, address_repo, product_repo, order_item_repo, coupon_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        coupon_repo.get_by_id.return_value = make_coupon(product_id=99)

        with pytest.raises(InvalidCouponException):
            order_service.create(1, order_create_payload(coupon_id=1))

    def test_coupon_not_assigned_to_user(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
        user_coupon_repo,
    ):
        """Cupom válido, mas sem vínculo com o usuário → rejeitado."""
        self._setup(address_repo, product_repo, order_item_repo, order_repo)
        coupon_repo.get_by_id.return_value = make_coupon()
        # Sobrescreve o default do autouse: o vínculo não existe.
        user_coupon_repo.get_by_user_and_coupon.return_value = None

        with pytest.raises(CouponNotAssignedException):
            order_service.create(1, order_create_payload(coupon_id=1))

    def test_coupon_min_purchase_not_met(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        self._setup(address_repo, product_repo, order_item_repo, order_repo)
        coupon_repo.get_by_id.return_value = make_coupon(min_purchase=200.0)

        with pytest.raises(InvalidCouponException):
            order_service.create(1, order_create_payload(coupon_id=1))

    def test_coupon_no_limite_de_usos_e_rejeitado(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        """`max_uses` agora é respeitado: antes era gravado e nunca lido."""
        self._setup(address_repo, product_repo, order_item_repo, order_repo)
        coupon_repo.get_by_id.return_value = make_coupon(
            max_uses=2, used_count=2
        )

        with pytest.raises(InvalidCouponException):
            order_service.create(1, order_create_payload(coupon_id=1))

    def test_coupon_dentro_do_limite_e_consumido(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        """Um uso válido incrementa `used_count` em 1."""
        self._setup(address_repo, product_repo, order_item_repo, order_repo)
        coupon = make_coupon(max_uses=5, used_count=1)
        coupon_repo.get_by_id.return_value = coupon

        order_service.create(1, order_create_payload(coupon_id=1))

        assert coupon.used_count == 2

    def test_checkout_usa_lock_no_cupom(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        """O checkout trava a linha do cupom (evita corrida em max_uses)."""
        self._setup(address_repo, product_repo, order_item_repo, order_repo)
        coupon_repo.get_by_id.return_value = make_coupon()
        coupon_repo.get_by_id_for_update.reset_mock()

        order_service.create(1, order_create_payload(coupon_id=1))

        coupon_repo.get_by_id_for_update.assert_called_once_with(1)

    def test_sem_cupom_nao_consome_nem_trava(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        coupon_repo,
    ):
        self._setup(address_repo, product_repo, order_item_repo, order_repo)

        order_service.create(1, order_create_payload())

        coupon_repo.get_by_id_for_update.assert_not_called()


class TestUpdate:
    def test_nao_queima_uso_do_cupom_em_edicao_simples(
        self, order_service, order_repo
    ):

        order = make_order(coupon_id=None)
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = [make_order_item()]

        order_service.update(1, 1, OrderUpdate(notes="ok"))

        assert order.notes == "ok"

    def test_success(self, order_service, order_repo):
        order = make_order()
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = [make_order_item()]

        result = order_service.update(1, 1, OrderUpdate(notes="nova observação"))

        assert result is order
        assert order.notes == "nova observação"
        assert order.subtotal == 100.0
        assert order.total == 100.0

    def test_with_items(self, order_service, order_repo, order_item_repo, product_repo):
        order = make_order()
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = []
        product_repo.get_by_id.return_value = make_product()
        item = make_order_item(quantity=1)
        order_item_repo.create_order_item.return_value = item

        result = order_service.update(1, 1, OrderUpdate(items=[OrderItemCreate(product_id=1, quantity=1)]))

        assert result is order
        assert item.order_id == 1
        assert order.subtotal == 50.0
        assert order.total == 50.0

    def test_cancelled_order(self, order_service, order_repo):
        order_repo.get_by_id.return_value = make_order(status=OrderStatus.CANCELLED)

        with pytest.raises(BadRequestException):
            order_service.update(1, 1, OrderUpdate(status=OrderStatus.PROCESSING))

    def test_not_found(self, order_service, order_repo):
        order_repo.get_by_id.return_value = None

        with pytest.raises(OrderNotFoundException):
            order_service.update(1, 1, OrderUpdate(notes="x"))

    def test_not_owned(self, order_service, order_repo):
        order_repo.get_by_id.return_value = make_order(user_id=2)

        with pytest.raises(ForbiddenException):
            order_service.update(1, 1, OrderUpdate(notes="x"))

    def test_address_not_owned(self, order_service, order_repo, address_repo):
        order_repo.get_by_id.return_value = make_order()
        address_repo.get_by_id.return_value = make_address(user_id=2)

        with pytest.raises(AddressForbiddenException):
            order_service.update(1, 1, OrderUpdate(address_id=1))


class TestDelete:
    def test_success(self, order_service, order_repo):
        order = make_order()
        order_repo.get_by_id.return_value = order

        result = order_service.delete(1, 1)

        assert result is order
        order_repo.delete.assert_called_once_with(order)

    def test_not_found(self, order_service, order_repo):
        order_repo.get_by_id.return_value = None

        with pytest.raises(OrderNotFoundException):
            order_service.delete(1, 1)

    def test_not_owned(self, order_service, order_repo):
        order_repo.get_by_id.return_value = make_order(user_id=2)

        with pytest.raises(ForbiddenException):
            order_service.delete(1, 1)


class TestBaixaDeEstoque:
  
    def _setup(
        self, address_repo, product_repo, order_item_repo, order_repo, produto
    ):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = produto
        order_item_repo.create_order_item.return_value = make_order_item()
        order_repo.create.return_value = make_order()

    def test_create_baixa_estoque(
        self, order_service, address_repo, product_repo, order_item_repo, order_repo
    ):
        produto = make_product(stock_qty=10)
        self._setup(
            address_repo, product_repo, order_item_repo, order_repo, produto
        )

        order_service.create(1, order_create_payload())

        # Pedido de 2 unidades sobre estoque 10 → 8.
        assert produto.stock_qty == 8
        product_repo.decrement_stock.assert_called_once_with(produto, 2)

    def test_create_sem_estoque_nao_baixa(
        self, order_service, address_repo, product_repo, order_item_repo, order_repo
    ):
  
        produto = make_product(stock_qty=1)
        self._setup(
            address_repo, product_repo, order_item_repo, order_repo, produto
        )

        with pytest.raises(InsufficientStockException):
            order_service.create(1, order_create_payload())

        assert produto.stock_qty == 1
        product_repo.decrement_stock.assert_not_called()

    def test_create_produto_repetido_soma_a_quantidade(
        self, order_service, address_repo, product_repo, order_item_repo, order_repo
    ):

        produto = make_product(stock_qty=3)
        self._setup(
            address_repo, product_repo, order_item_repo, order_repo, produto
        )

        payload = order_create_payload(
            items=[
                OrderItemCreate(product_id=1, quantity=2),
                OrderItemCreate(product_id=1, quantity=2),
            ]
        )

        with pytest.raises(InsufficientStockException):
            order_service.create(1, payload)

        assert produto.stock_qty == 3
        product_repo.decrement_stock.assert_not_called()

    def test_cancelar_repõe_estoque(
        self, order_service, order_repo, product_repo, order_item_repo
    ):

        order = make_order(status=OrderStatus.PENDING)
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = [make_order_item(quantity=2)]

        produto = make_product(stock_qty=8)
        product_repo.get_by_id.return_value = produto

        order_service.update(1, 1, OrderUpdate(status=OrderStatus.CANCELLED))

        assert order.status == OrderStatus.CANCELLED
        assert produto.stock_qty == 10
        product_repo.restock.assert_called_once_with(produto, 2)

    def test_cancelar_duas_vezes_nao_repõe_de_novo(
        self, order_service, order_repo, product_repo
    ):

        order = make_order(status=OrderStatus.CANCELLED)
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = [make_order_item(quantity=2)]

        produto = make_product(stock_qty=8)
        product_repo.get_by_id.return_value = produto


        with pytest.raises(BadRequestException):
            order_service.update(1, 1, OrderUpdate(status=OrderStatus.PROCESSING))

        assert produto.stock_qty == 8
        product_repo.restock.assert_not_called()

    def test_editar_itens_reconcilia_estoque(
        self, order_service, order_repo, product_repo, order_item_repo
    ):

        order = make_order()
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = [make_order_item(quantity=1)]

        produto = make_product(stock_qty=10)
        product_repo.get_by_id.return_value = produto
        order_item_repo.create_order_item.return_value = make_order_item(quantity=5)

        order_service.update(
            1, 1, OrderUpdate(items=[OrderItemCreate(product_id=1, quantity=5)])
        )


        assert produto.stock_qty == 6
        product_repo.restock.assert_called_once_with(produto, 1)
        product_repo.decrement_stock.assert_called_once_with(produto, 5)


class TestDevolucaoDeUsoDoCupom:


    def test_cancelar_devolve_uso(
        self, order_service, order_repo, coupon_repo, product_repo
    ):
        order = make_order(status=OrderStatus.PENDING, coupon_id=7)
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = [make_order_item(quantity=1)]
        product_repo.get_by_id.return_value = make_product(stock_qty=5)

        cupom = make_coupon(id=7, used_count=3)
        coupon_repo.get_by_id.return_value = cupom

        order_service.update(1, 1, OrderUpdate(status=OrderStatus.CANCELLED))

        assert cupom.used_count == 2

    def test_nao_devolve_abaixo_de_zero(
        self, order_service, order_repo, coupon_repo, product_repo
    ):
        order = make_order(status=OrderStatus.PENDING, coupon_id=7)
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = [make_order_item(quantity=1)]
        product_repo.get_by_id.return_value = make_product(stock_qty=5)

        cupom = make_coupon(id=7, used_count=0)
        coupon_repo.get_by_id.return_value = cupom

        order_service.update(1, 1, OrderUpdate(status=OrderStatus.CANCELLED))

        assert cupom.used_count == 0

    def test_pedido_sem_cupom_nao_toca_em_cupom(
        self, order_service, order_repo, coupon_repo, product_repo
    ):
        order = make_order(status=OrderStatus.PENDING, coupon_id=None)
        order_repo.get_by_id.return_value = order
        order_repo.get_with_items.return_value = [make_order_item(quantity=1)]
        product_repo.get_by_id.return_value = make_product(stock_qty=5)

        order_service.update(1, 1, OrderUpdate(status=OrderStatus.CANCELLED))

        coupon_repo.get_by_id_for_update.assert_not_called()

    def test_delete_devolve_uso(self, order_service, order_repo, coupon_repo):
        order = make_order(coupon_id=7)
        order_repo.get_by_id.return_value = order

        cupom = make_coupon(id=7, used_count=2)
        coupon_repo.get_by_id.return_value = cupom

        order_service.delete(1, 1)

        assert cupom.used_count == 1
        order_repo.delete.assert_called_once_with(order)


class TestUsoUnicoPorCliente:


    def test_primeiro_uso_marca_used_at(
        self, order_service, address_repo, product_repo, order_item_repo,
        order_repo, coupon_repo, user_coupon_repo,
    ):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        order_repo.create.return_value = make_order()

        coupon_repo.get_by_id.return_value = make_coupon(
            single_use_per_user=True
        )
        vinculo = SimpleNamespace(used_at=None)
        user_coupon_repo.get_by_user_and_coupon.return_value = vinculo

        order_service.create(1, order_create_payload(coupon_id=1))

        assert vinculo.used_at is not None

    def test_segundo_uso_e_rejeitado(
        self, order_service, address_repo, product_repo, order_item_repo,
        order_repo, coupon_repo, user_coupon_repo,
    ):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()

        coupon_repo.get_by_id.return_value = make_coupon(
            single_use_per_user=True
        )
        user_coupon_repo.get_by_user_and_coupon.return_value = SimpleNamespace(
            used_at=datetime.now()
        )

        with pytest.raises(InvalidCouponException):
            order_service.create(1, order_create_payload(coupon_id=1))

    def test_cupom_normal_permite_reuso(
        self, order_service, address_repo, product_repo, order_item_repo,
        order_repo, coupon_repo, user_coupon_repo,
    ):

        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        order_repo.create.return_value = make_order()

        coupon_repo.get_by_id.return_value = make_coupon(
            single_use_per_user=False
        )
        user_coupon_repo.get_by_user_and_coupon.return_value = SimpleNamespace(
            used_at=datetime.now()
        )

        # Não levanta: a regra de uso único está desligada.
        order_service.create(1, order_create_payload(coupon_id=1))


class TestLimpezaDoCarrinho:


    def _setup(
        self, address_repo, product_repo, order_item_repo, order_repo, user_repo, cart
    ):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product(stock_qty=10)
        order_item_repo.create_order_item.return_value = make_order_item()
        order_repo.create.return_value = make_order()

        usuario = make_user()
        usuario.cart = cart
        user_repo.get_by_id.return_value = usuario
        return usuario

    def test_create_limpa_o_carrinho_do_usuario(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        user_repo,
        cart_repo,
    ):
        cart = Cart(id=99, user_id=1)
        self._setup(
            address_repo, product_repo, order_item_repo, order_repo, user_repo, cart
        )

        order_service.create(1, order_create_payload())

        # Limpa pelo id do carrinho do usuário, não por um id qualquer.
        cart_repo.clear.assert_called_once_with(99)

    def test_create_sem_carrinho_nao_quebra(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        user_repo,
        cart_repo,
    ):
  
        self._setup(
            address_repo,
            product_repo,
            order_item_repo,
            order_repo,
            user_repo,
            cart=None,
        )

        order_service.create(1, order_create_payload())

        cart_repo.clear.assert_not_called()

    def test_create_usuario_inexistente_nao_quebra_limpeza(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        user_repo,
        cart_repo,
    ):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product(stock_qty=10)
        order_item_repo.create_order_item.return_value = make_order_item()
        order_repo.create.return_value = make_order()
        user_repo.get_by_id.return_value = None

        order_service.create(1, order_create_payload())

        cart_repo.clear.assert_not_called()

    def test_falha_no_checkout_nao_limpa_o_carrinho(
        self,
        order_service,
        address_repo,
        product_repo,
        order_item_repo,
        order_repo,
        user_repo,
        cart_repo,
    ):
  
        cart = Cart(id=99, user_id=1)
        self._setup(
            address_repo,
            product_repo,
            order_item_repo,
            order_repo,
            user_repo,
            cart,
        )
        product_repo.get_by_id.return_value = make_product(stock_qty=1)

        with pytest.raises(InsufficientStockException):
            order_service.create(1, order_create_payload())

        cart_repo.clear.assert_not_called()


class TestCartRepositoryClear:
  

    def test_clear_deleta_por_cart_id(self):
        from unittest.mock import MagicMock

        from app.repositories.cart_repo import CartRepository

        session = MagicMock(name="session")
        repo = CartRepository(session)
        session.query.return_value.filter.return_value.delete.return_value = 3

        removidos = repo.clear(42)

        assert removidos == 3
        assert session.query.return_value.filter.return_value.delete.called


class TestProductRepositoryEstoque:
   

    def test_decrement_stock_reduz(self):
        from unittest.mock import MagicMock

        from app.repositories.product_repo import ProductRepository

        repo = ProductRepository(MagicMock(name="session"))
        produto = make_product(stock_qty=10)

        repo.decrement_stock(produto, 3)

        assert produto.stock_qty == 7

    def test_decrement_stock_nao_permite_negativo(self):
        from unittest.mock import MagicMock

        from app.repositories.product_repo import ProductRepository

        repo = ProductRepository(MagicMock(name="session"))
        produto = make_product(stock_qty=2)

        with pytest.raises(ValueError):
            repo.decrement_stock(produto, 5)

        assert produto.stock_qty == 2

    def test_restock_aumenta(self):
        from unittest.mock import MagicMock

        from app.repositories.product_repo import ProductRepository

        repo = ProductRepository(MagicMock(name="session"))
        produto = make_product(stock_qty=2)

        repo.restock(produto, 5)

        assert produto.stock_qty == 7
