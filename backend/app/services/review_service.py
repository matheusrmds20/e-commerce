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
    """Regras de avaliações.

    SEGURANÇA: o autor da avaliação NÃO vem mais da query string (``user_id``),
    e sim do usuário autenticado (``current_user``, resolvido do token pela
    rota). Isso fecha o IDOR que permitia criar/editar/excluir avaliações em
    nome de outra pessoa. Um cliente comum só lê/altera as próprias
    avaliações; administradores podem operar sobre qualquer uma. Violações de
    posse viram ``ReviewForbiddenException`` na camada de API.
    """

    def __init__(self, db):
        self.repo = ReviewRepository(db)
        self.user_repo = UserRepository(db)
        self.product_repo = ProductRepository(db)
        self.session = db

    @staticmethod
    def _is_admin(current_user: User) -> bool:
        return current_user.role == UserRole.ADMIN

    def _ensure_owner_or_admin(self, current_user: User, user_id: int) -> None:
        """Garante que o autenticado só acesse a própria avaliação (ou seja admin)."""
        if self._is_admin(current_user):
            return
        if current_user.id != user_id:
            raise ReviewForbiddenException()

    def get_by_user_id(
        self, current_user: User, user_id: int | None = None
    ) -> list:
        """Lista as avaliações de um usuário ("minhas avaliações").

        Sem ``user_id`` devolve as do próprio autenticado. Com ``user_id``
        diferente, só administradores são aceitos.
        """
        alvo = current_user.id if user_id is None else user_id
        self._ensure_owner_or_admin(current_user, alvo)

        user = self.user_repo.get_by_id(alvo)

        if user is None:
            raise UserNotFoundException(user_id=alvo)

        reviews = user.reviews

        # Sem avaliações é estado normal (lista vazia), não erro.
        return reviews

    def get_by_product_id(self, product_id: int) -> list:
        product = self.product_repo.get_by_id(product_id)

        if product is None:
            raise ProductNotFoundException()

        # Produto válido sem avaliações é um estado normal (lista vazia), não um
        # erro. Retornar [] mantém o endpoint de listagem idempotente para a UI.
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
