import pytest

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


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

        with pytest.raises(ValueError) as exc:
            category_service.get_by_id(99)

        assert str(exc.value) == "No category found with id 99"

    def test_get_by_name_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_name.return_value = category

        assert category_service.get_by_name("Ficção") is category

    def test_get_by_name_not_found(self, category_service, category_repo):
        category_repo.get_by_name.return_value = None

        with pytest.raises(ValueError) as exc:
            category_service.get_by_name("Inexistente")

        assert str(exc.value) == "No category found with name Inexistente"

    def test_get_by_slug_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_slug.return_value = category

        assert category_service.get_by_slug("ficcao") is category

    def test_get_by_slug_not_found(self, category_service, category_repo):
        category_repo.get_by_slug.return_value = None

        with pytest.raises(ValueError) as exc:
            category_service.get_by_slug("sem-slug")

        assert str(exc.value) == "No category found with slug sem-slug"

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

        result = category_service.create(create_payload())

        assert result is category
        created = category_repo.create.call_args[0][0]
        assert created.name == "Ficção"
        assert created.slug == "ficcao"

    def test_create_name_already_exists(self, category_service, category_repo):
        category_repo.get_by_name.return_value = make_category()

        with pytest.raises(ValueError) as exc:
            category_service.create(create_payload())

        assert "already exists" in str(exc.value)

    def test_create_slug_already_exists(self, category_service, category_repo):
        category_repo.get_by_name.return_value = None
        category_repo.get_by_slug.return_value = make_category()

        with pytest.raises(ValueError) as exc:
            category_service.create(create_payload())

        assert "already exists" in str(exc.value)


class TestUpdate:
    def test_update_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_id.return_value = category
        category_repo.get_by_name.return_value = None
        category_repo.get_by_slug.return_value = None
        category_repo.update.return_value = category

        result = category_service.update(1, CategoryUpdate(name="Terror"))

        assert result is category
        assert category.name == "Terror"
        category_repo.update.assert_called_once_with(category)

    def test_update_not_found(self, category_service, category_repo):
        category_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            category_service.update(1, CategoryUpdate(name="Terror"))

        assert str(exc.value) == "No category found with id 1"

    def test_update_name_conflict(self, category_service, category_repo):
        category = make_category()
        other = make_category(id=2, name="Terror")
        category_repo.get_by_id.return_value = category
        category_repo.get_by_name.return_value = other

        with pytest.raises(ValueError) as exc:
            category_service.update(1, CategoryUpdate(name="Terror"))

        assert "already exists" in str(exc.value)

    def test_update_slug_conflict(self, category_service, category_repo):
        category = make_category()
        other = make_category(id=2, slug="terror")
        category_repo.get_by_id.return_value = category
        category_repo.get_by_name.return_value = None
        category_repo.get_by_slug.return_value = other

        with pytest.raises(ValueError) as exc:
            category_service.update(1, CategoryUpdate(slug="terror"))

        assert "already exists" in str(exc.value)


class TestDelete:
    def test_delete_success(self, category_service, category_repo):
        category = make_category()
        category_repo.get_by_id.return_value = category

        result = category_service.delete(1)

        assert result is category
        category_repo.delete.assert_called_once_with(category)

    def test_delete_not_found(self, category_service, category_repo):
        category_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            category_service.delete(1)

        assert str(exc.value) == "No category found with id 1"
