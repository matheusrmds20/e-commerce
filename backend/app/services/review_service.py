from app.models.review import Review
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.repositories.user_repo import UserRepository


class ReviewService:
    def __init__(self, db):
        self.repo = ReviewRepository(db)
        self.user_repo = UserRepository(db)
        self.product_repo = ProductRepository(db)
        self.session = db

    def get_by_id(self, review_id: int, user_id: int) -> dict:
        review = self.repo.get_by_id(review_id)

        if review is None:
            raise ValueError(f"No review found with id {review_id}")

        if review.user_id != user_id:
            raise ValueError("Review is not owned by user")

        return review

    def get_by_user_id(self, user_id: int) -> list:
        user = self.user_repo.get_by_id(user_id)

        if user is None:
            raise ValueError(f"No user found with id {user_id}")

        reviews = user.reviews

        if not reviews:
            raise ValueError(f"No reviews found with user_id {user_id}")

        return reviews

    def get_by_product_id(self, product_id: int) -> list:
        product = self.product_repo.get_by_id(product_id)

        if product is None:
            raise ValueError(f"No product found with id {product_id}")

        reviews = self.repo.get_by_product_id(product_id)

        if not reviews:
            raise ValueError(f"No reviews found with product_id {product_id}")

        return reviews

    def get_by_rating(self, rating: int) -> list:
        reviews = self.repo.get_by_rating(rating)

        if not reviews:
            raise ValueError(f"No reviews found with rating {rating}")

        return reviews

    def get_all(self) -> list:
        reviews = self.repo.get_all()

        if not reviews:
            raise ValueError("No reviews found")

        return reviews



    def create(self, user_id: int, data) -> dict:
        with self.session.begin():

            user = self.user_repo.get_by_id(user_id)

            if user is None:
                raise ValueError(f"No user found with id {user_id}")

            product = self.product_repo.get_by_id(data.product_id)

            if product is None:
                raise ValueError(f"No product found with id {data.product_id}")

            existing_review = self.repo.get_by_user_id_and_product_id(user_id, data.product_id)
            
            if existing_review is not None:
                raise ValueError(
                    f"User {user_id} already reviewed product {data.product_id}"
                )

            review = self.repo.create(
                Review(
                    user_id=user_id,
                    product_id=data.product_id,
                    rating=data.rating,
                    comment=data.comment,
                )
            )

            return review

    def update(self, review_id: int, user_id: int, data) -> dict:
        with self.session.begin():

            review = self.repo.get_by_id(review_id)

            if review is None:
                raise ValueError(f"No review found with id {review_id}")

            if review.user_id != user_id:
                raise ValueError("Review is not owned by user")

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(review, field, value)

            self.repo.update(review)

            self.session.refresh(review)
            return review

    def delete(self, review_id: int, user_id: int) -> dict:
        with self.session.begin():

            review = self.repo.get_by_id(review_id)

            if review is None:
                raise ValueError(f"No review found with id {review_id}")

            if review.user_id != user_id:
                raise ValueError("Review is not owned by user")

            self.repo.delete(review)
            return review

