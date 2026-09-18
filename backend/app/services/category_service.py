from app.repositories.category_repo import CategoryRepository
from app.models.category import Category



class CategoryService:
    def __init__(self, db):
        self.repo = CategoryRepository(db)
        self.session = db

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

    def create(self, data) -> Category:
        with self.session.begin():

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

    def update(self, category_id: int, data) -> Category:
        with self.session.begin():

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

    def delete(self, category_id: int) -> Category:
        with self.session.begin():

            category = self.repo.get_by_id(category_id)

            if category is None:
                raise ValueError(f"No category found with id {category_id}")

            self.repo.delete(category)
            return category

