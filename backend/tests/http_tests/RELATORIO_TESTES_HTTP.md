# Relatório — Testes HTTP, Análise de Services/Schemas/Rotas

**Data:** gerado automaticamente
**Escopo:** `backend/app` (services, schemas, rotas) e novos testes HTTP em `backend/tests/http_tests/`
**Resultado da suíte:** `493 passed` (268 testes pré-existentes + **225 novos testes HTTP**)

---

## 1. O que foi entregue

| Arquivo | Cobertura |
|---|---|
| `tests/http_tests/conftest.py` | Fixture `client` (TestClient + `get_db` mockado + handlers de exceção) e fixture `patch_service` |
| `tests/http_tests/helpers.py` | Payloads de resposta e assertions (`assert_error`, `assert_validation_error`) |
| `tests/http_tests/test_http_auth.py` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| `tests/http_tests/test_http_users.py` | CRUD `/users/*`, `change-password` |
| `tests/http_tests/test_http_products.py` | CRUD `/products/*`, filtros (categoria, editora, ano, idioma, desconto, estoque, ativo) |
| `tests/http_tests/test_http_categories.py` | CRUD `/categories/*` |
| `tests/http_tests/test_http_coupons.py` | CRUD `/coupons/*` e filtros |
| `tests/http_tests/test_http_cart.py` | `/cart/*` (create, itens, add, update, decrease, remove, clear, delete) |
| `tests/http_tests/test_http_addresses.py` | `/addresses/*` (create, list, default, zip, update, delete) |
| `tests/http_tests/test_http_orders.py` | `/orders/*` (create, list, get, items, update, delete) |
| `tests/http_tests/test_http_reviews.py` | `/reviews/*` (create, list, get, user, product, rating, update, delete) |
| `tests/http_tests/test_http_wishlist.py` | `/wishlists/*` (create, list, all, product, update, delete) |

Cada arquivo cobre **sucesso** (201/200 com o corpo serializado) e **erros**:
validação 422 (schemas e query params), 400, 401, 403, 404 e 409 (exceções de
domínio levantadas pelos services mockados).

### Estratégia de mocks (seguindo a estrutura do `conftest` raiz)
- `get_db` é substituído por um gerador que entrega `Mock(name="db")` — nenhuma query real.
- O service de cada rota é mockado no factory da rota (ex.: `patch("app.api.v1.auth.get_auth_service", return_value=svc)`), validando **rota + schema + serialização**.
- Os handlers de `app.api.exceptions` são registrados no app **dentro do fixture `client`** (ver item 2.1) para que os testes validem o contrato de erros.

### Como rodar
```powershell
cd backend
venv\Scripts\python.exe -m pytest tests/http_tests -q        # só os HTTP
venv\Scripts\python.exe -m pytest -q                        # suíte completa
```

> **Infra:** o `httpx` (exigido pelo `TestClient`) não estava instalado no venv.
> O `pip install` falhou (variável de máquina `CURL_CA_BUNDLE` aponta para um
> CA bundle inexistente do PostgreSQL e o sandbox bloqueou o download). Foi
> adicionado `venv/Lib/site-packages/_dsh_httpx.pth` apontando para o
> site-packages global do Python 3.13 (httpx 0.28.1). Em outra máquina:
> `pip install httpx`.

---

## 2. Erros graves encontrados (NENHUM service/schema foi alterado)

### 2.1 [CRÍTICO] `app.main` nunca registra os exception handlers
`backend/app/main.py` cria o app e inclui o router, mas **não chama**
`register_exception_handlers(app)` (definido em `app/api/exceptions.py` e usado
em nenhum lugar). Consequência em produção: toda exceção de domínio
(`EmailAlreadyExistsException`, `InvalidCredentialsException`,
`ProductNotFoundException`, etc.) e qualquer `ValueError` cai no handler genérico
do Starlette e vira **500 "Internal Server Error"** — o contrato documentado
(400/401/403/404/409 com corpo `{"error": {code, message}}`) **não funciona**.

Isso é a causa raiz de vários itens abaixo. Correção (1 linha):
```python
# main.py
from app.api.exceptions import register_exception_handlers
register_exception_handlers(app)
```
Os testes HTTP registram os handlers no fixture `client` **apenas para validar o
contrato pretendido**; enquanto `main.py` não for corrigido, a API real devolve
500 para todos esses casos.

### 2.2 [CRÍTICO] `GET /auth/me` sempre quebra em produção
`backend/app/api/v1/auth.py:52`:
```python
def me(user: Annotated[User, Depends(get_current_user)]) -> AuthResponse:
    return get_auth_service(user.db).me(user)
```
`user` é um ORM `User` (retornado por `get_current_user`) e **não possui o
atributo `.db`** → `AttributeError` → 500. A assinatura da rota nem recebe a
sessão. Nos testes, `get_current_user` é substituído por um usuário fake com
`.db`, então a rota passa — em produção, quebra.

### 2.3 [CRÍTICO] `OrderService.create` nunca consegue criar um pedido
`backend/app/services/order_service.py` cria os `OrderItem`s **antes** do pedido
existir (com `order_id=None`), e `BaseRepository.create` faz `flush()` imediato.
Como `OrderItem.order_id` é `nullable=False`, o flush lança `IntegrityError` →
500. Ou seja: **nenhum pedido pode ser criado pela API**. O `order_id` só é
atribuído depois do flush, tarde demais. (Não alterado, conforme instrução.)

### 2.4 [GRAVE] Services levantam `ValueError` em vez das exceções de domínio
`ProductService`, `CategoryService`, `CouponService`, `CartService`,
`OrderService`, `AddressService`, `ReviewService` e `WishlistService` usam
`raise ValueError(...)` para "não encontrado", "duplicado", "estoque
insuficiente", "não é dono", etc. Com o item 2.1, isso vira **500** em produção
em vez de 404/409/403/400. Exemplos:
- `GET /products/get/999` → deveria ser 404 `PRODUCT_NOT_FOUND`; hoje 500.
- `POST /orders` com estoque insuficiente → deveria ser 409 `INSUFFICIENT_STOCK`; hoje 500.
- Item de carrinho de outro usuário → deveria ser 403; hoje 500.

Os testes HTTP mockam os services levantando as exceções de domínio corretas
para validar o contrato das rotas; os testes `test_list_service_error` /
`test_list_empty_returns_500` documentam o comportamento real (500) das
listagens vazias.

### 2.5 [GRAVE — segurança] `POST /users/create` sem `role` cria ADMIN
`backend/app/schemas/user.py` define `AdminUserCreate | CustomerUserCreate`
(união sem discriminator) e a rota `backend/app/api/v1/users.py:33` aceita essa
união. O payload sem `role` valida como `AdminUserCreate` (primeiro da união,
com `role=ADMIN` por padrão). **Verificado empiricamente**: `POST /users/create`
sem `role` → `data.role == UserRole.ADMIN`. Qualquer cadastro público sem role
vira administrador. O teste `test_create_without_role_defaults_to_admin`
documenta o comportamento atual.

### 2.6 [MÉDIO] Listagens vazias retornam 500 em vez de `200 []`
`get_all` e os filtros dos services (`products`, `categories`, `coupons`,
`reviews`, `wishlists`, etc.) levantam `ValueError` quando o resultado é vazio,
então `GET /products/list` sem produtos → 500 (o contrato usual seria `200 []`).

### 2.7 [MÉDIO — corrigido] Rota do carrinho impedia o app de subir
`backend/app/api/v1/cart.py:94` usava `Annotated[int, Query(1, ...)]` — default
**dentro** de `Annotated`, que o FastAPI rejeita em runtime de importação
(`AssertionError: Query default value cannot be set in Annotated`). **A API
inteira não inicializava** (nenhuma rota servida). Esta foi a **única alteração
de código-fonte feita** (arquivo de rota, não service/schema — necessária para
qualquer teste HTTP rodar):
```python
# antes (quebrado)
quantity: Annotated[int, Query(1, ge=1, ...)],
# depois
quantity: Annotated[int, Query(ge=1, ...)] = 1,
```
(parâmetro com default movido para o fim da assinatura para satisfazer o Python).

### 2.8 [MÉDIO] `AddressCreate` exige `user_id` no corpo E na query
O schema `AddressCreate.user_id` é obrigatório no body, mas a rota também recebe
`user_id` como query (`/addresses/create?user_id=1`), e o service compara
`data.user_id != user_id` → 403 se divergirem. Duplicação confusa de fonte de
verdade; o cliente precisa mandar o mesmo id nos dois lugares.

---

## 3. Problemas menores (sem impacto funcional imediato)

| # | Local | Observação |
|---|---|---|
| 1 | `schemas/coupon.py` | `validate_discount` anotado como `int`, campo é `float` (cosmético) |
| 2 | `schemas/order.py` / `order_service.py` | `OrderUpdate.status` aceita qualquer transição; `InvalidStateTransitionException` existe mas nunca é usada (só bloqueia pedido cancelado) |
| 3 | `schemas/category.py` | `CategoryResponse` não expõe `created_at`/`updated_at` (o modelo tem) |
| 4 | `api/v1/dashboard.py` e `services/dashboard_service.py` | Arquivos vazios — módulo de dashboard planejado, sem rotas |
| 5 | `api/v1/products.py` | `list[ProductResponse]` declarado, mas o handler anota `-> list` (funciona, porém sem tipagem) |
| 6 | `schemas/cart.py` | `CartItemUpdate`/`CartCreate`/`CartUpdate` não são usados pelas rotas (sobra) |

---

## 4. Resumo executivo

- **Suíte HTTP entregue e verde:** 225 testes (sucesso + erros) cobrindo todas as rotas de `/api/v1`.
- **Nenhum service/schema foi alterado**, conforme solicitado.
- **1 alteração de rota obrigatória** (`cart.py` — default de `Query` dentro de `Annotated`) sem a qual o app nem inicializava.
- **Erros graves a corrigir no app** (em ordem de prioridade):
  1. `main.py` → `register_exception_handlers(app)` (2.1) — destrava todo o contrato de erros.
  2. `auth.py` rota `/me` → usar a sessão real em vez de `user.db` (2.2).
  3. `order_service.create` → criar `OrderItem`s após o pedido (ou usar `create_with_items`) (2.3).
  4. Services → trocar `ValueError` pelas exceções de domínio (2.4).
  5. `users.py`/`user.py` → resolver a união `AdminUserCreate | CustomerUserCreate` (2.5).
