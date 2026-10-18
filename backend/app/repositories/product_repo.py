
from sqlalchemy import or_
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

    def get_by_discount_pct(self, discount_pct: int) -> list[Product]:

        return (
            self.session.query(Product)
            .filter(Product.discount_pct >= discount_pct)
            .order_by(Product.discount_pct.desc())
            .all()
        )

    def get_by_is_active(self, is_active: bool) -> list[Product]:
        return self.session.query(Product).filter(Product.is_active == is_active).all()

    def paginate(
        self,
        page: int,
        per_page: int,
        category_id: int | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Product], int]:

        query = self.session.query(Product)

        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        if is_active is not None:
            query = query.filter(Product.is_active.is_(is_active))
        if search:
            termo = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.title.ilike(termo),
                    Product.author.ilike(termo),
                    Product.isbn.ilike(termo),
                )
            )

        total = query.count()
        items = (
            query.order_by(Product.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def get_recommendations(
        self,
        exclude_ids: list[int] | None = None,
        limit: int = 4,
    ) -> list[Product]:

        query = self.session.query(Product).filter(
            Product.is_active.is_(True),
            Product.stock_qty > 0,
        )

        if exclude_ids:
            query = query.filter(Product.id.notin_(exclude_ids))

        return query.order_by(Product.id).limit(limit).all()

    def get_featured(self, limit: int | None = None) -> list[Product]:

        query = (
            self.session.query(Product)
            .filter(Product.is_featured.is_(True), Product.is_active.is_(True))
            .order_by(Product.id)
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_bestsellers(self, limit: int | None = None) -> list[Product]:

        query = (
            self.session.query(Product)
            .filter(Product.is_bestseller.is_(True), Product.is_active.is_(True))
            .order_by(Product.id)
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()


