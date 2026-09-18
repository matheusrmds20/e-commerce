import pytest

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User, UserRole


def make_cart(**kwargs):
    fields = dict(id=1, user_id=1)
    fields.update(kwargs)
    return Cart(**fields)


def make_cart_item(**kwargs):
    fields = dict(id=1, cart_id=1, product_id=1, quantity=2)
    fields.update(kwargs)
    return CartItem(**fields)


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


class TestGetByID:
    def test_success(self, cart_service, cart_repo):
        cart = make_cart()
        cart_repo.get_by_id.return_value = cart

        assert cart_service.get_by_id(1, 1) is cart

    def test_not_found(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.get_by_id(1, 1)

        assert str(exc.value) == "No cart found with id 1"

    def test_not_owned(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = make_cart(user_id=2)

        with pytest.raises(ValueError) as exc:
            cart_service.get_by_id(1, 1)

        assert str(exc.value) == "Cart is not owned by user"


class TestGetByUserID:
    def test_success(self, cart_service, user_repo):
        user = make_user()
        cart = make_cart()
        user.cart = cart
        user_repo.get_by_id.return_value = user

        assert cart_service.get_by_user_id(1) is cart

    def test_user_not_found(self, cart_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.get_by_user_id(1)

        assert str(exc.value) == "No user found with id 1"

    def test_no_cart(self, cart_service, user_repo):
        user = make_user()
        user.cart = None
        user_repo.get_by_id.return_value = user

        with pytest.raises(ValueError) as exc:
            cart_service.get_by_user_id(1)

        assert str(exc.value) == "No cart found with user_id 1"


class TestGetWithItems:
    def test_success(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = make_cart()
        items = [make_cart_item()]
        cart_repo.get_with_items.return_value = items

        assert cart_service.get_with_items(1, 1) == items

    def test_not_found(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.get_with_items(1, 1)

        assert str(exc.value) == "No cart found with id 1"

    def test_not_owned(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = make_cart(user_id=2)

        with pytest.raises(ValueError) as exc:
            cart_service.get_with_items(1, 1)

        assert str(exc.value) == "Cart is not owned by user"

    def test_no_items(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = make_cart()
        cart_repo.get_with_items.return_value = []

        with pytest.raises(ValueError) as exc:
            cart_service.get_with_items(1, 1)

        assert str(exc.value) == "No items found in cart with id 1"


class TestCreate:
    def test_success(self, cart_service, user_repo, cart_repo):
        user = make_user()
        user.cart = None
        cart = make_cart()
        user_repo.get_by_id.return_value = user
        cart_repo.create.return_value = cart

        result = cart_service.create(1)

        assert result is cart
        created = cart_repo.create.call_args[0][0]
        assert created.user_id == 1

    def test_user_not_found(self, cart_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.create(1)

        assert str(exc.value) == "No user found with id 1"

    def test_user_already_has_cart(self, cart_service, user_repo):
        user = make_user()
        user.cart = make_cart()
        user_repo.get_by_id.return_value = user

        with pytest.raises(ValueError) as exc:
            cart_service.create(1)

        assert str(exc.value) == "User 1 already has a cart"


class TestAddItem:
    def test_add_new_item(self, cart_service, cart_repo, product_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        product_repo.get_by_id.return_value = make_product()
        cart_item_repo.get_by_cart_and_product.return_value = None
        item = make_cart_item()
        cart_item_repo.add_item.return_value = item

        result = cart_service.add_item(1, 1, 1, 2)

        assert result is item
        cart_item_repo.add_item.assert_called_once_with(1, 1, 2)

    def test_add_existing_item_increments(self, cart_service, cart_repo, product_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        product_repo.get_by_id.return_value = make_product()
        existing = make_cart_item(quantity=2)
        cart_item_repo.get_by_cart_and_product.return_value = existing

        result = cart_service.add_item(1, 1, 1, 3)

        assert result is existing
        assert existing.quantity == 5

    def test_cart_not_found(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.add_item(1, 1, 1, 2)

        assert str(exc.value) == "No cart found with id 1"

    def test_cart_not_owned(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = make_cart(user_id=2)

        with pytest.raises(ValueError) as exc:
            cart_service.add_item(1, 1, 1, 2)

        assert str(exc.value) == "Cart is not owned by user"

    def test_product_not_found(self, cart_service, cart_repo, product_repo):
        cart_repo.get_by_id.return_value = make_cart()
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.add_item(1, 1, 99, 2)

        assert str(exc.value) == "No product found with id 99"

    def test_insufficient_stock(self, cart_service, cart_repo, product_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        product_repo.get_by_id.return_value = make_product(stock_qty=1)
        # Nada ainda na sacola — a validação compara o total pedido com o estoque.
        cart_item_repo.get_by_cart_and_product.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.add_item(1, 1, 1, 5)

        assert "Insufficient stock for product 1" in str(exc.value)

    def test_insufficient_stock_considera_o_que_ja_esta_na_sacola(
        self, cart_service, cart_repo, product_repo, cart_item_repo
    ):
        """Estoque 3, 2 já na sacola, adicionar 2 → total 4 > 3, deve falhar.

        Sem somar o que já existe, `quantity` (2) caberia no estoque e o item
        ficaria com 4 unidades de um produto que só tem 3.
        """
        cart_repo.get_by_id.return_value = make_cart()
        product_repo.get_by_id.return_value = make_product(stock_qty=3)
        cart_item_repo.get_by_cart_and_product.return_value = make_cart_item(
            quantity=2
        )

        with pytest.raises(ValueError) as exc:
            cart_service.add_item(1, 1, 1, 2)

        assert "requested: 4" in str(exc.value)


class TestUpdateItem:
    def test_success(self, cart_service, cart_repo, cart_item_repo, product_repo):
        cart_repo.get_by_id.return_value = make_cart()
        # Estoque de sobra para o novo valor pedido.
        product_repo.get_by_id.return_value = make_product(stock_qty=100)
        item = make_cart_item()
        cart_item_repo.get_by_id.return_value = item

        result = cart_service.update_item(1, 1, 1, 5)

        assert result is item
        cart_item_repo.update_quantity.assert_called_once_with(item, 5)

    def test_item_not_found(self, cart_service, cart_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        cart_item_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.update_item(1, 1, 99, 5)

        assert str(exc.value) == "No cart item found with id 99"


class TestDecreaseItem:
    def test_success(self, cart_service, cart_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        item = make_cart_item()
        cart_item_repo.get_by_id.return_value = item

        result = cart_service.decrease_item(1, 1, 1, 1)

        assert result is item
        cart_item_repo.decrease_quantity.assert_called_once_with(item, 1)

    def test_item_not_found(self, cart_service, cart_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        cart_item_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.decrease_item(1, 1, 99, 1)

        assert str(exc.value) == "No cart item found with id 99"


class TestRemoveItem:
    def test_success(self, cart_service, cart_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        item = make_cart_item()
        cart_item_repo.get_by_id.return_value = item

        result = cart_service.remove_item(1, 1, 1)

        assert result is item
        cart_item_repo.delete.assert_called_once_with(item)

    def test_item_not_found(self, cart_service, cart_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        cart_item_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.remove_item(1, 1, 99)

        assert str(exc.value) == "No cart item found with id 99"


class TestClear:
    def test_success(self, cart_service, cart_repo, cart_item_repo):
        cart_repo.get_by_id.return_value = make_cart()
        items = [make_cart_item(), make_cart_item(id=2)]
        cart_repo.get_with_items.return_value = items

        result = cart_service.clear(1, 1)

        assert result is not None
        assert cart_item_repo.delete.call_count == 2

    def test_not_found(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.clear(1, 1)

        assert str(exc.value) == "No cart found with id 1"


class TestDelete:
    def test_success(self, cart_service, cart_repo):
        cart = make_cart()
        cart_repo.get_by_id.return_value = cart

        result = cart_service.delete(1, 1)

        assert result is cart
        cart_repo.delete.assert_called_once_with(cart)

    def test_not_found(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            cart_service.delete(1, 1)

        assert str(exc.value) == "No cart found with id 1"

    def test_not_owned(self, cart_service, cart_repo):
        cart_repo.get_by_id.return_value = make_cart(user_id=2)

        with pytest.raises(ValueError) as exc:
            cart_service.delete(1, 1)

        assert str(exc.value) == "Cart is not owned by user"


class TestLockDeEstoque:
    """Garante que a leitura do produto usa a versão com lock (FOR UPDATE).

    Em produção, sem `FOR UPDATE`, dois `add_item` simultâneos leem o mesmo
    `stock_qty` e ambos passam na validação (check-then-act race). Estes testes
    travam o comportamento: o service deve chamar `get_by_id_for_update`, e não
    a leitura simples.
    """

    def test_add_item_usa_leitura_com_lock(
        self, cart_service, cart_repo, product_repo, cart_item_repo
    ):
        cart_repo.get_by_id.return_value = make_cart()
        product_repo.get_by_id.return_value = make_product(stock_qty=10)
        cart_item_repo.get_by_cart_and_product.return_value = None

        cart_service.add_item(1, 1, 7, 1)

        product_repo.get_by_id_for_update.assert_called_once_with(7)

    def test_update_item_para_cima_usa_leitura_com_lock(
        self, cart_service, cart_repo, cart_item_repo, product_repo
    ):
        cart_repo.get_by_id.return_value = make_cart()
        cart_item_repo.get_by_id.return_value = make_cart_item(
            product_id=7, quantity=1
        )
        product_repo.get_by_id.return_value = make_product(stock_qty=10)

        cart_service.update_item(1, 1, 1, 5)

        product_repo.get_by_id_for_update.assert_called_once_with(7)

    def test_update_item_para_baixo_nao_precisa_de_lock(
        self, cart_service, cart_repo, cart_item_repo, product_repo
    ):
        """Reduzir quantidade nunca esbarra no estoque — não vale travar a linha."""
        cart_repo.get_by_id.return_value = make_cart()
        cart_item_repo.get_by_id.return_value = make_cart_item(quantity=5)

        cart_service.update_item(1, 1, 1, 2)

        product_repo.get_by_id_for_update.assert_not_called()

    def test_update_item_sem_estoque_suficiente(self, cart_service, cart_repo, cart_item_repo, product_repo):
        cart_repo.get_by_id.return_value = make_cart()
        cart_item_repo.get_by_id.return_value = make_cart_item(quantity=1)
        product_repo.get_by_id.return_value = make_product(stock_qty=3)

        with pytest.raises(ValueError) as exc:
            cart_service.update_item(1, 1, 1, 10)

        assert "Insufficient stock" in str(exc.value)


class TestProductRepositoryLock:
    """A query do repositório precisa emitir FOR UPDATE de verdade."""

    def test_get_by_id_for_update_emite_for_update(self):
        from unittest.mock import MagicMock

        from app.repositories.product_repo import ProductRepository

        session = MagicMock(name="session")
        repo = ProductRepository(session)

        repo.get_by_id_for_update(42)

        # session.query(Product).filter(...).with_for_update().first()
        chain = session.query.return_value.filter.return_value
        assert chain.with_for_update.called, (
            "get_by_id_for_update deve chamar .with_for_update() — sem isso o "
            "lock não existe e a race condition de estoque volta."
        )
        assert chain.with_for_update.return_value.first.called
