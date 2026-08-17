from datetime import datetime

import pytest

from app.models.product import Product
from app.models.user import User, UserRole
from app.models.wishlist import Wishlist
from app.schemas.wishlist import WishlistCreate, WishlistUpdate


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


def make_wishlist(**kwargs):
    fields = dict(id=1, user_id=1, product_id=1)
    fields.update(kwargs)
    return Wishlist(**fields)


class TestGet:
    def test_get_by_id_success(self, wishlist_service, wishlist_repo):
        item = make_wishlist()
        wishlist_repo.get_by_id.return_value = item

        assert wishlist_service.get_by_id(1, 1) is item

    def test_get_by_id_not_found(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_by_id(99, 1)

        assert str(exc.value) == "No wishlist item found with id 99"

    def test_get_by_id_not_owned(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_by_id.return_value = make_wishlist(user_id=2)

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_by_id(1, 1)

        assert str(exc.value) == "Wishlist item is not owned by user"

    def test_get_by_user_id_success(self, wishlist_service, user_repo):
        user = make_user()
        items = [make_wishlist()]
        user.wishlist_items = items
        user_repo.get_by_id.return_value = user

        assert wishlist_service.get_by_user_id(1) == items

    def test_get_by_user_id_user_not_found(self, wishlist_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_by_user_id(1)

        assert str(exc.value) == "No user found with id 1"

    def test_get_by_user_id_no_items(self, wishlist_service, user_repo):
        user = make_user()
        user.wishlist_items = []
        user_repo.get_by_id.return_value = user

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_by_user_id(1)

        assert str(exc.value) == "No wishlist items found with user_id 1"

    def test_get_by_product_id_success(self, wishlist_service, product_repo, wishlist_repo):
        product_repo.get_by_id.return_value = make_product()
        items = [make_wishlist()]
        wishlist_repo.get_by_product_id.return_value = items

        assert wishlist_service.get_by_product_id(1) == items

    def test_get_by_product_id_product_not_found(self, wishlist_service, product_repo):
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_by_product_id(99)

        assert str(exc.value) == "No product found with id 99"

    def test_get_by_product_id_no_items(self, wishlist_service, product_repo, wishlist_repo):
        product_repo.get_by_id.return_value = make_product()
        wishlist_repo.get_by_product_id.return_value = []

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_by_product_id(1)

        assert str(exc.value) == "No wishlist items found with product_id 1"

    def test_get_by_created_at_empty(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_by_created_at.return_value = []

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_by_created_at(datetime.now())

        assert "No wishlist items found" in str(exc.value)

    def test_get_by_updated_at_empty(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_by_updated_at.return_value = []

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_by_updated_at(datetime.now())

        assert "No wishlist items found" in str(exc.value)

    def test_get_all_success(self, wishlist_service, wishlist_repo):
        items = [make_wishlist()]
        wishlist_repo.get_all.return_value = items

        assert wishlist_service.get_all() == items

    def test_get_all_empty(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_all.return_value = []

        with pytest.raises(ValueError) as exc:
            wishlist_service.get_all()

        assert str(exc.value) == "No wishlist items found"


class TestCreate:
    def test_success(self, wishlist_service, user_repo, product_repo, wishlist_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = make_product()
        wishlist_repo.get_by_user_id.return_value = []
        item = make_wishlist()
        wishlist_repo.create.return_value = item

        result = wishlist_service.create(1, WishlistCreate(product_id=1))

        assert result is item
        created = wishlist_repo.create.call_args[0][0]
        assert created.user_id == 1
        assert created.product_id == 1

    def test_user_not_found(self, wishlist_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            wishlist_service.create(1, WishlistCreate(product_id=1))

        assert str(exc.value) == "No user found with id 1"

    def test_product_not_found(self, wishlist_service, user_repo, product_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            wishlist_service.create(1, WishlistCreate(product_id=99))

        assert str(exc.value) == "No product found with id 99"

    def test_duplicate_product(self, wishlist_service, user_repo, product_repo, wishlist_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = make_product()
        wishlist_repo.get_by_user_id.return_value = [make_wishlist(product_id=1)]

        with pytest.raises(ValueError) as exc:
            wishlist_service.create(1, WishlistCreate(product_id=1))

        assert "already has product" in str(exc.value)


class TestUpdate:
    def test_success(self, wishlist_service, wishlist_repo, product_repo):
        item = make_wishlist()
        wishlist_repo.get_by_id.return_value = item
        product_repo.get_by_id.return_value = make_product()
        wishlist_repo.get_by_user_id.return_value = [item]
        wishlist_repo.update.return_value = item

        result = wishlist_service.update(1, 1, WishlistUpdate(product_id=2))

        assert result is item
        assert item.product_id == 2
        wishlist_repo.update.assert_called_once_with(item)

    def test_not_found(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            wishlist_service.update(99, 1, WishlistUpdate(product_id=2))

        assert str(exc.value) == "No wishlist item found with id 99"

    def test_not_owned(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_by_id.return_value = make_wishlist(user_id=2)

        with pytest.raises(ValueError) as exc:
            wishlist_service.update(1, 1, WishlistUpdate(product_id=2))

        assert str(exc.value) == "Wishlist item is not owned by user"

    def test_duplicate_product(self, wishlist_service, wishlist_repo, product_repo):
        item = make_wishlist()
        other = make_wishlist(id=2, product_id=2)
        wishlist_repo.get_by_id.return_value = item
        product_repo.get_by_id.return_value = make_product()
        wishlist_repo.get_by_user_id.return_value = [item, other]

        with pytest.raises(ValueError) as exc:
            wishlist_service.update(1, 1, WishlistUpdate(product_id=2))

        assert "already has product" in str(exc.value)


class TestDelete:
    def test_success(self, wishlist_service, wishlist_repo):
        item = make_wishlist()
        wishlist_repo.get_by_id.return_value = item

        result = wishlist_service.delete(1, 1)

        assert result is item
        wishlist_repo.delete.assert_called_once_with(item)

    def test_not_found(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            wishlist_service.delete(99, 1)

        assert str(exc.value) == "No wishlist item found with id 99"

    def test_not_owned(self, wishlist_service, wishlist_repo):
        wishlist_repo.get_by_id.return_value = make_wishlist(user_id=2)

        with pytest.raises(ValueError) as exc:
            wishlist_service.delete(1, 1)

        assert str(exc.value) == "Wishlist item is not owned by user"
