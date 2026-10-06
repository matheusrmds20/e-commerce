# Levantamento: Remoção dos `ValueError` dos Services

> Status: **levantamento apenas — nenhum código alterado.**
> Objetivo: integrar o tratamento de erros na camada de *service* (em vez de traduzir `ValueError` nas rotas) e identificar as exceções que ainda não existem.

---

## 1. Padrão atual (o problema)

- `app/api/exceptions.py` define uma hierarquia completa de exceções (`BookCommerceException` e subclasses com `status_code` + `code`).
- Os handlers globais já convertem essas exceções em JSON padronizado.
- **Porém**, a maioria dos services ainda lança `ValueError` genérico.
- A tradução `ValueError → HTTP` acontece **nas rotas**, em funções `_traduzir_value_error`, por *string-matching* (comparação frágil de texto).

Consequências:
- Tradução espalhada e frágil (mudou a mensagem → quebrou o código HTTP).
- Muitos `ValueError` não são traduzidos → viram **500**.
- Exceções já definidas ficam **sem uso**.
- Mensagens em inglês cru vazam para o cliente (inconsistente com o restante, que é PT-BR).

---

## 2. Exceções definidas porém **nunca usadas** (0 usos)

| Exceção | Status HTTP | Observação |
|---|---|---|
| `EmptyCartException` | 400 | Carrinho vazio no checkout — ninguém lança. |
| `InvalidStateTransitionException` | 400 | Transição inválida de status — ninguém lança. |
| `TokenExpiredException` | 401 | Sessão expirada — ninguém lança (auth usa `InvalidTokenException`). |
| `OrderNotFoundException` | 404 | Pedido não encontrado — `order_service` usa `ValueError`. |
| `AddressNotFoundException` | 404 | Endereço não encontrado — `address_service` usa `ValueError`. |
| `DuplicateReviewException` | 409 | `review_service` usa `ValueError` → traduzido para `ConflictException`. |
| `DuplicateWishlistException` | 409 | `wishlist_service` usa `ValueError` → traduzido para `ConflictException`. |

## 3. Exceções usadas **apenas na rota** (traduzidas, não lançadas no service)

Usadas em `_traduzir_value_error`, nunca `raise` no service:
- `ProductNotFoundException`
- `CategoryNotFoundException`
- `CouponNotAssignedException`
- `InsufficientStockException`
- `WishlistForbiddenException`
- `ReviewForbiddenException`

## 4. Services que **já** usam as exceções corretamente (padrão-alvo)

- `user_service.py` — usa `EmailAlreadyExistsException`, `ForbiddenException`, `InsufficientPermissionException`, `UserNotFoundException`, `BadRequestException`.
- `auth_service.py` — usa `EmailAlreadyExistsException`, `InvalidCredentialsException`, `InactiveUserException`, `InvalidTokenException`, `UserNotFoundException`.
- `address_service.delete` — usa `AddressLinkedToOrdersException`.

Estes são o modelo de referência: **o service lança a exceção e a rota não traduz nada.**

---

## 5. 🔴 BUG CRÍTICO — services cujas rotas NÃO traduzem `ValueError`

Nestes casos, `ValueError` cai no handler genérico (`generic_exception_handler`) e vira **HTTP 500**, quando deveria ser um erro do cliente (400/403/404/409).

| Service | Rota(s) afetada(s) | Consequência |
|---|---|---|
| `payment_service.py` | `payments.py` — **todas** as rotas (`create`, `get/{id}`, `order/{id}`, `checkout/{id}`, `webhook`) | "order not found", "not owned", "already exists", erros de webhook → **500** |
| `coupon_service.py` | `coupons.py` — **todas** (`create`, `update`, `delete`) | "coupon already exists", "product not found", "coupon not found" → **500** |
| `product_service.py` | `products.py` — `GET /list` (`get_all`), `GET /get/{id}` (`get_by_id`), `GET /category/{id}`, `GET /active/{is_active}` | "No product found", "No products found..." → **500** |
| `category_service.py` | `categories.py` — `GET /list` (`get_all`) | "No categories found" → **500** |

> **Nota:** as demais rotas (`orders`, `cart`, `addresses`, `reviews`, `wishlist`, `user_coupons`, `newsletter`, `products` escritas, `categories` escritas, `admin.update_order_status`) já possuem `try/except ValueError`.

---

## 6. Mapa completo: `ValueError` dos services → exceção recomendada

Legenda da coluna "Existe": ✅ = já existe e pode ser usada; 🆕 = **não existe**, precisa criar.

### `address_service.py` — rota traduz ✓
| Mensagem (`ValueError`) | Exceção recomendada | Existe |
|---|---|---|
| "No address found with id / zip_code / default" | `AddressNotFoundException` | ✅ (sem uso) |
| "Address is not owned by user" | `ForbiddenException` (ideal: novo `AddressForbiddenException`) | ✅ / 🆕 |
| "Address with zip_code ... already exists" | `ConflictException` (`ADDRESS_ALREADY_EXISTS`) | ✅ |
| "No addresses found with user_id" | `NotFoundException` — ou listagem retornar `[]` | ✅ |

### `admin_service.py` — rota traduz só `update_order_status`
| "Pedido #... não encontrado" | `OrderNotFoundException` | ✅ (sem uso) |
|---|---|---|
| "Status '...' inválido" | `InvalidStateTransitionException` | ✅ (sem uso) |

### `cart_service.py` — rota traduz ✓
| "No user found" | `UserNotFoundException` | ✅ |
|---|---|---|
| "No cart found" | `NotFoundException` (`CART_NOT_FOUND`) — ideal: novo `CartNotFoundException` | ✅ / 🆕 |
| "User ... already has a cart" | `ConflictException` — ideal: novo `CartAlreadyExistsException` | ✅ / 🆕 |
| "Cart is not owned by user" / "Cart item is not owned by user" | `ForbiddenException` | ✅ |
| "No product found" | `ProductNotFoundException` | ✅ |
| "No cart item found" | `NotFoundException` (`CART_ITEM_NOT_FOUND`) — ideal: novo `CartItemNotFoundException` | ✅ / 🆕 |
| "Insufficient stock" | `InsufficientStockException(title, available)` — hoje o cart só tem msg; exige reformulação | ✅ |

### `category_service.py` — rota traduz ✓
| "Admin permission required" | `InsufficientPermissionException` | ✅ |
|---|---|---|
| "No category found (id / name / slug)" | `CategoryNotFoundException` | ✅ |
| "No categories found" | `NotFoundException` — ou listagem retornar `[]` | ✅ |
| "Category with name/slug already exists" | `ConflictException` (`DUPLICATE_CATEGORY`) | ✅ |

### `coupon_service.py` — 🔴 rota NÃO traduz
| "No coupons found" | `NotFoundException` / novo `CouponNotFoundException` | ✅ / 🆕 |
|---|---|---|
| "Coupon with code ... already exists" | `ConflictException` / novo `DuplicateCouponException` | ✅ / 🆕 |
| "No product found" | `ProductNotFoundException` | ✅ |
| "No coupon found with id" | novo `CouponNotFoundException` | 🆕 |

### `newsletter_service.py` — rota traduz ✓
| "Email ... is already subscribed" | `ConflictException` (`NEWSLETTER_ALREADY_SUBSCRIBED`) | ✅ |
|---|---|---|
| "No subscriber found with email" | novo `NewsletterSubscriberNotFoundException` | 🆕 |
| "Admin permission required" | `ForbiddenException` | ✅ |
| "No newsletter subscribers found" | `NotFoundException` — ou listagem retornar `[]` | ✅ |

### `order_service.py` — rota traduz ✓
| "No product found" | `ProductNotFoundException` | ✅ |
|---|---|---|
| "Product '...' is not active" | novo `ProductInactiveException` (hoje vira `ProductNotFound` — semanticamente errado) | 🆕 |
| "Insufficient stock" | `InsufficientStockException(title, available)` | ✅ |
| "No coupon found with id" | novo `CouponNotFoundException` (hoje vira `InvalidCouponException` — errado) | 🆕 |
| "Coupon '...' is not assigned to user" | `CouponNotAssignedException` | ✅ |
| "not active" / "has expired" / "min purchase" / "not applicable" | `InvalidCouponException` | ✅ |
| "No user found" | `UserNotFoundException` | ✅ |
| "No address found" | `AddressNotFoundException` | ✅ (sem uso) |
| "not owned by user" | `ForbiddenException` | ✅ |
| "Order must have at least one item" | `BadRequestException` | ✅ |
| "No order found" | `OrderNotFoundException` | ✅ (sem uso) |
| "Cannot update a cancelled order" | `InvalidStateTransitionException` / `ConflictException` | ✅ (sem uso) |
| "Receipt not generated" / "is not completed" | `NotFoundException` / `BadRequestException` | ✅ |
| "No items found in order" | `NotFoundException` | ✅ |

### `payment_service.py` — 🔴 rota NÃO traduz
| "Order not found" | `OrderNotFoundException` | ✅ (sem uso) |
|---|---|---|
| "No payment found" / "No payments found" | novo `PaymentNotFoundException` | 🆕 |
| "Order ... does not belong to user" | `ForbiddenException` | ✅ |
| "Payment already exists for order" | novo `DuplicatedPaymentException` (409) | 🆕 |
| "Merchant order ... no payments" / "no external_reference" / "not payment nor merchant_order" | `BadRequestException` | ✅ |
| "Payment not found for order" | novo `PaymentNotFoundException` | 🆕 |
| "Payment ... does not match order" | `ConflictException` | ✅ |

### `product_service.py` — rota traduz parcial ✓⚠️
| "Admin permission required" | `InsufficientPermissionException` | ✅ |
|---|---|---|
| "No product found" | `ProductNotFoundException` | ✅ |
| "No products found (category / is_active / all)" | `NotFoundException` — ou listagem retornar `[]` | ✅ |
| "No category found" | `CategoryNotFoundException` | ✅ |
| "Product with title/slug already exists" | `ConflictException` (`DUPLICATE_PRODUCT`) — ideal: novo `DuplicateProductException` | ✅ / 🆕 |

### `review_service.py` — rota traduz ✓
| "Review is not owned by user" | `ReviewForbiddenException` | ✅ |
|---|---|---|
| "No user found" | `UserNotFoundException` | ✅ |
| "No product found" | `ProductNotFoundException` | ✅ |
| "User ... already reviewed product" | `DuplicateReviewException` | ✅ (sem uso) |
| "No review found" | `NotFoundException` (`REVIEW_NOT_FOUND`) | ✅ |

### `user_coupon_service.py` — rota traduz ✓
| "No user found" | `UserNotFoundException` | ✅ |
|---|---|---|
| "No coupon found" | novo `CouponNotFoundException` | 🆕 |
| "User ... already has coupon" | `ConflictException` (`USER_COUPON_DUPLICATE`) — ideal: novo `DuplicateUserCouponException` | ✅ / 🆕 |
| "User coupon is not owned by user" | `CouponNotAssignedException` | ✅ |
| "No user coupon found" | `NotFoundException` (`USER_COUPON_NOT_FOUND`) | ✅ |

### `wishlist_service.py` — rota traduz ✓
| "Wishlist item is not owned by user" | `WishlistForbiddenException` | ✅ |
|---|---|---|
| "Admin permission required" | `WishlistForbiddenException` | ✅ |
| "No user found" | `UserNotFoundException` | ✅ |
| "No product found" | `ProductNotFoundException` | ✅ |
| "User ... already has product" | `DuplicateWishlistException` | ✅ (sem uso) |
| "No wishlist item found" | `NotFoundException` (`WISHLIST_NOT_FOUND`) | ✅ |

---

## 7. Exceções que **não existem** e precisariam ser criadas 🆕

| Nova exceção | Status HTTP | Onde seria usada |
|---|---|---|
| `CouponNotFoundException` | 404 | `order_service`, `user_coupon_service`, `coupon_service` |
| `PaymentNotFoundException` | 404 | `payment_service` |
| `CartNotFoundException` | 404 | `cart_service` (opcional) |
| `CartAlreadyExistsException` | 409 | `cart_service` (opcional) |
| `CartItemNotFoundException` | 404 | `cart_service` (opcional) |
| `DuplicateCouponException` | 409 | `coupon_service` (opcional) |
| `DuplicateProductException` | 409 | `product_service` (opcional) |
| `DuplicateUserCouponException` | 409 | `user_coupon_service` (opcional) |
| `ProductInactiveException` | 400 | `order_service` |
| `NewsletterSubscriberNotFoundException` | 404 | `newsletter_service` |
| `AddressForbiddenException` | 403 | `address_service` (opcional) |

---

## 8. Defeitos de tradução atuais (mesmo onde a rota traduz)

1. **`reviews.py` fallback** — tudo que não casa nenhum padrão retorna `NotFoundException` com `code="PRODUCT_NOT_FOUND"`. *Default* enganoso.
2. **`products.py` "is not active" → `ProductNotFound`** — semanticamente incorreto: o produto existe, apenas está inativo.
3. **"No coupon found with id" vira `InvalidCouponException`** em `orders.py` — deveria ser 404, não 400.
4. **Listagens que tratam lista vazia como erro** — `cart get_by_user_id`, `order get_by_user_id`, vários `get_all` impõem 404/500 onde `[]` (HTTP 200) seria mais correto (padrão já usado corretamente em `get_featured`, `get_bestsellers`, `get_recommendations`, `get_discount_pct`).

---

## 9. Plano de ação sugerido (para implementação futura)

> ✔ **Etapa 1 concluída** — ver *seção 11. Progresso*.

Ordem de prioridade:

1. **Corrigir os endpoints sem tradução** (geram 500 hoje):
   - `payments.py`, `coupons.py`, e os `GET` públicos de `products.py`/`categories.py`.
2. **Trocar `ValueError →` exceção específica no service**, começando pelas classes já existentes sem uso:
   - `OrderNotFound`, `AddressNotFound`, `DuplicateReview`, `DuplicateWishlist`, `InvalidStateTransition`, `EmptyCart`.
3. **Adicionar as classes novas** da seção 7.
4. **Consolidar**: refatorar `InsufficientStockException(title, available)` para receber `(product_title, available)` onde hoje só há mensagem (cart).
5. **Remover `_traduzir_value_error` e os `try/except ValueError` das rotas**, deixando os handlers globais tratarem tudo. Resultado: código mais simples, à prova de mudança de texto.
6. **Ajustar endpoints de listagem** para retornar `[]` (200) em vez de erro quando apropriado.

---

## 10. Observações finais para a implementação

- **Padrão-alvo** (copiar de `user_service` / `auth_service`): `raise <ExceçãoEspecífica>()` no service, sem `try/except` na rota.
- **Mensagens em PT-BR**: as exceções novas/padrão devem trazer mensagem em português (o atual vazamento de inglês cru é inconsistente com o resto).
- **Mercado Pago / webhook**: erros do `payment_service.process_webhook` são tratados internamente na própria rota (return `{"status": "error"}`), mas os `ValueError` em `create`/`checkout`/`get_*` precisam virar exceções.

---

## 11. Progresso — Etapa 1 (concluída)

> ✔ **Etapas 2 e 5 também concluídas** — ver seção 12.

Objetivo: eliminar os endpoints que retornavam **500** por `ValueError` não traduzido.

### Descobertas durante a implementação
- `category_service.get_all` **não** gerava 500 na prática: o `BaseRepository.get_all` retorna `[]` (nunca `None`), então o `if categories is None` jamais dispara. Nenhuma alteração foi necessária em categorias.
- Nos métodos públicos GET de `products` (`get_by_category_id`, `get_by_is_active`, `get_all`) e em `coupon_service.get_all`, **lista vazia agora retorna `[]` (HTTP 200)** em vez de erro — padrão consistente com `get_featured`/`get_bestsellers`/`get_recommendations` do mesmo arquivo.
- `product_service.get_by_id` passou a levantar `ProductNotFoundException` (404) em vez de `ValueError`.

### Mudanças feitas
| Arquivo | Mudança |
|---|---|
| `app/api/exceptions.py` | Adicionadas `CouponNotFoundException` (404) e `PaymentNotFoundException` (404). |
| `app/services/payment_service.py` | Todos os `ValueError` → `OrderNotFoundException` / `PaymentNotFoundException` / `ForbiddenException` / `ConflictException` / `BadRequestException`. |
| `app/services/coupon_service.py` | `ValueError` → `CouponNotFoundException` / `ConflictException`/`ProductNotFoundException`; `get_all` retorna `[]`. |
| `app/services/product_service.py` | `get_by_id` → `ProductNotFoundException`; `get_by_category_id`/`get_by_is_active`/`get_all` retornam `[]`. |
| `tests/service_tests/test_payment_service.py` | Assertions atualizados para as novas exceções. |
| `tests/service_tests/test_coupon_service.py` | Assertions atualizados para as novas exceções + `get_all` vazio retorna `[]`. |
| `tests/service_tests/test_product_service.py` | `get_by_id` → `ProductNotFoundException`; listas vazias retornam `[]`. |

> **Nota:** as rotas `payments.py` / `coupons.py` continuam **sem** `try/except` (como antes), mas agora isso é correto: os services lançam `BookCommerceException` e os handlers globais as convertem em JSON padronizado. Os `ValueError` que ainda restam em `product_service` (create/update/delete) seguem sendo traduzidos pelas rotas — a ser migrado nas etapas 2–5.

---

## 12. Progresso — Etapa 2 + Etapa 5 (concluídas)

> ✔ **Etapa 6 (listagens `[]`) também concluída** — ver seção 13.

Migração completa: **nenhum service de domínio lança mais `ValueError`**. As rotas não possuem mais `_traduzir_value_error` nem `try/except ValueError` — os services lançam `BookCommerceException` diretamente e os handlers globais geram o JSON padronizado.

### Services migrados (ValueError → exceção de domínio)
| Service | Exceções usadas |
|---|---|
| `address_service` | `AddressNotFoundException`, `AddressForbiddenException`, `ConflictException`, `AddressLinkedToOrdersException` |
| `admin_service` | `OrderNotFoundException`, `InvalidStateTransitionException` |
| `cart_service` | `UserNotFoundException`, `CartNotFoundException`, `CartAlreadyExistsException`, `CartItemNotFoundException`, `ForbiddenException`, `ProductNotFoundException`, `InsufficientStockException` |
| `category_service` | `CategoryNotFoundException`, `ConflictException`, `InsufficientPermissionException` |
| `coupon_service` | `CouponNotFoundException`, `ConflictException`, `ProductNotFoundException` |
| `newsletter_service` | `ConflictException`, `ForbiddenException`, `NewsletterSubscriberNotFoundException` |
| `order_service` | `AddressNotFoundException`, `AddressForbiddenException`, `BadRequestException`, `CouponNotFoundException`, `CouponNotAssignedException`, `ForbiddenException`, `InsufficientStockException`, `InvalidCouponException`, `NotFoundException`, `OrderNotFoundException`, `ProductNotFoundException`, `UserNotFoundException` |
| `payment_service` | `OrderNotFoundException`, `PaymentNotFoundException`, `ForbiddenException`, `ConflictException`, `BadRequestException` |
| `product_service` | `CategoryNotFoundException`, `DuplicateProductException`, `InsufficientPermissionException`, `ProductNotFoundException` |
| `review_service` | `DuplicateReviewException`, `NotFoundException`, `ProductNotFoundException`, `ReviewForbiddenException`, `UserNotFoundException` |
| `user_coupon_service` | `CouponNotFoundException`, `CouponNotAssignedException`, `NotFoundException`, `ConflictException`, `UserNotFoundException` |
| `wishlist_service` | `DuplicateWishlistException`, `NotFoundException`, `ProductNotFoundException`, `UserNotFoundException`, `WishlistForbiddenException` |

### Exceções novas adicionadas a `app/api/exceptions.py`
- `CartNotFoundException` (404), `CartItemNotFoundException` (404), `CartAlreadyExistsException` (409)
- `CouponNotFoundException`, `PaymentNotFoundException`, `NewsletterSubscriberNotFoundException` (404)
- `ProductInactiveException` (400), `DuplicateProductException` (409)
- `AddressForbiddenException` (403)
- Também aproveitadas as que estavam sem uso: `OrderNotFoundException`, `AddressNotFoundException`, `DuplicateReviewException`, `DuplicateWishlistException`, `InvalidStateTransitionException`.

### Rotas simplificadas (removido `_traduzir_value_error` / `try/except ValueError`)
`addresses.py`, `categories.py`, `newsletter.py`, `reviews.py`, `wishlist.py`, `user_coupons.py`, `orders.py`, `cart.py`, `products.py`, `admin.py`.

> `payments.py` e `coupons.py` nunca tiveram try/except — agora corretamente desnecessário.

### Listagens que passaram a retornar `[]` (200) em vez de erro
- `product_service.get_all` / `get_by_category_id` / `get_by_is_active`
- `coupon_service.get_all`
- `newsletter_service.list_all`
- `wishlist_service.get_all`

### Testes atualizados
- `tests/service_tests/`: `test_address`, `test_cart`, `test_category`, `test_newsletter`, `test_order`, `test_order_email`, `test_product`, `test_review`, `test_user_coupon`, `test_wishlist` — asserts de `ValueError` → exceções de domínio.
- `tests/http_tests/`: `test_http_products`, `test_http_categories`, `test_http_newsletter`, `test_http_order_receipt`, `test_http_orders`, `test_http_reviews`, `test_http_wishlist`, `test_http_cart` — mocks agora simulam exceções de domínio em vez de `ValueError`.

### Resultados validados (execução final estável)
- Suíte completa `tests/`: **639 passed, 1 skipped**
  - `tests/service_tests` + `tests/schemas_tests`: 337
  - `tests/http_tests`: 302
- Ruff em `app/` e testes: **All checks passed**

### ValueErrors restantes
Nenhum `raise ValueError` nos services de domínio. Só os `except ValueError` legítimos em `admin_service` (que capturam `OrderStatus(...)` inválido para lançar `InvalidStateTransitionException`).

---

## 13. Progresso — Etapa 6 (listagens `[]` — concluída)

Padronização completa: **toda listagem retorna `[]` (HTTP 200) quando vazia**, em vez de 404. A ausência de itens não é erro de API REST.

### Listagens que passaram a devolver `[]` (200)
| Método | Antes | Agora |
|---|---|---|
| `product_service.get_all` / `get_by_category_id` / `get_by_is_active` | 404/500 | `[]` (200) |
| `coupon_service.get_all` | 400 | `[]` (200) |
| `category_service.get_all` | — | `[]` (200) |
| `newsletter_service.list_all` | 404 | `[]` (200) |
| `wishlist_service.get_all` | 404 | `[]` (200) |
| `address_service.get_by_user_id` | 404 | `[]` (200) |
| `order_service.get_by_user_id` | 404 | `[]` (200) |
| `review_service.get_by_user_id` | 404 | `[]` (200) |
| `wishlist_service.get_by_user_id` | 404 | `[]` (200) |
| `payment_service.get_by_order_id` | 404 | `[]` (200) |

### Mantidos como 404 (consulta de entidade individual — correto)
- `cart_service.get_by_user_id` (`/cart/me`): 404 quando o usuário ainda não tem carrinho — **comportamento intencional** (handshake do front, documentado).
- `address_service` `get_by_id` / `get_by_zip_code` / `get_actual_address_default` / `set_default`: entidade única inexistente → 404.
- `review_service`/`cart`/`product`/`coupon`/`payment` `get_by_*` de entidade única → 404.

### Testes atualizados
- `tests/service_tests/test_payment_service.py::test_get_by_order_id_empty` — agora espera `[]`.
- `tests/service_tests/test_review_service.py::test_no_reviews` — agora espera `[]`.

### Resultados validados
- Suíte completa `tests/`: **639 passed, 1 skipped**
- Ruff em `app/` e testes: **All checks passed**

---

## 14. Progresso — Polimento final (concluído)

### Consolidação de exceções redundantes
- **`ProductInactiveException`** agora é lançada de fato em `order_service` (antes se usava `BadRequestException` genérico com `code="PRODUCT_INACTIVE"`).
- **`TokenExpiredException`** passou a ser lançada em `auth_service.refresh` quando o JWT está expirado (`jose.ExpiredSignatureError`) — antes tudo era tratado como `InvalidTokenException`. Isso dá ao frontend o código `TOKEN_EXPIRED` (mensagem "Sessão expirada") de forma distinta de um token malformado. Novo teste de cobertura adicionado.
- **`EmptyCartException`** foi **removida**: o `order_service.create` recebe os itens no payload (`data.items`) e não constrói o pedido a partir de um carrinho lido, então a classe não correspondia a nenhum fluxo real. O checkout esvazia a sacola apenas *depois*, e a ausência de carrinho já é tratada como não-erro em `_limpar_carrinho`.

### Resultado: nenhuma exceção sem uso
Todas as 35 classes de `app/api/exceptions.py` são referenciadas no código (sem classe morta).

### Validação final
- Suíte completa `tests/`: **640 passed, 1 skipped**
- Ruff em `app/` e testes: **All checks passed**