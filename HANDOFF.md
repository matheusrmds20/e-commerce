# Handoff — Análise Frontend/Backend e Feature de Cupons por Usuário

> Documento de contexto para iniciar um **novo chat**. Resume o que foi analisado,
> o que o frontend consome, endpoints não usados, o que foi implementado na feature
> de cupons (vínculo usuário↔cupom) e o estado atual do repositório.
>
> Última atualização: após implementação de "Cupons por usuário (ownership)".

---

## 1. Visão geral do projeto

- **Raiz:** `C:/Users/mathe/OneDrive/Desktop/E-commerce v1`
- **Backend:** FastAPI + SQLAlchemy + Alembic + PostgreSQL. Raiz em `backend/`, app em `backend/app/`.
- **Frontend:** React 19 + Vite + Tailwind v4. Raiz em `frontend/Papiro/`, código em `frontend/Papiro/src/`.
- **Alembic:** fica na **raiz do repo** (`alembic/`), não em `backend/`. O `env.py` importa cada model explicitamente.
- **Backend foi construído primeiro** → muitos endpoints ficaram sem uso no frontend.

### Como rodar / validar

```bash
# Backend — testes (a venv está em ./venv)
cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1/backend"
source ../venv/Scripts/activate
python -m pytest tests/ -q          # atualmente: 591 passed
python -m ruff check app/           # há erros PRÉ-EXISTENTES de whitespace

# Migrations (da raiz do repo)
cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1"
alembic current                     # head atual: 8cf455aabd0d
alembic heads

# Frontend — lint e build
cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1/frontend/Papiro"
npx eslint src/
npm run build
```

- **Banco:** PostgreSQL em `localhost:5433/bookcommerce-db` (ver `backend/.env`).
- **API base:** `VITE_API_URL` (default `http://localhost:8000/api/v1`).
- **Token:** JWT em `localStorage`, chave `papiro.token`. Interceptor do axios anexa `Bearer`.
- **Erros normalizados:** envelope `{ error: { code, message, details? } }` → `ApiError` em `src/api/client.js`.

> ⚠️ **Regra de trabalho do usuário:** implementar **parte por parte**, sempre
> apresentando o levantamento e um plano **antes** de tocar em código.

---

## 2. Mapa do frontend (`frontend/Papiro/src/`)

### Camada de API (`src/api/`)

| Arquivo | Service | Observação |
|---|---|---|
| `client.js` | — | Instância axios, `ApiError`, `toApiError`, token |
| `adapters.js` | — | Conversões snake_case↔view PT-BR, `calcularTotais`, `formatarPreco` |
| `auth.js` | `authService` | login usa **form-urlencoded** (`username`=email) |
| `products.js` | `productService` | catálogo, paginado, recomendações, CRUD |
| `categories.js` | `categoryService` | listagem |
| `cart.js` | `cartService` | carrinho |
| `addresses.js` | `addressService` | endereços |
| `orders.js` | `orderService` | pedidos |
| `reviews.js` | `reviewService` | avaliações |
| `wishlist.js` | `wishlistService` | lista de desejos |
| `coupons.js` | `couponService` | **cupons + vínculos (novo)** |
| `admin.js` | `adminService` | dashboard, pedidos, usuários |
| `cards.js` | `cardService` | **cartões são 100% localStorage** (não há endpoint) |
| `newsletter.js` | `newsletterService` | **endpoint não existe no backend** |
| `home.js` | — | composição da Home a partir de vários endpoints |

### Páginas (`src/pages/`)
`Home`, `Acervo`, `DetalheLivro`, `Carrinho`, `Checkout`, `Login`, `Registro`, `MinhaConta`, `Admin`.

### Contextos (`src/context/`)
`AuthContext`, `CartContext`.

---

## 3. O que o frontend USA (por service)

✅ = usado | ❌ = **nunca chamado** (código morto no front)

| Service | Métodos usados | Métodos NÃO usados |
|---|---|---|
| `authService` | `login`, `register`, `me`, `logout` | — |
| `addressService` | `criar`, `listar`, `definirPadrao`, `atualizar`, `excluir` | ❌ `padrao` (`GET /addresses/default`) |
| `productService` | `listar`, `obter`, `listarPorDesconto`, `listarPorAtivo`, `listarDestaques`, `listarMaisVendidos`, `listarPaginado`, `recomendacoes`, `criar`, `excluir` | ❌ `listarPorCategoria`, ❌ `atualizar` |
| `categoryService` | `listar` | — |
| `cartService` | `criar`, `obter`, `adicionarItem`, `atualizarQuantidade`, `removerItem`, `limpar` | — |
| `orderService` | `criar`, `listar` | ❌ `obter`, ❌ `itens`, ❌ `atualizar`, ❌ `excluir` |
| `reviewService` | `listarPorProduto`, `criar`, `excluir` | ❌ `atualizar` |
| `wishlistService` | `adicionar`, `listar`, `excluir` | — |
| `couponService` | `listar`, `criar`, `atualizar`, `excluir`, `meusCupons`, `vinculosDoCupom`, `atribuir`, `removerVinculo` | — |
| `adminService` | `obterEstatisticas`, `listarPedidos`, `atualizarStatusPedido`, `listarUsuarios` | — |
| `cardService` | `listar`, `criar`, `atualizar`, `excluir`, `definirPadrao` | — (localStorage; `salvarTodos` é interno) |
| `newsletterService` | `inscrever` | — (endpoint inexistente no backend) |

> Membros de service **órfãos** (métodos definidos e nunca chamados):
> `addressService.padrao`, `productService.listarPorCategoria`, `productService.atualizar`,
> `orderService.obter/itens/atualizar/excluir`, `reviewService.atualizar`.
> Utilitário exportado e nunca usado: `mascararCartao` (em `cards.js`).

---

## 4. Endpoints do backend NÃO consumidos pelo frontend

O backend expõe **muito mais** do que o front consome. Agrupado por área:

### Products (`/products`) — não usados
`GET /title/{title}`, `GET /slug/{slug}`, `GET /isbn/{isbn}`, `GET /publisher/{publisher}`,
`GET /year/{year}`, `GET /language/{language}`, `GET /stock/{qty}`.
(Usados: `list`, `paginated`, `recommendations`, `featured`, `bestsellers`, `get/{id}`, `category/{id}`, `discount/{pct}`, `active/{bool}`, `create`, `delete`. **`update` existe no service mas nunca é chamado.**)

### Categories (`/categories`) — não usados
`POST /create`, `GET /get/{id}`, `GET /name/{name}`, `GET /slug/{slug}`, `PATCH /update/{id}`, `DELETE /delete/{id}`.
(Usado apenas: `GET /list`.)

### Coupons (`/coupons`) — parcialmente usados
Usados no Admin: `create`, `list`, `update/{id}`, `delete/{id}`.
**Não usados:** `GET /get/{id}`, `GET /code/{code}`, `GET /product/{id}`, `GET /valid-until/{d}`,
`GET /max-uses/{n}`, `GET /discount-type/{t}`, `GET /discount-value/{v}`, `GET /min-purchase/{v}`, `GET /max-discount/{v}`.

### Cart (`/cart`) — não usados
`GET /get/{cart_id}`, `GET /items/{cart_id}`, `PATCH /{cart_id}/items/decrease/{item_id}`, `DELETE /delete/{cart_id}`.

### Orders (`/orders`) — não usados pelo front
`GET /get/{id}`, `GET /items/{id}`, `PATCH /update/{id}`, `DELETE /delete/{id}` — existem no service, mas nenhuma tela chama.

### Users (`/users`) — sem service no front
`POST /create`, `GET /user_id/{id}`, `GET /email/{email}`, `PATCH /update/{id}`,
`POST /change_password/{id}/change-password`, `DELETE /delete/{id}`.

### Wishlist (`/wishlists`) — não usados
`GET /get/{id}`, `GET /all`, `GET /product/{product_id}`, `PATCH /update/{id}`.

### Reviews (`/reviews`) — não usados
`GET /list`, `GET /get/{id}`, `GET /user/{user_id}`, `GET /rating/{rating}`, `PATCH /update/{id}`.

### Addresses (`/addresses`) — não usados
`GET /get/{address_id}`, `GET /zip/{zip_code}`.

### Auth / Admin / User-coupons
100% cobertos (todos usados). **Novo:** `/user-coupons` (ver seção 5).

> **Inexistente no backend mas chamado pelo front:** `POST /newsletter/subscribe`
> (`src/api/newsletter.js`) — o próprio arquivo documenta que retorna 404 e a UI
> trata como indisponível.

---

## 5. Feature implementada: Cupons por usuário (ownership N:N)

### 5.1. Conceito
Cupom deixou de ser "global" e passou a ter **dono**: um cupom N:N com usuários.
Só aparece/usável no checkout para quem foi **atribuído**. Um cupom pode pertencer
a vários usuários; um usuário acumula vários cupons.

### 5.2. Backend — arquivos (novos e alterados)

**Novos:**
- `backend/app/models/user_coupon.py` — tabela `user_coupons` (FK `user_id`, `coupon_id`, unique composta `uq_user_coupon`).
- `backend/app/repositories/user_coupon_repo.py` — `get_by_user_id`, `get_by_coupon_id`, `get_by_user_and_coupon`.
- `backend/app/schemas/user_coupon.py` — `UserCouponCreate` (`user_id`, `coupon_id`), `UserCouponResponse`.
- `backend/app/services/user_coupon_service.py` — regras de criação/remoção/ownership (cobertura 100%).
- `backend/app/api/v1/user_coupons.py` — router `/user-coupons`.
- `alembic/versions/8cf455aabd0d_user_coupons.py` — **migration aplicada** (tabela já existe no banco).
- `backend/tests/service_tests/test_user_coupon_service.py`.

**Alterados:**
- `backend/app/models/user.py` — relação `User.coupons`.
- `backend/app/models/coupon.py` — relação `Coupon.users`.
- `alembic/env.py` — import do model para o autogenerate.
- `backend/app/api/router.py` — registra `user_coupon_router` com prefixo `/user-coupons`.
- `backend/app/services/order_service.py` — `_validate_coupon(coupon_id, items, user_id)` agora **exige posse** do cupom.
- `backend/app/api/v1/orders.py` — traduz erro de posse para **403 `COUPON_NOT_ASSIGNED`**.
- `backend/app/api/v1/user_coupons.py` — "not owned by user" → `COUPON_NOT_ASSIGNED`.
- `backend/app/api/exceptions.py` — nova exceção `CouponNotAssignedException(ForbiddenException, code="COUPON_NOT_ASSIGNED", 403)`.
- `backend/tests/conftest.py` — fixtures `user_coupon_repo`, `user_coupon_service`.
- `backend/tests/service_tests/test_order_service.py` — `_grant_coupon_ownership` + casos.
- `backend/tests/http_tests/test_http_orders.py` — `test_create_coupon_not_assigned`.

### 5.3. Endpoints de `/user-coupons`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/user-coupons/my` | **Cupons atribuídos ao usuário autenticado** (usado no checkout). Retorna `CouponResponse[]`. |
| POST | `/user-coupons/create` | Atribui/resgata um cupom a um usuário. Body: `{ user_id, coupon_id }`. 201. |
| GET | `/user-coupons/list?user_id=` | Vínculos do usuário. |
| GET | `/user-coupons/all` | Todos os vínculos. |
| GET | `/user-coupons/get/{user_coupon_id}?user_id=` | Busca um vínculo. |
| GET | `/user-coupons/user/{user_id}` | Vínculos de um usuário. |
| GET | `/user-coupons/coupon/{coupon_id}` | **Vínculos de um cupom** (usado no Admin p/ pré-marcar). |
| DELETE | `/user-coupons/delete/{user_coupon_id}?user_id=` | Remove vínculo. |

### 5.4. Frontend — arquivos (novos e alterados)

**Novo:**
- `src/components/SecaoCupons.jsx` — seção do checkout que lista os cupons do usuário, com cartões clicáveis (código, desconto, validade, mín. compra, máx. desconto, produto), botão "Remover cupom".

**Alterados:**
- `src/api/coupons.js` — `couponService` ganhou: `meusCupons()`, `vinculosDoCupom(id)`, `atribuir(userId, couponId)`, `removerVinculo(vinculoId, userId)`.
- `src/pages/Checkout.jsx` — lista via `meusCupons()` (só cupons do usuário logado); filtra ativos/não expirados/aplicáveis/min-purchase; estima desconto (mesma regra do backend); envia `coupon_id` no pedido; `Total = base − desconto`.
- `src/components/ResumoPedido.jsx` — linha "Desconto (CÓDIGO)" e total ajustado.
- `src/components/ModalCupom.jsx` — bloco **"Atribuir a usuários"** (checkboxes de leitores), props `usuarios` e `vinculosIniciais`; devolve IDs selecionados no `onSalvar`.
- `src/pages/Admin.jsx` — aba "Descontos & Cupons" (CRUD + atribuição); `handleEditarCupom` carrega vínculos antes de montar o modal; `handleSalvarCupom` faz **diff** (cria vínculos novos, remove desmarcados).

### 5.5. Regras de negócio (importantes)

- **Desconto é recalculado no backend** (`order_service._calculate_totals`); o front só estima.
  - `percentage`: `subtotal * value/100`, limitado por `max_discount`.
  - `fixed`: `value` absoluto, limitado ao subtotal.
- **Posse:** cupom não atribuído ao usuário → **403 `COUPON_NOT_ASSIGNED`** (mensagem PT: "Este cupom não está atribuído ao seu usuário.").
- **Validações do backend:** ativo, não expirado, `product_id` compatível com itens, `min_purchase`.
- **Admin (opção escolhida):** atribuição via **multi-seleção no modal de criar/editar cupom** (não botão individual por linha).

### 5.6. Migration — atenção
- `8cf455aabd0d_user_coupons` já existe no disco e **já foi aplicada** (tabela criada).
- A cadeia é: `<base> → fb4e3ed8eb4c → dfaa470fc553 → 8cf455aabd0d (head)`.
- Em outro ambiente: rodar `alembic upgrade head` da **raiz** do repo.

---

## 6. Estado do repositório (git)

Branch com alterações **não commitadas**. Resumo do `git status` (sem `.pyc`/coverage):

**Modificados (M):**
```
alembic/env.py
backend/app/api/exceptions.py
backend/app/api/router.py
backend/app/api/v1/orders.py
backend/app/models/coupon.py
backend/app/models/user.py
backend/app/services/order_service.py
backend/tests/conftest.py
backend/tests/http_tests/test_http_orders.py
backend/tests/service_tests/test_order_service.py
frontend/Papiro/src/api/coupons.js
frontend/Papiro/src/components/ModalCupom.jsx
frontend/Papiro/src/pages/Admin.jsx
frontend/Papiro/src/pages/Checkout.jsx
```

**Novos (??):**
```
alembic/versions/8cf455aabd0d_user_coupons.py
backend/app/api/v1/user_coupons.py
backend/app/models/user_coupon.py
backend/app/repositories/user_coupon_repo.py
backend/app/schemas/user_coupon.py
backend/app/services/user_coupon_service.py
backend/tests/service_tests/test_user_coupon_service.py
```

> ⚠️ A maior parte do backend de `UserCoupon` **já estava no working tree** (não commitada)
> quando a feature foi retomada. O trabalho desta sessão completou o frontend + o erro
> específico `COUPON_NOT_ASSIGNED`.

---

## 7. Validação atual

- **Backend:** `591 passed` (era 590 antes do teste novo), codificação de erro coberta por HTTP test.
- **Frontend:** `npx eslint src/` limpo nos arquivos tocados; `npm run build` OK.
- **Ruff:** há erros **pré-existentes** de whitespace em vários arquivos (ex.: `review_service.py`,
  final de `exceptions.py` sem newline). Não foram introduzidos pela feature.

---

## 8. Backlog sugerido (próximas partes)

Ordem proposta (do mais impactante ao menor), seguindo a regra "parte por parte":

1. **Limpeza de código morto** — remover métodos de service órfãos (§3) e `mascararCartao`.
2. **Users / Minha Conta** — trocar senha (`POST /users/change_password/...`), editar perfil.
3. **Wishlist** — evitar duplicatas e completar CRUD (`/get`, `/all`, `/product`, `/update`).
4. **Orders** — histórico detalhado (`get`, `items`), cancelar (`update`/`delete`).
5. **Cart** — `decrease`, `get`/`items` avulsos.
6. **Products/Categories/Reviews** — buscas por slug/isbn/ano/idioma; CRUD de categorias; reviews por usuário/nota.
7. **Newsletter** — implementar no backend o `POST /newsletter/subscribe` ou remover o service do front.

---

## 9. Como pedir no novo chat (sugestão de prompt)

> "Estou no projeto E-commerce v1 (FastAPI + React/Vite). Leia o `HANDOFF.md` na raiz
> para contexto. Vamos trabalhar **parte por parte**. Próxima parte: [X]. Antes de
> alterar código, faça o levantamento e me apresente um plano."
orderService.obter/itens/atualizar/excluir, productService.listarPorCategoria/atualizar, addressService.padrao, reviewService.atualizar, mascararCartao