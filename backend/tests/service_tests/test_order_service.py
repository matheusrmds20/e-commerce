from datetime import datetime, timedelta

import pytest

from app.models.address import Address
from app.models.coupon import Coupon, DiscountType
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderItemCreate, OrderUpdate


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


class TestGetByID:
    def test_success(self, order_service, order_repo):
        order = make_order()
        order_repo.get_by_id.return_value = order

        assert order_service.get_by_id(1, 1) is order

    def test_not_found(self, order_service, order_repo):
        order_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            order_service.get_by_id(1, 1)

        assert str(exc.value) == "No order found with id 1"

    def test_not_owned(self, order_service, order_repo):
        order_repo.get_by_id.return_value = make_order(user_id=2)

        with pytest.raises(ValueError) as exc:
            order_service.get_by_id(1, 1)

        assert str(exc.value) == "Order is not owned by user"


class TestGetByUserID:
    def test_success(self, order_service, user_repo):
        user = make_user()
        orders = [make_order()]
        user.orders = orders
        user_repo.get_by_id.return_value = user

        assert order_service.get_by_user_id(1) == orders

    def test_user_not_found(self, order_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            order_service.get_by_user_id(1)

        assert str(exc.value) == "No user found with id 1"

    def test_no_orders(self, order_service, user_repo):
        user = make_user()
        user.orders = []
        user_repo.get_by_id.return_value = user

        with pytest.raises(ValueError) as exc:
            order_service.get_by_user_id(1)

        assert str(exc.value) == "No orders found with user_id 1"


class TestGetWithItems:
    def test_success(self, order_service, order_repo):
        order_repo.get_by_id.return_value = make_order()
        items = [make_order_item()]
        order_repo.get_with_items.return_value = items

        assert order_service.get_with_items(1, 1) == items

    def test_no_items(self, order_service, order_repo):
        order_repo.get_by_id.return_value = make_order()
        order_repo.get_with_items.return_value = []

        with pytest.raises(ValueError) as exc:
            order_service.get_with_items(1, 1)

        assert str(exc.value) == "No items found in order with id 1"


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

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload(address_id=99))

        assert str(exc.value) == "No address found with id 99"

    def test_address_not_owned(self, order_service, address_repo):
        address_repo.get_by_id.return_value = make_address(user_id=2)

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload())

        assert str(exc.value) == "Address is not owned by user"

    def test_empty_items(self, order_service, address_repo):
        address_repo.get_by_id.return_value = make_address()

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload(items=[]))

        assert str(exc.value) == "Order must have at least one item"

    def test_product_not_found(self, order_service, address_repo, product_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload())

        assert str(exc.value) == "No product found with id 1"

    def test_product_inactive(self, order_service, address_repo, product_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product(is_active=False)

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload())

        assert str(exc.value) == "Product 'Livro' is not active"

    def test_insufficient_stock(self, order_service, address_repo, product_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product(stock_qty=1)

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload())

        assert "Insufficient stock" in str(exc.value)

    def test_coupon_not_found(self, order_service, address_repo, product_repo, order_item_repo, coupon_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        coupon_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload(coupon_id=99))

        assert str(exc.value) == "No coupon found with id 99"

    def test_coupon_inactive(self, order_service, address_repo, product_repo, order_item_repo, coupon_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        coupon_repo.get_by_id.return_value = make_coupon(is_active=False)

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload(coupon_id=1))

        assert "is not active" in str(exc.value)

    def test_coupon_expired(self, order_service, address_repo, product_repo, order_item_repo, coupon_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        coupon_repo.get_by_id.return_value = make_coupon(
            valid_until=datetime.now() - timedelta(days=1)
        )

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload(coupon_id=1))

        assert "has expired" in str(exc.value)

    def test_coupon_not_applicable(self, order_service, address_repo, product_repo, order_item_repo, coupon_repo):
        address_repo.get_by_id.return_value = make_address()
        product_repo.get_by_id.return_value = make_product()
        order_item_repo.create_order_item.return_value = make_order_item()
        coupon_repo.get_by_id.return_value = make_coupon(product_id=99)

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload(coupon_id=1))

        assert "not applicable" in str(exc.value)

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

        with pytest.raises(ValueError) as exc:
            order_service.create(1, order_create_payload(coupon_id=1))

        assert "minimum purchase" in str(exc.value)


class TestUpdate:
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

        with pytest.raises(ValueError) as exc:
            order_service.update(1, 1, OrderUpdate(status=OrderStatus.PROCESSING))

        assert str(exc.value) == "Cannot update a cancelled order"

    def test_not_found(self, order_service, order_repo):
        order_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            order_service.update(1, 1, OrderUpdate(notes="x"))

        assert str(exc.value) == "No order found with id 1"

    def test_not_owned(self, order_service, order_repo):
        order_repo.get_by_id.return_value = make_order(user_id=2)

        with pytest.raises(ValueError) as exc:
            order_service.update(1, 1, OrderUpdate(notes="x"))

        assert str(exc.value) == "Order is not owned by user"

    def test_address_not_owned(self, order_service, order_repo, address_repo):
        order_repo.get_by_id.return_value = make_order()
        address_repo.get_by_id.return_value = make_address(user_id=2)

        with pytest.raises(ValueError) as exc:
            order_service.update(1, 1, OrderUpdate(address_id=1))

        assert str(exc.value) == "Address is not owned by user"


class TestDelete:
    def test_success(self, order_service, order_repo):
        order = make_order()
        order_repo.get_by_id.return_value = order

        result = order_service.delete(1, 1)

        assert result is order
        order_repo.delete.assert_called_once_with(order)

    def test_not_found(self, order_service, order_repo):
        order_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            order_service.delete(1, 1)

        assert str(exc.value) == "No order found with id 1"

    def test_not_owned(self, order_service, order_repo):
        order_repo.get_by_id.return_value = make_order(user_id=2)

        with pytest.raises(ValueError) as exc:
            order_service.delete(1, 1)

        assert str(exc.value) == "Order is not owned by user"
