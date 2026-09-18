"""Helpers dos testes HTTP: payloads de resposta e assertions.

Módulo regular (não conftest) para ser importado diretamente pelos testes.
As exceções de domínio devem ser importadas de ``app.api.exceptions`` e
``UserRole`` de ``app.models.user``.
"""

CREATED_AT = "2024-01-01T12:00:00"
UPDATED_AT = "2024-01-02T12:00:00"


# ---------------------------------------------------------------------------
# Payloads de resposta (shape dos response_models)
# ---------------------------------------------------------------------------


def product_payload(**overrides):
    """Payload compatível com ProductResponse."""
    payload = {
        "id": 1,
        "category_id": 1,
        "title": "Clean Code",
        "slug": "clean-code",
        "description": "Principios e praticas do codigo limpo",
        "price": 59.9,
        "image_url": None,
        "is_active": True,
        "is_featured": False,
        "is_bestseller": False,
        "author": "Robert C. Martin",
        "isbn": "9780132350884",
        "publisher": "Prentice Hall",
        "publication_year": 2008,
        "pages": 464,
        "language": "en",
        "synopsis": "Um classico da engenharia de software.",
        "discount_pct": 10,
        "stock_qty": 25,
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }
    payload.update(overrides)
    return payload


def user_payload(**overrides):
    """Payload compatível com UserResponse."""
    payload = {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "role": "customer",
        "is_active": True,
        "email_verified": False,
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }
    payload.update(overrides)
    return payload


def auth_user_payload(**overrides):
    """Payload compatível com AuthResponse (sem email_verified/updated_at)."""
    payload = {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "role": "customer",
        "is_active": True,
        "created_at": CREATED_AT,
    }
    payload.update(overrides)
    return payload


def category_payload(**overrides):
    payload = {
        "id": 1,
        "name": "Tecnologia",
        "slug": "tecnologia",
        "description": "Livros de tecnologia",
        "image_url": None,
        "is_active": True,
        "parent_id": None,
    }
    payload.update(overrides)
    return payload


def coupon_payload(**overrides):
    payload = {
        "id": 1,
        "code": "PROMO10",
        "product_id": None,
        "discount_type": "percentage",
        "discount_value": 10.0,
        "min_purchase": None,
        "max_discount": None,
        "valid_until": "2025-12-31T23:59:59",
        "max_uses": 100,
        "is_active": True,
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }
    payload.update(overrides)
    return payload


def cart_item_payload(**overrides):
    payload = {
        "id": 1,
        "cart_id": 1,
        "product_id": 1,
        "quantity": 2,
        "product": product_payload(),
    }
    payload.update(overrides)
    return payload


def cart_payload(**overrides):
    payload = {
        "id": 1,
        "user_id": 1,
        "items": [cart_item_payload()],
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }
    payload.update(overrides)
    return payload


def address_payload(**overrides):
    payload = {
        "id": 1,
        "user_id": 1,
        "street": "Rua das Flores",
        "number": "100",
        "complement": None,
        "neighborhood": "Centro",
        "city": "Sao Paulo",
        "state": "SP",
        "zip_code": "01001000",
        "is_default": False,
        "updated_at": UPDATED_AT,
    }
    payload.update(overrides)
    return payload


def order_item_payload(**overrides):
    payload = {
        "id": 1,
        "order_id": 1,
        "product_id": 1,
        "quantity": 2,
        "price": 59.9,
    }
    payload.update(overrides)
    return payload


def order_payload(**overrides):
    payload = {
        "id": 1,
        "user_id": 1,
        "address_id": 1,
        "coupon_id": None,
        "notes": None,
        "status": "pending",
        "subtotal": 119.8,
        "discount_amount": 0.0,
        "shipping_cost": 0.0,
        "total": 119.8,
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
        "order_items": [order_item_payload()],
    }
    payload.update(overrides)
    return payload


def wishlist_payload(**overrides):
    payload = {
        "id": 1,
        "user_id": 1,
        "product_id": 1,
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }
    payload.update(overrides)
    return payload


def review_payload(**overrides):
    payload = {
        "id": 1,
        "user_id": 1,
        "product_id": 1,
        "rating": 5,
        "comment": "Excelente livro",
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Assertions auxiliares
# ---------------------------------------------------------------------------


def assert_error(response, status_code: int, code: str | None = None):
    """Valida o corpo padronizado de erro: {"error": {"code", "message"}}."""
    assert response.status_code == status_code, (
        f"status esperado {status_code}, obtido {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "error" in body, f"resposta sem o envelope 'error': {response.text}"
    if code is not None:
        assert body["error"]["code"] == code


def assert_validation_error(response):
    """Valida erro de validação 422 com o formato padronizado."""
    assert response.status_code == 422, (
        f"status esperado 422, obtido {response.status_code}: {response.text}"
    )
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in body["error"]
