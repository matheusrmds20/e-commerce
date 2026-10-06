import pytest

from app.api.exceptions import (
    DuplicateReviewException,
    NotFoundException,
    ProductNotFoundException,
    ReviewForbiddenException,
    UserNotFoundException,
)
from app.models.product import Product
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate, ReviewUpdate


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


def make_admin(**kwargs):
    return make_user(id=99, role=UserRole.ADMIN, **kwargs)


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


def make_review(**kwargs):
    fields = dict(id=1, user_id=1, product_id=1, rating=5)
    fields.update(kwargs)
    return Review(**fields)


class TestGetByUserId:
    def test_own_reviews(self, review_service, user_repo):
        user = make_user()
        reviews = [make_review()]
        user.reviews = reviews
        user_repo.get_by_id.return_value = user

        assert review_service.get_by_user_id(make_user()) == reviews

    def test_other_user_forbidden(self, review_service, user_repo):
        user = make_user()
        user.reviews = [make_review()]
        user_repo.get_by_id.return_value = user

        with pytest.raises(ReviewForbiddenException):
            review_service.get_by_user_id(make_user(id=2), 1)

    def test_admin_can_target_any_user(self, review_service, user_repo):
        user = make_user()
        reviews = [make_review()]
        user.reviews = reviews
        user_repo.get_by_id.return_value = user

        assert review_service.get_by_user_id(make_admin(), 1) == reviews

    def test_user_not_found(self, review_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            review_service.get_by_user_id(make_user())

    def test_no_reviews(self, review_service, user_repo):
        """Sem avaliações devolve [] (estado normal), não erro."""
        user = make_user()
        user.reviews = []
        user_repo.get_by_id.return_value = user

        assert review_service.get_by_user_id(make_user()) == []


class TestGetByProductId:
    def test_success(self, review_service, product_repo, review_repo):
        product_repo.get_by_id.return_value = make_product()
        reviews = [make_review()]
        review_repo.get_by_product_id.return_value = reviews

        assert review_service.get_by_product_id(1) == reviews

    def test_product_not_found(self, review_service, product_repo):
        product_repo.get_by_id.return_value = None

        with pytest.raises(ProductNotFoundException):
            review_service.get_by_product_id(99)

    def test_no_reviews_returns_empty(self, review_service, product_repo, review_repo):
        product_repo.get_by_id.return_value = make_product()
        review_repo.get_by_product_id.return_value = []

        # Produto válido sem avaliações devolve lista vazia (não é erro).
        assert review_service.get_by_product_id(1) == []


class TestCreate:
    def test_success(self, review_service, user_repo, product_repo, review_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = make_product()
        review_repo.get_by_user_id_and_product_id.return_value = None
        review = make_review()
        review_repo.create.return_value = review

        result = review_service.create(
            make_user(), ReviewCreate(product_id=1, rating=5, comment="Ótimo")
        )

        assert result is review
        created = review_repo.create.call_args[0][0]
        assert created.user_id == 1
        assert created.product_id == 1
        assert created.rating == 5

    def test_user_not_found(self, review_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            review_service.create(
                make_user(), ReviewCreate(product_id=1, rating=5)
            )

    def test_product_not_found(self, review_service, user_repo, product_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = None

        with pytest.raises(ProductNotFoundException):
            review_service.create(
                make_user(), ReviewCreate(product_id=99, rating=5)
            )

    def test_duplicate_review(self, review_service, user_repo, product_repo, review_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = make_product()
        review_repo.get_by_user_id_and_product_id.return_value = make_review()

        with pytest.raises(DuplicateReviewException):
            review_service.create(
                make_user(), ReviewCreate(product_id=1, rating=5)
            )


class TestUpdate:
    def test_success(self, review_service, review_repo):
        review = make_review()
        review_repo.get_by_id.return_value = review
        review_repo.update.return_value = review

        result = review_service.update(1, ReviewUpdate(rating=4), make_user())

        assert result is review
        assert review.rating == 4
        review_repo.update.assert_called_once_with(review)

    def test_not_found(self, review_service, review_repo):
        review_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            review_service.update(99, ReviewUpdate(rating=4), make_user())

    def test_not_owned(self, review_service, review_repo):
        review_repo.get_by_id.return_value = make_review(user_id=2)

        with pytest.raises(ReviewForbiddenException):
            review_service.update(1, ReviewUpdate(rating=4), make_user())

    def test_admin_can_update_any_review(self, review_service, review_repo):
        review = make_review(user_id=2)
        review_repo.get_by_id.return_value = review
        review_repo.update.return_value = review

        result = review_service.update(1, ReviewUpdate(rating=3), make_admin())

        assert result is review
        assert review.rating == 3


class TestDelete:
    def test_success(self, review_service, review_repo):
        review = make_review()
        review_repo.get_by_id.return_value = review

        result = review_service.delete(1, make_user())

        assert result is review
        review_repo.delete.assert_called_once_with(review)

    def test_not_found(self, review_service, review_repo):
        review_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            review_service.delete(99, make_user())

    def test_not_owned(self, review_service, review_repo):
        review_repo.get_by_id.return_value = make_review(user_id=2)

        with pytest.raises(ReviewForbiddenException):
            review_service.delete(1, make_user())

    def test_admin_can_delete_any_review(self, review_service, review_repo):
        review = make_review(user_id=2)
        review_repo.get_by_id.return_value = review

        result = review_service.delete(1, make_admin())

        assert result is review
        review_repo.delete.assert_called_once_with(review)
