
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session) -> None:
        super().__init__(Product, db)

    def get_by_id_for_update(self, product_id: int) -> Product | None:

        return (
            self.session.query(Product)
            .filter(Product.id == product_id)
            .with_for_update()
            .first()
        )

    def decrement_stock(self, product: Product, quantity: int) -> Product:

        if quantity < 0:
            raise ValueError("A quantidade a baixar não pode ser negativa")

        novo_saldo = product.stock_qty - quantity

        if novo_saldo < 0:
            raise ValueError(
                f"Estoque insuficiente para baixa: disponível "
                f"{product.stock_qty}, solicitado {quantity}"
            )

        product.stock_qty = novo_saldo
        self.session.add(product)
        return product

    def restock(self, product: Product, quantity: int) -> Product:

        if quantity < 0:
            raise ValueError("A quantidade a repor não pode ser negativa")

        product.stock_qty = product.stock_qty + quantity
        self.session.add(product)
        return product

    def get_by_category_id(self, category_id: int) -> list[Product]:
        return self.session.query(Product).filter(Product.category_id == category_id).all()

    def get_by_title(self, title: str) -> Product | None:
        return self.session.query(Product).filter(Product.title == title).first()

    def get_by_slug(self, slug: str) -> Product | None:
        return self.session.query(Product).filter(Product.slug == slug).first()

    def get_by_isbn(self, isbn: str) -> Product | None:
        return self.session.query(Product).filter(Product.isbn == isbn).first()

    def get_by_publisher(self, publisher: str) -> list[Product]:
        return self.session.query(Product).filter(Product.publisher == publisher).all()

    def get_by_publication_year(self, publication_year: int) -> list[Product]:
        return self.session.query(Product).filter(Product.publication_year == publication_year).all()

    def get_by_language(self, language: str) -> list[Product]:
        return self.session.query(Product).filter(Product.language == language).all()

    def get_by_discount_pct(self, discount_pct: int) -> list[Product]:
        return self.session.query(Product).filter(Product.discount_pct == discount_pct).all()

    def get_by_stock_qty(self, stock_qty: int) -> list[Product]:
        return self.session.query(Product).filter(Product.stock_qty == stock_qty).all()

    def get_by_is_active(self, is_active: bool) -> list[Product]:
        return self.session.query(Product).filter(Product.is_active == is_active).all()


