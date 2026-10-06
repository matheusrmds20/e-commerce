import pytest

from app.api.exceptions import (
    CategoryNotFoundException,
    ConflictException,
    InsufficientPermissionException,
)
from app.models.category import Category
from app.models.user import User, UserRole
from app.schemas.category import CategoryCreate, CategoryUpdate


def make_user(role=UserRole.ADMIN, **kwargs):
    fields = dict(
        id=99,
        email="admin@example.com",
        full_name="Admin",
        password_hash="hashed",
        role=role,
        is_active=True,
    )
    fields.update(kwargs)
    return User(**fields)


def make_category(**kwargs):
    fields = dict(id=1, name="Ficção", slug="ficcao", is_active=True)
    fields.update(kwargs)
    return Category(**fields)


def create_payload(**kwargs):
    fields = dict(name="Ficção", slug="ficcao")
    fields.update(kwargs)
    return CategoryCreate(**fields)


class TestGet:
    def test_get_by_id_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_id.return_value = category

        assert category_service.get_by_id(1) is category

    def test_get_by_id_not_found(self, category_service, category_repo):
        category_repo.get_by_id.return_value = None

        with pytest.raises(CategoryNotFoundException):
            category_service.get_by_id(99)

    def test_get_by_name_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_name.return_value = category

        assert category_service.get_by_name("Ficção") is category

    def test_get_by_name_not_found(self, category_service, category_repo):
        category_repo.get_by_name.return_value = None

        with pytest.raises(CategoryNotFoundException):
            category_service.get_by_name("Inexistente")

    def test_get_by_slug_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_slug.return_value = category

        assert category_service.get_by_slug("ficcao") is category

    def test_get_by_slug_not_found(self, category_service, category_repo):
        category_repo.get_by_slug.return_value = None

        with pytest.raises(CategoryNotFoundException):
            category_service.get_by_slug("sem-slug")

    def test_get_all_success(self, category_service, category_repo):
        categories = [make_category()]
        category_repo.get_all.return_value = categories

        assert category_service.get_all() == categories

    def test_get_all_empty(self, category_service, category_repo):
        category_repo.get_all.return_value = []

        assert category_service.get_all() == []


class TestCreate:
    def test_create_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_name.return_value = None
        category_repo.get_by_slug.return_value = None
        category_repo.create.return_value = category

        result = category_service.create(create_payload(), make_user())

        assert result is category
        created = category_repo.create.call_args[0][0]
        assert created.name == "Ficção"
        assert created.slug == "ficcao"

    def test_create_name_already_exists(self, category_service, category_repo):
        category_repo.get_by_name.return_value = make_category()

        with pytest.raises(ConflictException):
            category_service.create(create_payload(), make_user())

    def test_create_slug_already_exists(self, category_service, category_repo):
        category_repo.get_by_name.return_value = None
        category_repo.get_by_slug.return_value = make_category()

        with pytest.raises(ConflictException):
            category_service.create(create_payload(), make_user())


class TestUpdate:
    def test_update_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_id.return_value = category
        category_repo.get_by_name.return_value = None
        category_repo.get_by_slug.return_value = None
        category_repo.update.return_value = category

        result = category_service.update(1, CategoryUpdate(name="Terror"), make_user())

        assert result is category
        assert category.name == "Terror"
        category_repo.update.assert_called_once_with(category)

    def test_update_not_found(self, category_service, category_repo):
        category_repo.get_by_id.return_value = None

        with pytest.raises(CategoryNotFoundException):
            category_service.update(1, CategoryUpdate(name="Terror"), make_user())

    def test_update_name_conflict(self, category_service, category_repo):
        category = make_category()
        other = make_category(id=2, name="Terror")
        category_repo.get_by_id.return_value = category
        category_repo.get_by_name.return_value = other

        with pytest.raises(ConflictException):
            category_service.update(1, CategoryUpdate(name="Terror"), make_user())

    def test_update_slug_conflict(self, category_service, category_repo):
        category = make_category()
        other = make_category(id=2, slug="terror")
        category_repo.get_by_id.return_value = category
        category_repo.get_by_name.return_value = None
        category_repo.get_by_slug.return_value = other

        with pytest.raises(ConflictException):
            category_service.update(1, CategoryUpdate(slug="terror"), make_user())


class TestAdminPermission:
    def test_create_customer_forbidden(self, category_service, category_repo):
        with pytest.raises(InsufficientPermissionException):
            category_service.create(create_payload(), make_user(role=UserRole.CUSTOMER))

        category_repo.create.assert_not_called()

    def test_update_customer_forbidden(self, category_service, category_repo):
        with pytest.raises(InsufficientPermissionException):
            category_service.update(
                1, CategoryUpdate(name="Terror"), make_user(role=UserRole.CUSTOMER)
            )

        category_repo.update.assert_not_called()

    def test_delete_customer_forbidden(self, category_service, category_repo):
        with pytest.raises(InsufficientPermissionException):
            category_service.delete(1, make_user(role=UserRole.CUSTOMER))

        category_repo.delete.assert_not_called()


class TestDelete:
    def test_delete_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_id.return_value = category

        result = category_service.delete(1, make_user())

        assert result is category
        category_repo.delete.assert_called_once_with(category)

    def test_delete_not_found(self, category_service, category_repo):
        category_repo.get_by_id.return_value = None

        with pytest.raises(CategoryNotFoundException):
            category_service.delete(1, make_user())
