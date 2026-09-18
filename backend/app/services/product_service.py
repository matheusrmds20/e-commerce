from app.models.product import Product
from app.repositories.category_repo import CategoryRepository
from app.repositories.product_repo import ProductRepository


class ProductService:
    def __init__(self, db):
        self.repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.session = db

    def get_by_id(self, product_id: int) -> dict:
        product = self.repo.get_by_id(product_id)

        if product is None:
            raise ValueError(f"No product found with id {product_id}")

        return product

    def get_by_title(self, title: str) -> dict:
        product = self.repo.get_by_title(title)

        if product is None:
            raise ValueError(f"No product found with title '{title}'")

        return product

    def get_by_slug(self, slug: str) -> dict:
        product = self.repo.get_by_slug(slug)

        if product is None:
            raise ValueError(f"No product found with slug '{slug}'")

        return product

    def get_by_isbn(self, isbn: str) -> dict:
        product = self.repo.get_by_isbn(isbn)

        if product is None:
            raise ValueError(f"No product found with ISBN '{isbn}'")

        return product

    def get_by_category_id(self, category_id: int) -> list:
        products = self.repo.get_by_category_id(category_id)

        if not products:
            raise ValueError(f"No products found with category_id {category_id}")

        return products

    def get_by_publisher(self, publisher: str) -> list:
        products = self.repo.get_by_publisher(publisher)

        if not products:
            raise ValueError(f"No products found with publisher '{publisher}'")

        return products

    def get_by_publication_year(self, publication_year: int) -> list:
        products = self.repo.get_by_publication_year(publication_year)

        if not products:
            raise ValueError(f"No products found with publication_year {publication_year}")

        return products


    def get_by_language(self, language: str) -> list:
        products = self.repo.get_by_language(language)

        if not products:
            raise ValueError(f"No products found with language '{language}'")

        return products

    def get_by_discount_pct(self, discount_pct: int) -> list:
        """Produtos com desconto de pelo menos `discount_pct`.

        Não levanta erro quando vazio: "nenhum produto em promoção" é um estado
        normal de catálogo, e o carrossel da Home deve receber `[]` (200) em vez
        de estourar 500.
        """
        return self.repo.get_by_discount_pct(discount_pct)

    def get_by_stock_qty(self, stock_qty: int) -> list:
        products = self.repo.get_by_stock_qty(stock_qty)

        if not products:
            raise ValueError(f"No products found with stock_qty {stock_qty}")

        return products

    def get_by_is_active(self, is_active: bool) -> list:
        products = self.repo.get_by_is_active(is_active)

        if not products:
            raise ValueError(f"No products found with is_active {is_active}")

        return products

    def get_featured(self, limit: int | None = None) -> list:
        """Produtos em destaque para a vitrine.

        Diferente dos demais `get_by_*`, NÃO levanta erro quando a lista está
        vazia: "nenhum destaque marcado" é um estado normal de curadoria, e a
        Home deve receber `[]` (HTTP 200) em vez de 400.
        """
        return self.repo.get_featured(limit)

    def get_bestsellers(self, limit: int | None = None) -> list:
        """Produtos mais vendidos (curadoria manual) para a vitrine.

        Mesma regra de `get_featured`: lista vazia é resposta válida.
        """
        return self.repo.get_bestsellers(limit)

    def get_recommendations(
        self,
        exclude_ids: list[int] | None = None,
        limit: int = 4,
    ) -> list:
        """Recomendações para o carrinho.

        Não levanta erro quando vazio (catálogo pequeno ou tudo já na sacola):
        o carrinho apenas não mostra a seção de recomendados.
        """
        return self.repo.get_recommendations(exclude_ids, limit)

    def get_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        category_id: int | None = None,
    ) -> dict:
        """Catálogo paginado no formato do envelope `Page[T]`.

        Retorna `{"data": [...], "meta": {...}}`. A paginação e o filtro por
        categoria acontecem no banco (`WHERE` + `offset`/`limit`), então o custo
        não cresce com o tamanho do catálogo.

        Quando `category_id` é informado, a categoria precisa existir: um id
        inválido é erro do cliente (404), não um catálogo vazio.
        """
        if category_id is not None:
            categoria = self.category_repo.get_by_id(category_id)
            if categoria is None:
                raise ValueError(f"No category found with id {category_id}")

        items, total = self.repo.paginate(page, per_page, category_id)
        total_pages = (total + per_page - 1) // per_page if per_page else 0

        return {
            "data": items,
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }

    def get_all(self) -> list:
        products = self.repo.get_all()

        if not products:
            raise ValueError("No products found")

        return products


    def create(self, data) -> dict:
        with self.session.begin():

            category = self.category_repo.get_by_id(data.category_id)

            if category is None:
                raise ValueError(f"No category found with id {data.category_id}")

            existing_title = self.repo.get_by_title(data.title)
            if existing_title is not None:
                raise ValueError(f"Product with title '{data.title}' already exists")

            existing_slug = self.repo.get_by_slug(data.slug)
            if existing_slug is not None:
                raise ValueError(f"Product with slug '{data.slug}' already exists")

            product = self.repo.create(
                Product(
                    category_id=data.category_id,
                    title=data.title,
                    slug=data.slug,
                    description=data.description,
                    price=data.price,
                    image_url=data.image_url,
                    is_active=data.is_active,
                    # Flags de curadoria da vitrine. Sem repassar aqui, o admin
                    # não conseguiria marcar um produto e `/products/featured`
                    # ficaria sempre vazio.
                    is_featured=data.is_featured,
                    is_bestseller=data.is_bestseller,
                    author=data.author,
                    isbn=data.isbn,
                    publisher=data.publisher,
                    publication_year=data.publication_year,
                    pages=data.pages,
                    language=data.language,
                    synopsis=data.synopsis,
                    discount_pct=data.discount_pct,
                    stock_qty=data.stock_qty,
                )
            )

            return product

    def update(self, product_id: int, data) -> dict:
        with self.session.begin():

            product = self.repo.get_by_id(product_id)

            if product is None:
                raise ValueError(f"No product found with id {product_id}")

            if data.category_id is not None:
                category = self.category_repo.get_by_id(data.category_id)
                if category is None:
                    raise ValueError(f"No category found with id {data.category_id}")

            if data.title is not None:
                existing_title = self.repo.get_by_title(data.title)
                if existing_title is not None and existing_title.id != product_id:
                    raise ValueError(f"Product with title '{data.title}' already exists")

            if data.slug is not None:
                existing_slug = self.repo.get_by_slug(data.slug)
                if existing_slug is not None and existing_slug.id != product_id:
                    raise ValueError(f"Product with slug '{data.slug}' already exists")

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(product, field, value)

            self.repo.update(product)

            return product

    def delete(self, product_id: int) -> dict:
        with self.session.begin():

            product = self.repo.get_by_id(product_id)

            if product is None:
                raise ValueError(f"No product found with id {product_id}")

            self.repo.delete(product)
            return product

