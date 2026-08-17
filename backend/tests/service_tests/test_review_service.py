import pytest

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


class TestGet:
    def test_get_by_id_success(self, review_service, review_repo):
        review = make_review()
        review_repo.get_by_id.return_value = review

        assert review_service.get_by_id(1, 1) is review

    def test_get_by_id_not_found(self, review_service, review_repo):
        review_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            review_service.get_by_id(99, 1)

        assert str(exc.value) == "No review found with id 99"

    def test_get_by_id_not_owned(self, review_service, review_repo):
        review_repo.get_by_id.return_value = make_review(user_id=2)

        with pytest.raises(ValueError) as exc:
            review_service.get_by_id(1, 1)

        assert str(exc.value) == "Review is not owned by user"

    def test_get_by_user_id_success(self, review_service, user_repo):
        user = make_user()
        reviews = [make_review()]
        user.reviews = reviews
        user_repo.get_by_id.return_value = user

        assert review_service.get_by_user_id(1) == reviews

    def test_get_by_user_id_user_not_found(self, review_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            review_service.get_by_user_id(1)

        assert str(exc.value) == "No user found with id 1"

    def test_get_by_user_id_no_reviews(self, review_service, user_repo):
        user = make_user()
        user.reviews = []
        user_repo.get_by_id.return_value = user

        with pytest.raises(ValueError) as exc:
            review_service.get_by_user_id(1)

        assert str(exc.value) == "No reviews found with user_id 1"

    def test_get_by_product_id_success(self, review_service, product_repo, review_repo):
        product_repo.get_by_id.return_value = make_product()
        reviews = [make_review()]
        review_repo.get_by_product_id.return_value = reviews

        assert review_service.get_by_product_id(1) == reviews

    def test_get_by_product_id_product_not_found(self, review_service, product_repo):
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            review_service.get_by_product_id(99)

        assert str(exc.value) == "No product found with id 99"

    def test_get_by_product_id_no_reviews(self, review_service, product_repo, review_repo):
        product_repo.get_by_id.return_value = make_product()
        review_repo.get_by_product_id.return_value = []

        with pytest.raises(ValueError) as exc:
            review_service.get_by_product_id(1)

        assert str(exc.value) == "No reviews found with product_id 1"

    def test_get_by_rating_success(self, review_service, review_repo):
        reviews = [make_review()]
        review_repo.get_by_rating.return_value = reviews

        assert review_service.get_by_rating(5) == reviews

    def test_get_by_rating_empty(self, review_service, review_repo):
        review_repo.get_by_rating.return_value = []

        with pytest.raises(ValueError) as exc:
            review_service.get_by_rating(5)

        assert str(exc.value) == "No reviews found with rating 5"

    def test_get_all_success(self, review_service, review_repo):
        reviews = [make_review()]
        review_repo.get_all.return_value = reviews

        assert review_service.get_all() == reviews

    def test_get_all_empty(self, review_service, review_repo):
        review_repo.get_all.return_value = []

        with pytest.raises(ValueError) as exc:
            review_service.get_all()

        assert str(exc.value) == "No reviews found"


class TestCreate:
    def test_success(self, review_service, user_repo, product_repo, review_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = make_product()
        review_repo.get_by_user_id_and_product_id.return_value = None
        review = make_review()
        review_repo.create.return_value = review

        result = review_service.create(1, ReviewCreate(product_id=1, rating=5, comment="Ótimo"))

        assert result is review
        created = review_repo.create.call_args[0][0]
        assert created.user_id == 1
        assert created.product_id == 1
        assert created.rating == 5

    def test_user_not_found(self, review_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            review_service.create(1, ReviewCreate(product_id=1, rating=5))

        assert str(exc.value) == "No user found with id 1"

    def test_product_not_found(self, review_service, user_repo, product_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            review_service.create(1, ReviewCreate(product_id=99, rating=5))

        assert str(exc.value) == "No product found with id 99"

    def test_duplicate_review(self, review_service, user_repo, product_repo, review_repo):
        user_repo.get_by_id.return_value = make_user()
        product_repo.get_by_id.return_value = make_product()
        review_repo.get_by_user_id_and_product_id.return_value = make_review()

        with pytest.raises(ValueError) as exc:
            review_service.create(1, ReviewCreate(product_id=1, rating=5))

        assert "already reviewed" in str(exc.value)


class TestUpdate:
    def test_success(self, review_service, review_repo):
        review = make_review()
        review_repo.get_by_id.return_value = review
        review_repo.update.return_value = review

        result = review_service.update(1, 1, ReviewUpdate(rating=4))

        assert result is review
        assert review.rating == 4
        review_repo.update.assert_called_once_with(review)

    def test_not_found(self, review_service, review_repo):
        review_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            review_service.update(99, 1, ReviewUpdate(rating=4))

        assert str(exc.value) == "No review found with id 99"

    def test_not_owned(self, review_service, review_repo):
        review_repo.get_by_id.return_value = make_review(user_id=2)

        with pytest.raises(ValueError) as exc:
            review_service.update(1, 1, ReviewUpdate(rating=4))

        assert str(exc.value) == "Review is not owned by user"


class TestDelete:
    def test_success(self, review_service, review_repo):
        review = make_review()
        review_repo.get_by_id.return_value = review

        result = review_service.delete(1, 1)

        assert result is review
        review_repo.delete.assert_called_once_with(review)

    def test_not_found(self, review_service, review_repo):
        review_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            review_service.delete(99, 1)

        assert str(exc.value) == "No review found with id 99"

    def test_not_owned(self, review_service, review_repo):
        review_repo.get_by_id.return_value = make_review(user_id=2)

        with pytest.raises(ValueError) as exc:
            review_service.delete(1, 1)

        assert str(exc.value) == "Review is not owned by user"
