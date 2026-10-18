from app.api.exceptions import (
    DuplicateReviewException,
    NotFoundException,
    ProductNotFoundException,
    ReviewForbiddenException,
    UserNotFoundException,
)
from app.models.review import Review
from app.models.user import User, UserRole
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.repositories.user_repo import UserRepository


class ReviewService:


    def __init__(self, db):
        self.repo = ReviewRepository(db)
        self.user_repo = UserRepository(db)
        self.product_repo = ProductRepository(db)
        self.session = db

    @staticmethod
    def _is_admin(current_user: User) -> bool:
        return current_user.role == UserRole.ADMIN

    def _ensure_owner_or_admin(self, current_user: User, user_id: int) -> None:

        if self._is_admin(current_user):
            return
        if current_user.id != user_id:
            raise ReviewForbiddenException()

    def get_by_user_id(
        self, current_user: User, user_id: int | None = None
    ) -> list:
        alvo = current_user.id if user_id is None else user_id
        self._ensure_owner_or_admin(current_user, alvo)

        user = self.user_repo.get_by_id(alvo)

        if user is None:
            raise UserNotFoundException(user_id=alvo)

        reviews = user.reviews


        return reviews

    def get_paginated_by_user_id(
        self,
        current_user: User,
        user_id: int | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:

        from app.schemas.common import montar_pagina

        alvo = current_user.id if user_id is None else user_id
        self._ensure_owner_or_admin(current_user, alvo)

        user = self.user_repo.get_by_id(alvo)
        if user is None:
            raise UserNotFoundException(user_id=alvo)

        items, total = self.repo.paginate_by_user_id(alvo, page, per_page)
        return montar_pagina(items, page, per_page, total)

    def get_paginated_by_product_id(
        self, product_id: int, page: int = 1, per_page: int = 20
    ) -> dict:

        from app.schemas.common import montar_pagina

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundException()

        items, total = self.repo.paginate_by_product_id(
            product_id, page, per_page
        )
        return montar_pagina(items, page, per_page, total)

    def get_by_product_id(self, product_id: int) -> list:
        product = self.product_repo.get_by_id(product_id)

        if product is None:
            raise ProductNotFoundException()

        return self.repo.get_by_product_id(product_id)

    def create(self, current_user: User, data) -> Review:
        with self.session.begin():
            user = self.user_repo.get_by_id(current_user.id)

            if user is None:
                raise UserNotFoundException(user_id=current_user.id)

            product = self.product_repo.get_by_id(data.product_id)

            if product is None:
                raise ProductNotFoundException()

            existing_review = self.repo.get_by_user_id_and_product_id(
                current_user.id, data.product_id
            )

            if existing_review is not None:
                raise DuplicateReviewException()

            review = self.repo.create(
                Review(
                    user_id=current_user.id,
                    product_id=data.product_id,
                    rating=data.rating,
                    comment=data.comment,
                )
            )

            return review

    def update(self, review_id: int, data, current_user: User) -> Review:
        with self.session.begin():
            review = self.repo.get_by_id(review_id)

            if review is None:
                raise NotFoundException(
                    "Avaliação não encontrada.", code="REVIEW_NOT_FOUND"
                )

            self._ensure_owner_or_admin(current_user, review.user_id)

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(review, field, value)

            self.repo.update(review)

            self.session.refresh(review)
            return review

    def delete(self, review_id: int, current_user: User) -> Review:
        with self.session.begin():
            review = self.repo.get_by_id(review_id)

            if review is None:
                raise NotFoundException(
                    "Avaliação não encontrada.", code="REVIEW_NOT_FOUND"
                )

            self._ensure_owner_or_admin(current_user, review.user_id)

            self.repo.delete(review)
            return review
