from app.models.category import Category
from app.models.user import User, UserRole
from app.repositories.category_repo import CategoryRepository


class CategoryService:
    """Regras de categorias.

    SEGURANÇA: leitura (get_by_*/get_all) continua pública — o catálogo precisa
    listar categorias sem login. Escrita (create/update/delete) passou a exigir
    **administrador** (o usuário vem do token, resolvido pela rota). Antes
    qualquer anônimo podia criar/excluir categorias.
    """

    def __init__(self, db):
        self.repo = CategoryRepository(db)
        self.session = db

    @staticmethod
    def _ensure_admin(current_user: User) -> None:
        if current_user.role != UserRole.ADMIN:
            raise ValueError("Admin permission required to manage categories")

    def get_by_id(self, category_id: int) -> Category:
        category = self.repo.get_by_id(category_id)

        if category is None:
            raise ValueError(f"No category found with id {category_id}")

        return category

    def get_by_name(self, name: str) -> Category:
        category = self.repo.get_by_name(name)

        if category is None:
            raise ValueError(f"No category found with name {name}")

        return category

    def get_by_slug(self, slug: str) -> Category:
        category = self.repo.get_by_slug(slug)

        if category is None:
            raise ValueError(f"No category found with slug {slug}")

        return category

    def get_all(self) -> list:
        categories = self.repo.get_all()

        if categories is None:
            raise ValueError("No categories found")

        return categories

    def create(self, data, current_user: User) -> Category:
        with self.session.begin():
            self._ensure_admin(current_user)

            existing_name = self.repo.get_by_name(data.name)
            if existing_name is not None:
                raise ValueError(f"Category with name '{data.name}' already exists")

            existing_slug = self.repo.get_by_slug(data.slug)
            if existing_slug is not None:
                raise ValueError(f"Category with slug '{data.slug}' already exists")

            category = self.repo.create(
                Category(
                    name=data.name,
                    slug=data.slug,
                    image_url=data.image_url,
                    description=data.description,
                    is_active=data.is_active,
                    parent_id=data.parent_id,
                )
            )

            return category

    def update(self, category_id: int, data, current_user: User) -> Category:
        with self.session.begin():
            self._ensure_admin(current_user)

            category = self.repo.get_by_id(category_id)

            if category is None:
                raise ValueError(f"No category found with id {category_id}")

            if data.name is not None:
                existing_name = self.repo.get_by_name(data.name)
                if existing_name is not None and existing_name.id != category_id:
                    raise ValueError(f"Category with name '{data.name}' already exists")

            if data.slug is not None:
                existing_slug = self.repo.get_by_slug(data.slug)
                if existing_slug is not None and existing_slug.id != category_id:
                    raise ValueError(f"Category with slug '{data.slug}' already exists")

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(category, field, value)

            self.repo.update(category)

            return category

    def delete(self, category_id: int, current_user: User) -> Category:
        with self.session.begin():
            self._ensure_admin(current_user)

            category = self.repo.get_by_id(category_id)

            if category is None:
                raise ValueError(f"No category found with id {category_id}")

            self.repo.delete(category)
            return category

