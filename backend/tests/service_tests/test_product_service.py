import pytest

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def make_product(**kwargs):
    fields = dict(
        id=1,
        category_id=1,
        title="Livro Teste",
        slug="livro-teste",
        description="Descrição do livro",
        author="Autor",
        price=50.0,
        stock_qty=10,
        is_active=True,
        is_featured=False,
        is_bestseller=False,
    )
    fields.update(kwargs)
    return Product(**fields)


def make_category(**kwargs):
    fields = dict(id=1, name="Ficção", slug="ficcao", is_active=True)
    fields.update(kwargs)
    return Category(**fields)


def create_payload(**kwargs):
    fields = dict(
        category_id=1,
        title="Livro Teste",
        slug="livro-teste",
        description="Descrição do livro",
        price=50.0,
        author="Autor",
        isbn="978-123",
        stock_qty=10,
    )
    fields.update(kwargs)
    return ProductCreate(**fields)


@pytest.mark.parametrize(
    "method,repo_method,lookup",
    [
        ("get_by_id", "get_by_id", 99),
        ("get_by_title", "get_by_title", "não existe"),
        ("get_by_slug", "get_by_slug", "sem-slug"),
        ("get_by_isbn", "get_by_isbn", "000000"),
    ],
)
def test_get_single_success(product_service, product_repo, method, repo_method, lookup):
    product = make_product()
    getattr(product_repo, repo_method).return_value = product

    assert getattr(product_service, method)(lookup) is product


@pytest.mark.parametrize(
    "method,repo_method,lookup,message",
    [
        ("get_by_id", "get_by_id", 99, "No product found with id 99"),
        ("get_by_title", "get_by_title", "não existe", "No product found with title 'não existe'"),
        ("get_by_slug", "get_by_slug", "sem-slug", "No product found with slug 'sem-slug'"),
        ("get_by_isbn", "get_by_isbn", "000000", "No product found with ISBN '000000'"),
    ],
)
def test_get_single_not_found(product_service, product_repo, method, repo_method, lookup, message):
    getattr(product_repo, repo_method).return_value = None

    with pytest.raises(ValueError) as exc:
        getattr(product_service, method)(lookup)

    assert str(exc.value) == message


@pytest.mark.parametrize(
    "method,repo_method,lookup",
    [
        ("get_by_category_id", "get_by_category_id", 1),
        ("get_by_publisher", "get_by_publisher", "Editora X"),
        ("get_by_publication_year", "get_by_publication_year", 2020),
        ("get_by_language", "get_by_language", "pt-BR"),
        ("get_by_discount_pct", "get_by_discount_pct", 10),
        ("get_by_stock_qty", "get_by_stock_qty", 5),
        ("get_by_is_active", "get_by_is_active", True),
        ("get_all", "get_all", None),
    ],
)
def test_get_list_success(product_service, product_repo, method, repo_method, lookup):
    products = [make_product()]
    getattr(product_repo, repo_method).return_value = products

    if lookup is None:
        result = getattr(product_service, method)()
    else:
        result = getattr(product_service, method)(lookup)

    assert result == products


@pytest.mark.parametrize(
    "method,repo_method,lookup,message",
    [
        ("get_by_category_id", "get_by_category_id", 1, "No products found with category_id 1"),
        ("get_by_publisher", "get_by_publisher", "Editora X", "No products found with publisher 'Editora X'"),
        ("get_by_publication_year", "get_by_publication_year", 2020, "No products found with publication_year 2020"),
        ("get_by_language", "get_by_language", "pt-BR", "No products found with language 'pt-BR'"),
        # `get_by_discount_pct` NÃO entra aqui: lista vazia é resposta válida
        # (ausência de promoção não é erro). Coberto em TestVitrine.
        ("get_by_stock_qty", "get_by_stock_qty", 5, "No products found with stock_qty 5"),
        ("get_by_is_active", "get_by_is_active", True, "No products found with is_active True"),
        ("get_all", "get_all", None, "No products found"),
    ],
)
def test_get_list_empty(product_service, product_repo, method, repo_method, lookup, message):
    getattr(product_repo, repo_method).return_value = []

    with pytest.raises(ValueError) as exc:
        if lookup is None:
            getattr(product_service, method)()
        else:
            getattr(product_service, method)(lookup)

    assert str(exc.value) == message


class TestCreate:
    def test_create_success(self, product_service, product_repo, category_repo):
        category = make_category()
        product = make_product()
        category_repo.get_by_id.return_value = category
        product_repo.get_by_title.return_value = None
        product_repo.get_by_slug.return_value = None
        product_repo.create.return_value = product

        result = product_service.create(create_payload())

        assert result is product
        created = product_repo.create.call_args[0][0]
        assert created.category_id == 1
        assert created.title == "Livro Teste"
        assert created.slug == "livro-teste"
        assert created.price == 50.0
        assert created.stock_qty == 10

    def test_create_category_not_found(self, product_service, category_repo):
        category_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            product_service.create(create_payload())

        assert str(exc.value) == "No category found with id 1"

    def test_create_title_already_exists(self, product_service, category_repo, product_repo):
        category_repo.get_by_id.return_value = make_category()
        product_repo.get_by_title.return_value = make_product()

        with pytest.raises(ValueError) as exc:
            product_service.create(create_payload())

        assert "already exists" in str(exc.value)

    def test_create_slug_already_exists(self, product_service, category_repo, product_repo):
        category_repo.get_by_id.return_value = make_category()
        product_repo.get_by_title.return_value = None
        product_repo.get_by_slug.return_value = make_product()

        with pytest.raises(ValueError) as exc:
            product_service.create(create_payload())

        assert "already exists" in str(exc.value)


class TestUpdate:
    def test_update_success(self, product_service, product_repo):
        product = make_product()
        product_repo.get_by_id.return_value = product
        product_repo.update.return_value = product

        result = product_service.update(1, ProductUpdate(price=99.0))

        assert result is product
        assert product.price == 99.0
        product_repo.update.assert_called_once_with(product)

    def test_update_not_found(self, product_service, product_repo):
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            product_service.update(1, ProductUpdate(price=99.0))

        assert str(exc.value) == "No product found with id 1"

    def test_update_title_conflict(self, product_service, product_repo):
        product = make_product()
        other = make_product(id=2, title="Outro Livro")
        product_repo.get_by_id.return_value = product
        product_repo.get_by_title.return_value = other

        with pytest.raises(ValueError) as exc:
            product_service.update(1, ProductUpdate(title="Outro Livro"))

        assert "already exists" in str(exc.value)

    def test_update_category_not_found(self, product_service, product_repo, category_repo):
        product_repo.get_by_id.return_value = make_product()
        category_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            product_service.update(1, ProductUpdate(category_id=99))

        assert str(exc.value) == "No category found with id 99"


class TestDelete:
    def test_delete_success(self, product_service, product_repo):
        product = make_product()
        product_repo.get_by_id.return_value = product

        result = product_service.delete(1)

        assert result is product
        product_repo.delete.assert_called_once_with(product)

    def test_delete_not_found(self, product_service, product_repo):
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            product_service.delete(1)

        assert str(exc.value) == "No product found with id 1"


class TestVitrine:
    """Métodos de vitrine: get_featured e get_bestsellers.

    Contrato diferente dos demais `get_by_*`: lista vazia NÃO é erro. A Home
    deve receber [] para renderizar o estado vazio, em vez de estourar 400.
    """

    @pytest.mark.parametrize(
        "method,repo_method",
        [
            ("get_featured", "get_featured"),
            ("get_bestsellers", "get_bestsellers"),
        ],
    )
    def test_vitrine_success(self, product_service, product_repo, method, repo_method):
        products = [make_product(is_featured=True)]
        getattr(product_repo, repo_method).return_value = products

        result = getattr(product_service, method)()

        assert result == products

    @pytest.mark.parametrize(
        "method,repo_method",
        [
            ("get_featured", "get_featured"),
            ("get_bestsellers", "get_bestsellers"),
        ],
    )
    def test_vitrine_empty_returns_list(self, product_service, product_repo, method, repo_method):
        """Vazio é resposta válida — não deve levantar ValueError."""
        getattr(product_repo, repo_method).return_value = []

        result = getattr(product_service, method)()

        assert result == []

    @pytest.mark.parametrize(
        "method,repo_method",
        [
            ("get_featured", "get_featured"),
            ("get_bestsellers", "get_bestsellers"),
        ],
    )
    def test_vitrine_passes_limit(self, product_service, product_repo, method, repo_method):
        getattr(product_repo, repo_method).return_value = []

        getattr(product_service, method)(3)

        getattr(product_repo, repo_method).assert_called_once_with(3)


class TestPaginacao:
    """get_paginated: envelope { data, meta } com total_pages calculado."""

    def test_paginated_meta(self, product_service, product_repo):
        product_repo.paginate.return_value = ([make_product()], 45)

        result = product_service.get_paginated(page=2, per_page=20)

        assert result["meta"] == {
            "page": 2,
            "per_page": 20,
            "total": 45,
            "total_pages": 3,
        }
        assert len(result["data"]) == 1
        product_repo.paginate.assert_called_once_with(2, 20, None)

    def test_paginated_total_pages_arredonda_para_cima(
        self, product_service, product_repo
    ):
        """41 itens com 20 por página = 3 páginas (não 2)."""
        product_repo.paginate.return_value = ([], 41)

        result = product_service.get_paginated(page=1, per_page=20)

        assert result["meta"]["total_pages"] == 3

    def test_paginated_exato_nao_cria_pagina_extra(
        self, product_service, product_repo
    ):
        """40 itens com 20 por página = exatamente 2 páginas."""
        product_repo.paginate.return_value = ([], 40)

        result = product_service.get_paginated(page=1, per_page=20)

        assert result["meta"]["total_pages"] == 2

    def test_paginated_vazio(self, product_service, product_repo):
        product_repo.paginate.return_value = ([], 0)

        result = product_service.get_paginated(page=1, per_page=20)

        assert result["data"] == []
        assert result["meta"]["total_pages"] == 0


class TestRecommendations:
    """get_recommendations: lista vazia é resposta válida."""

    def test_recommendations_success(self, product_service, product_repo):
        product_repo.get_recommendations.return_value = [make_product()]

        result = product_service.get_recommendations([1, 2], 4)

        assert len(result) == 1
        product_repo.get_recommendations.assert_called_once_with([1, 2], 4)

    def test_recommendations_empty_returns_list(
        self, product_service, product_repo
    ):
        product_repo.get_recommendations.return_value = []

        assert product_service.get_recommendations([], 4) == []


class TestPaginacaoComFiltro:
    """get_paginated com category_id: filtra no banco e valida a categoria."""

    def test_paginated_passa_category_id(
        self, product_service, product_repo, category_repo
    ):
        category_repo.get_by_id.return_value = make_category()
        product_repo.paginate.return_value = ([], 0)

        product_service.get_paginated(page=1, per_page=12, category_id=3)

        product_repo.paginate.assert_called_once_with(1, 12, 3)

    def test_paginated_total_reflete_o_filtro(
        self, product_service, product_repo, category_repo
    ):
        """`total` deve vir do filtro, senão total_pages anunciaria páginas extras."""
        category_repo.get_by_id.return_value = make_category()
        # 13 itens NA CATEGORIA, com 12 por página = 2 páginas.
        product_repo.paginate.return_value = ([make_product()], 13)

        result = product_service.get_paginated(page=1, per_page=12, category_id=3)

        assert result["meta"]["total"] == 13
        assert result["meta"]["total_pages"] == 2

    def test_paginated_categoria_inexistente_levanta(
        self, product_service, category_repo
    ):
        category_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            product_service.get_paginated(page=1, per_page=12, category_id=999)

        assert "No category found with id 999" in str(exc.value)

    def test_paginated_sem_filtro_nao_valida_categoria(
        self, product_service, product_repo, category_repo
    ):
        product_repo.paginate.return_value = ([], 0)

        product_service.get_paginated(page=1, per_page=12)

        category_repo.get_by_id.assert_not_called()


class TestDesconto:
    """get_by_discount_pct: filtro mínimo (>=) e vazio não é erro.

    Antes o service levantava ValueError quando não encontrava nada, e a rota
    devolvia 500. Como a Home chama `/products/discount/1`, o carrossel de
    promoções quebrava sempre que nenhum produto tinha desconto.
    """

    def test_desconto_vazio_retorna_lista(self, product_service, product_repo):
        product_repo.get_by_discount_pct.return_value = []

        assert product_service.get_by_discount_pct(50) == []

    def test_desconto_repassa_o_minimo(self, product_service, product_repo):
        product_repo.get_by_discount_pct.return_value = [make_product()]

        product_service.get_by_discount_pct(15)

        product_repo.get_by_discount_pct.assert_called_once_with(15)
