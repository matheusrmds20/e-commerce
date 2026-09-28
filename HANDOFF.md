# Handoff — E-commerce v1 (Frontend/Backend)

> Documento de contexto para iniciar um **novo chat**. Resume o que foi analisado,
> o que o frontend consome, endpoints não usados, e as features já implementadas
> (Cupons por usuário, Users/Minha Conta, Wishlist segura) e o estado do repositório.
>
> Última atualização: **Parte 10 — limpeza de endpoints órfãos** — removidas
> **11 rotas** nunca consumidas pelo front: 9 de `/coupons` e 2 de `/wishlists`
> (+ métodos de service/repo/schema e testes). Antes disso: **Parte 9** (edição
> de produtos no Admin) e **Parte 8** (segurança em `/users`).

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
python -m pytest tests/ -q          # atualmente: 561 passed (~13s, cobertura 87%)
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

> ⚠️ **Regras de trabalho do usuário:** implementar **parte por parte**, sempre
> apresentando o levantamento e um plano **antes** de tocar em código; e
> **atualizar este HANDOFF.md ao final de cada task concluída**.

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
| `orders.js` | `orderService` | pedidos: `criar`, `listar`, `cancelar` |
| `reviews.js` | `reviewService` | avaliações |
| `wishlist.js` | `wishlistService` | lista de desejos |
| `coupons.js` | `couponService` | **cupons + vínculos (novo)** |
| `users.js` | `userService` | **novo (Users parte B)**: `atualizar`, `alterarSenha` |
| `admin.js` | `adminService` | dashboard, pedidos, usuários |
| `cards.js` | `cardService` | **cartões são 100% localStorage** (não há endpoint) |
| `newsletter.js` | `newsletterService` | ✅ ativo (Parte 7 — Home + aba do Admin) |
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
| `addressService` | `criar`, `listar`, `definirPadrao`, `atualizar`, `excluir` | — |
| `productService` | `listar`, `obter`, `listarPorDesconto`, `listarPorAtivo`, `listarDestaques`, `listarMaisVendidos`, `listarPaginado`, `recomendacoes`, `criar`, `atualizar`, `excluir` | ❌ `listarPorCategoria` (removido na limpeza) |
| `categoryService` | `listar` | — |
| `cartService` | `criar`, `obter`, `adicionarItem`, `atualizarQuantidade`, `removerItem`, `limpar` | — |
| `orderService` | `criar`, `listar`, `cancelar` | — |
| `reviewService` | `listarPorProduto`, `criar`, `excluir` | — |
| `wishlistService` | `adicionar`, `listar`, `buscarPorProduto`, `excluir` (todos sem `userId` — auth por token) | — |
| `couponService` | `listar`, `criar`, `atualizar`, `excluir`, `meusCupons`, `vinculosDoCupom`, `atribuir`, `removerVinculo` | — |
| `adminService` | `obterEstatisticas`, `listarPedidos`, `atualizarStatusPedido`, `listarUsuarios` | — |
| `cardService` | `listar`, `criar`, `atualizar`, `excluir`, `definirPadrao` | — (localStorage; `salvarTodos` é interno) |
| `newsletterService` | `inscrever`, `listarInscritos` | — |

> Membros de service órfãos foram **removidos** na limpeza de código morto
> (exceção: `productService.atualizar` foi mantido — e **passou a ser usado**
> na Parte 9, botão "Editar" da aba Acervo). Também removidos: `mascararCartao` (em `cards.js`) e,
> em `adapters.js`, `itensParaOrderPayload` e `pedidoParaView`.
> ¹ `productService.atualizar` agora é chamado pelo botão **"Editar"** de cada
> linha da aba Acervo do Admin (`PATCH /products/update/{id}`).
> Componentes de `src/components/` foram auditados: **nenhum** está órfão.

---

## 4. Endpoints do backend NÃO consumidos pelo frontend

O backend expõe **muito mais** do que o front consome. Agrupado por área:

### Products (`/products`) — **busca + admin na Parte 6c**
- **Removidos como órfãos (match exato):** `GET /title/{title}`, `GET /slug/{slug}`,
  `GET /isbn/{isbn}`, `GET /publisher/{publisher}`, `GET /year/{year}`,
  `GET /language/{language}`, `GET /stock/{qty}` (rotas + métodos de service/repo).
  A busca por termo livre agora vive em `GET /paginated?search=` (`ILIKE`
  case-insensitive sobre **título, autor e ISBN**, aplicada no banco antes de
  paginar; `meta.total` reflete o filtro).
- **Escritas exigem admin do token** (401 sem token, 403 `INSUFFICIENT_PERMISSION`):
  `POST /create`, `PATCH /update/{id}`, `DELETE /delete/{id}`. O router traduz
  ValueErrors: duplicado → **409 `DUPLICATE_PRODUCT`**, inexistente → **404**
  (`CATEGORY_NOT_FOUND`/`PRODUCT_NOT_FOUND`) — antes viravam 500.
- **Públicos e usados:** `list`, `get/{id}`, `paginated`, `recommendations`,
  `featured`, `bestsellers`, `category/{id}`, `discount/{pct}`, `active/{bool}`
  (os dois últimos alimentam a Home). **`update` agora é usado** pelo botão
  "Editar" da aba Acervo do Admin (Parte 9): `PATCH /products/update/{id}`
  (admin), PATCH parcial — campos vazios são omitidos e o `slug` não é
  regerado ao editar.

### Categories (`/categories`) — **escrita restrita a admin na Parte 6b**
Usados pelo front: `GET /list` (público), `POST /create`, `PATCH /update/{id}`,
`DELETE /delete/{id}` (**admin apenas** — 401 sem token, 403
`INSUFFICIENT_PERMISSION` sem papel). Também públicos e agora com tradução de
404: `GET /get/{id}`, `GET /name/{name}`, `GET /slug/{slug}`. Duplicado de
nome/slug → **409 `DUPLICATE_CATEGORY`** (antes os ValueErrors viravam 500).

### Coupons (`/coupons`) — **limpo na Parte 10**
Usados no Admin: `create`, `list`, `update/{id}`, `delete/{id}`.
**Removidos como órfãos (9 rotas):** `GET /get/{id}`, `GET /code/{code}`,
`GET /product/{id}`, `GET /valid-until/{d}`, `GET /max-uses/{n}`,
`GET /discount-type/{t}`, `GET /discount-value/{v}`, `GET /min-purchase/{v}`,
`GET /max-discount/{v}` — e os métodos de service correspondentes
(`CouponService.get_by_*`) + lookups órfãos do repo (`get_by_product_id`,
`get_by_valid_until`, `get_by_max_uses`, `get_by_discount_type`,
`get_by_discount_value`, `get_by_min_purchase`, `get_by_max_discount`,
`get_by_created_at`, `get_by_updated_at`). O repo mantém só `get_by_code`
(usado por `create`/`update`) + `get_by_id`/`get_all` da base.

### Cart (`/cart`) — **limpo na Parte 5**
Rotas restantes (todas escopadas ao usuário do token): `POST /create`, `GET /cart/me`,
`POST /{cart_id}/items/add`, `PATCH /{cart_id}/items/update/{item_id}`, `DELETE .../delete/{item_id}`, `DELETE .../clear`.
**Removidos como órfãos:** `GET /get/{id}`, `GET /items/{id}`, `PATCH .../decrease/{id}`
e `DELETE /delete/{id}` — o front decrementa via `update` com valor absoluto, e o
`update` agora **remove o item quando `quantity <= 0`** (herdando o comportamento do
`decrease`). Métodos órfãos removidos: `CartService.get_by_id/get_with_items/decrease_item/delete`
e `CartItemRepository.decrease_quantity`.

### Orders (`/orders`) — **cancelamento implementado na Parte 4**
Rotas atuais (todas escopadas ao usuário do token):
`POST /create`, `GET /list`, `PATCH /update/{id}` (usado para **cancelar** pelo
cliente), `DELETE /delete/{id}`.
**Removidos como redundantes:** `GET /get/{id}` e `GET /items/{id}` — os itens já
vêm embutidos em `OrderResponse.order_items`, então não havia ganho de UI.
Também removidos do service os métodos órfãos `OrderService.get_by_id` e
`OrderService.get_with_items` (o repo homônimo continua usado internamente).

### Users (`/users`) — **protegido na parte A de "Users / Minha Conta"**
`PATCH /update/{id}`, `POST /change_password/{id}/change-password` e `DELETE /delete/{id}`
exigem Bearer token + ownership (dono ou admin; 403 `USER_FORBIDDEN`).
`GET /user_id/{id}` e `GET /email/{email}` são restritos a **admin** (403
`INSUFFICIENT_PERMISSION`). `POST /create` exige **admin** do token (401 sem
token, 403 sem papel) e aceita escolher o papel via `role` (default `ADMIN`,
agora seguro — antes era público e criava ADMIN por padrão).

### Wishlist (`/wishlists`) — **protegida na Parte 3 (A+B)**
O dono vem do **token** (`Depends(get_current_user)`), não mais da query `user_id`
(IDOR fechado). Item de terceiro → **403 `WISHLIST_FORBIDDEN`**; admin opera sobre
qualquer usuário. `GET /wishlists/all` é restrito a admin.
Usados pelo front: `create`, `list`, `product/{id}` (novo, no DetalheLivro), `delete/{id}`.
**Removidos como órfãos na Parte 10 (2 rotas):** `GET /get/{id}` e
`PATCH /update/{id}` — + métodos de service `get_by_id`/`update`
(e `get_by_created_at`/`get_by_updated_at`, sem rota), lookups do repo
`get_by_created_at`/`get_by_updated_at` e o schema `WishlistUpdate`.
O repo mantém `get_by_product_id` + `get_by_id`/`get_by_user_id`/`get_all` da base.

### Reviews (`/reviews`) — **protegido na Parte 6a (fecha IDOR)**
O autor vem do **token**; criar/atualizar/excluir exigem Bearer. Avaliação de
terceiro → **403 `REVIEW_FORBIDDEN`**; admin opera sobre qualquer uma.
`GET /list` = minhas avaliações (admin pode `?user_id=`).
**Removidos como órfãos:** `GET /get/{id}`, `GET /rating/{rating}` e o antigo
`GET /user/{user_id}` (virou `/list` autenticado). **Novo em uso:**
`PATCH /update/{id}` (editar review).

### Addresses (`/addresses`) — não usados
`GET /get/{address_id}`, `GET /zip/{zip_code}`.

### Auth / Admin / User-coupons
100% cobertos (todos usados). **Novo:** `/user-coupons` (ver seção 5).

### Newsletter (`/newsletter`) — **implementado na Parte 7**
Usados pelo front: `POST /subscribe` (**público** — Home; duplicado → 409
`NEWSLETTER_ALREADY_SUBSCRIBED`) e `GET /list` (**admin** — aba Newsletter do
Admin). **Não usado:** `POST /unsubscribe` (público; mantido para o link de
descadastro dos e-mails).

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

## 5b. Feature implementada: Wishlist segura + toggle (Parte 3)

### 5b.1. Conceito
A lista de desejos deixou de aceitar `user_id` arbitrário na query string. O dono
vem **do token**; um cliente só acessa a própria wishlist (admin acessa qualquer
uma). No DetalheLivro, o botão virou **toggle** (adicionar ⇄ remover).

### 5b.2. Parte B — Backend (endurecimento de auth, fecha IDOR)
**Alterados:**
- `backend/app/services/wishlist_service.py` — assinaturas recebem `current_user`;
  `_ensure_owner_or_admin` (dono/admin) em `get_by_id`/`update`/`delete`;
  `get_by_user_id(current_user, user_id=None)` (comum só o próprio; admin pode alvo);
  `get_by_product_id(product_id, current_user)` filtra pela posse (admin vê todos);
  `get_all(current_user)` exige admin; `create(data, current_user)` grava para o logado.
- `backend/app/api/v1/wishlist.py` — removido `UserId = Query(...)`; injetado
  `AuthUser = Depends(get_current_user)`; traduz `"not owned by user"` → 403
  `WISHLIST_FORBIDDEN` e `"Admin permission required"` → 403.
- `backend/app/api/exceptions.py` — nova `WishlistForbiddenException` (403, code
  `WISHLIST_FORBIDDEN`).
- `backend/tests/service_tests/test_wishlist_service.py` — assinaturas novas +
  casos de admin e de filtragem por usuário.
- `backend/tests/http_tests/test_http_wishlist.py` — fixture `auth_user`, casos
  401 (sem token) e 403 (item de terceiro / `/all` de cliente).

**Comportamento das rotas `/wishlists/*`:** sem token → 401; item de outro
usuário → 403 `WISHLIST_FORBIDDEN`; admin opera sobre qualquer usuário;
`GET /wishlists/all` só admin; `GET /wishlists/product/{id}` — comum vê só o
próprio item.

### 5b.3. Parte A — Frontend
- `frontend/Papiro/src/api/wishlist.js` — reescrito: métodos sem `userId`
  (`adicionar`, `listar`, `excluir`); novo `buscarPorProduto(productId)` →
  `GET /wishlists/product/{id}` (404 vira `[]`).
- `frontend/Papiro/src/pages/DetalheLivro.jsx` — checagem "já nos desejos" usa
  `buscarPorProduto` (não baixa mais a lista toda); guarda `wishlistItemId`;
  `adicionarAosDesejos` → `alternarDesejo` (**toggle** adicionar/remover; se faltar
  o id, reconsulta antes de remover).
- `frontend/Papiro/src/components/PainelCompra.jsx` — rótulo
  `"Adicionar aos desejos"` ⇄ `"Remover dos desejos"`.
- `frontend/Papiro/src/pages/MinhaConta.jsx` (`AbaWishlist`) — 3 chamadas sem
  `usuario.id`.

### 5b.4. Validação
- Backend: **605 passed** após a Parte 4 (era 617 antes de remover os 12 testes dos endpoints órfãos de orders).
- Frontend: ESLint limpo, build OK.
- Zero referências ao formato antigo (`grep` confirmou).

---

## 5c. Feature implementada: Cancelar pedido + remoção de endpoints órfãos (Parte 4)

### 5c.1. Conceito
O cliente agora pode **cancelar o próprio pedido** pela aba "Meus pedidos"
(antes só o admin mudava status). Aproveitou-se para **remover dois endpoints
redundantes** de orders, que nunca tiveram uso e cujo dado já vem embutido.

### 5c.2. Frontend — cancelar pedido
- `frontend/Papiro/src/api/orders.js` — novo `cancelar(orderId)` →
  `PATCH /orders/update/{id}` com `{ status: 'cancelled' }`.
- `frontend/Papiro/src/pages/MinhaConta.jsx` (`AbaPedidos`) — botão
  **"Cancelar pedido"** visível só quando `status` ∈ {`pending`, `processing`};
  usa o componente `Confirmacao`; recarrega a lista após cancelar (sem update
  otimista). Estados `paraCancelar`/`cancelando`.
- `frontend/Papiro/src/components/Confirmacao.jsx` — nova prop opcional
  `textoOcupado` (default `'Excluindo…'`) para o botão de cancelamento dizer
  "Cancelando…".

**Regras do backend já existentes (reutilizadas):** posse validada (**403** se
não for o dono), **devolve estoque** ao cancelar, e recusa cancelar um pedido já
cancelado (**400** `INVALID_STATE_TRANSITION`).

### 5c.3. Backend — remoção dos endpoints redundantes
- `backend/app/api/v1/orders.py` — removidas as rotas `GET /orders/get/{id}` e
  `GET /orders/items/{id}`; import de `OrderItemResponse` removido.
- `backend/app/services/order_service.py` — removidos os métodos órfãos
  `get_by_id` e `get_with_items` (o **repo** homônimo continua usado internamente
  por `create`/`update`).
- Testes removidos: `TestGetOrder` (HTTP) e `TestGetByID`/`TestGetWithItems`
  (service), mais os 2 `TestAuthRequired` dessas rotas — 12 testes no total.

**Rotas `/orders` após a limpeza:** `POST /create`, `GET /list`,
`PATCH /update/{id}`, `DELETE /delete/{id}`.
> `OrderItemResponse` **permanece** no schema — é usado por
> `OrderResponse.order_items`.

### 5c.4. Validação
- Backend: **605 passed**.
- Frontend: ESLint limpo, build OK.
- Ruff: nenhum erro novo (os 4 de `order_service.py` são pré-existentes do HEAD).
- OpenAPI confirma que as rotas removidas sumiram.

---

## 5d. Feature implementada: limpeza de Cart (Parte 5)

- **Backend:** removidas 4 rotas órfãs de `/cart` (`get/{id}`, `items/{id}`,
  `decrease/{item_id}`, `delete/{cart_id}`) e os métodos de service/repo
  correspondentes. O `PATCH .../items/update/{item_id}` agora trata `quantity <= 0`
  como remoção do item (antes gravava 0 — pendência documentada).
- **Frontend:** nenhum código alterado; apenas o comentário de contrato em
  `src/api/cart.js` atualizado (o botão "−" da sacola sempre usou `atualizarQuantidade`).
- **Testes:** 23 removidos (10 HTTP + 13 service, incluindo o substituído
  `test_update_quantity_zero_reaches_service`); 2 novos cobrindo a remoção em `quantity=0`.
- **Validação:** 584 passed; ESLint limpo; build OK; nenhum erro novo de ruff.

---

## 6. Estado do repositório (git)

Branch com alterações **não commitadas** (o restante das features anteriores já foi
commitado). Resumo atual do `git status` (sem `.pyc`/coverage):

**Modificados (M):**
```
HANDOFF.md
backend/app/api/exceptions.py
backend/app/api/v1/cart.py
backend/app/api/v1/orders.py
backend/app/api/v1/users.py
backend/app/api/v1/wishlist.py
backend/app/repositories/cart_item_repo.py
backend/app/services/cart_service.py
backend/app/services/order_service.py
backend/app/services/user_service.py
backend/app/services/wishlist_service.py
backend/tests/http_tests/test_http_cart.py
backend/tests/http_tests/test_http_orders.py
backend/tests/http_tests/test_http_users.py
backend/tests/http_tests/test_http_wishlist.py
backend/tests/service_tests/test_cart_service.py
backend/tests/service_tests/test_order_service.py
backend/tests/service_tests/test_user_service.py
backend/tests/service_tests/test_wishlist_service.py
frontend/Papiro/src/api/adapters.js
frontend/Papiro/src/api/addresses.js
frontend/Papiro/src/api/cards.js
frontend/Papiro/src/api/orders.js
frontend/Papiro/src/api/products.js
frontend/Papiro/src/api/reviews.js
frontend/Papiro/src/api/wishlist.js
frontend/Papiro/src/components/Confirmacao.jsx
frontend/Papiro/src/components/PainelCompra.jsx
frontend/Papiro/src/pages/DetalheLivro.jsx
frontend/Papiro/src/pages/MinhaConta.jsx
```

**Novos (??):**
```
frontend/Papiro/src/api/users.js
```

> ⚠️ Features anteriores (Cupons por usuário, migration `8cf455aabd0d`, etc.) **já
> foram commitadas**. O que está pendente agora inclui: endurecimento de auth em
> `/users` e `/wishlists`, o `users.js` do front, o toggle da wishlist e a limpeza
> de Cart da Parte 5.

> ⚠️ A maior parte do backend de `UserCoupon` **já estava no working tree** (não commitada)
> quando a feature foi retomada. O trabalho desta sessão completou o frontend + o erro
> específico `COUPON_NOT_ASSIGNED`.

---

## 7. Validação atual

> Números citados nas seções 5b–5e e 8 são **snapshots históricos por parte**
> (mostram a evolução da suíte). O estado **atual** é o abaixo: **561 passed**.

- **Backend:** `561 passed` (~13s, cobertura 87%; 60 warnings — todos
  `StarletteDeprecationWarning` de `HTTP_422_UNPROCESSABLE_ENTITY`, cosméticos).
  (Parte 10: −39 testes dos endpoints órfãos de coupons/wishlist.)
- **Frontend:** `npx eslint src/` limpo; `npm run build` OK (warning pré-existente de
  chunk >500 kB). Após a limpeza de código morto: eslint limpo, build OK e grep
  confirmando zero referências aos símbolos removidos.
- **Ruff:** há erros **pré-existentes** de whitespace em vários arquivos (ex.: `review_service.py`,
  final de `exceptions.py` sem newline). Não foram introduzidos pelas features.

---

## 8. Backlog sugerido (próximas partes)

Ordem proposta (do mais impactante ao menor), seguindo a regra "parte por parte":

1. ~~**Limpeza de código morto**~~ — ✅ **CONCLUÍDO**. Removidos: `addressService.padrao`,
   `productService.listarPorCategoria`, `orderService.obter/itens/atualizar/excluir`,
   `reviewService.atualizar`, `mascararCartao` (`cards.js`), `itensParaOrderPayload` e
   `pedidoParaView` (`adapters.js`). Mantido: `productService.atualizar`. Validação:
   eslint limpo, build OK, zero referências restantes. Cabeçalho de `orders.js`
   atualizado (só documenta create/list).
2. ~~**Users / Minha Conta**~~ — ✅ **CONCLUÍDO** (partes A e B).
   - **Parte A — segurança em `/users` (backend):** `update`,
     `change_password` e `delete` exigem token + dono/admin (403 `USER_FORBIDDEN`);
     `GET /user_id/{id}` só admin. Regra de dono/admin implementada NO SERVICE
     (`UserService._ensure_owner_or_admin` / `_ensure_admin`; router só injeta
     `AuthUser` e repassa). 13 testes novos (fixture `auth_user` no HTTP + classe
     `TestOwnershipOrAdmin` no service). **604 passed**.
   - **Parte B — frontend:** criado `src/api/users.js` (`atualizar`, `alterarSenha`).
     Aba "Dados pessoais" de `MinhaConta.jsx` refatorada: modo leitura por padrão
     (lista nome/e-mail/membro desde + botão "Editar dados"), form de edição com
     validação client + Cancelar, e seção "Alterar senha" (senha atual/nova/
     confirmação, toggle mostrar, espelha regras do backend; 400
     `INVALID_CURRENT_PASSWORD` vira erro de campo). Seção de senha é
     **compacta/retrátil**: título + botão "Alterar senha"; o form só aparece
     ao expandir. `api` inline removido da página. ESLint limpo, build OK.
   Pendências de segurança **RESOLVIDAS** na Parte 8 (ver seção 5f):
   `GET /users/email/{email}` agora é **admin-only** e `POST /users/create`
   exige **admin** (antes criava ADMIN por padrão e era público).
3. ~~**Wishlist**~~ — ✅ **CONCLUÍDO** (partes A e B).
   - **Parte B — backend (auth, fecha IDOR):** dono vem do **token**, não mais da
     query `user_id`. `_ensure_owner_or_admin` no service; `get_by_product_id`
     filtra pela posse (admin vê todos); `get_all` exige admin; nova
     `WishlistForbiddenException` (403 `WISHLIST_FORBIDDEN`). 13 testes novos.
   - **Parte A — frontend:** `wishlist.js` sem `userId` + novo `buscarPorProduto`;
     DetalheLivro usa esse endpoint e o botão virou **toggle** (adicionar/remover);
     `PainelCompra` com rótulo dinâmico; `MinhaConta` sem `usuario.id`.
   > Nota: duplicata **já era** tratada (409 `WISHLIST_DUPLICATE` nas duas camadas);
   > o ganho real foi segurança + eficiência (não baixar a lista toda) + toggle.
4. ~~**Orders**~~ — ✅ **CONCLUÍDO** (Parte 4).
   - **Frontend:** `orderService.cancelar(id)` (via `PATCH /update/{id}` com
     `status: 'cancelled'`); botão **"Cancelar pedido"** na aba "Meus pedidos"
     (só para `pending`/`processing`), com `Confirmacao`. `Confirmacao` ganhou a
     prop opcional `textoOcupado`.
   - **Backend:** removidos os endpoints redundantes `GET /get/{id}` e
     `GET /items/{id}` (os itens já vêm em `OrderResponse.order_items`) e os
     métodos órfãos `OrderService.get_by_id`/`get_with_items`.
   > Cancelar devolve estoque e recusa pedido já cancelado (400); posse → 403.
5. ~~**Cart**~~ — ✅ **CONCLUÍDO** (Parte 5). Removidos os endpoints órfãos
   `GET /cart/get/{id}`, `GET /cart/items/{id}`, `PATCH /cart/{id}/items/decrease/{id}`
   e `DELETE /cart/delete/{id}` (o front usa `update` com valor absoluto, que agora
   **remove o item quando `quantity <= 0`** — comportamento herdado do `decrease`).
   Métodos órfãos removidos: `CartService.get_by_id/get_with_items/decrease_item/delete`
   e `CartItemRepository.decrease_quantity`. 23 testes removidos, 2 novos (zero
   remove item na service e na rota). **584 passed**.
6. **Products/Categories/Reviews** — ✅ **CONCLUÍDO**. 
    **Parte 6a (Reviews) concluída:**
   - **Backend:** dono da avaliação vem do **token** (fecha IDOR de `user_id` na
     query). `POST /create` grava para o autenticado; `PATCH /update/{id}` e
     `DELETE /delete/{id}` exigem dono/admin (**403 `REVIEW_FORBIDDEN`**, nova
     exceção em `exceptions.py`). `GET /list` virou "minhas avaliações"
     (admin pode alvejar `?user_id=`); `GET /product/{id}` segue público, agora
     com tradução 404 `PRODUCT_NOT_FOUND`. **Removidos como órfãos:**
     `GET /get/{id}`, `GET /rating/{rating}` (rota + service + `review_repo.get_by_rating`)
     e o antigo `GET /user/{user_id}`. O service também ganhou tradução de erros
     no router (antes ValueErrors viravam 500: duplicada agora é **409
     `DUPLICATE_REVIEW`**, não encontrado **404 `REVIEW_NOT_FOUND`**).
   - **Frontend:** `reviews.js` sem `userId` (`criar(payload)`, `excluir(id)`,
     novo `atualizar(id, payload)` e `listarMinhas(userId?)`). `DetalheLivro.jsx`
     sem `usuario.id` nas chamadas + handler `salvarEdicaoAvaliacao`;
     `DetalhesLivro.jsx` ganhou botão **"Editar"** na avaliação própria com form
     inline (nota ★ + comentário pré-preenchidos, Salvar/Cancelar).
   - **Validação:** 582 passed (46 testes antigos de reviews → 44 novos);
     eslint limpo; build OK.
   - **Parte 6b (Categories) concluída:**
     - **Backend:** `CategoryService` ganhou `_ensure_admin`; `create`/`update`/
       `delete` exigem **admin do token** (401 sem token, 403
       `INSUFFICIENT_PERMISSION`). Router traduz ValueErrors: duplicado →
       **409 `DUPLICATE_CATEGORY`**, não encontrado → **404
       `CATEGORY_NOT_FOUND`** (get/{id}, name, slug também traduzidos).
     - **Frontend:** `categoryService` ganhou `criar`/`atualizar`/`excluir`;
       novo componente `ModalCategoria.jsx` (nome, slug com sugestão
       automática, descrição, imagem, ativo); aba **"Categorias"** no Admin
       (sidebar + mobile) com tabela e CRUD completo; filtro por termo de
       busca (`categoriasFiltradas`); botão do cabeçalho contextual
       ("Nova Categoria").
     - **Validação:** 591 passed (+9 líquido); eslint limpo; build OK.
   - **Parte 6c (Products) concluída — etapa 8.6 ✅ completa:**
     - **Backend:** `GET /products/paginated` ganhou `?search=` (termo livre,
       `ILIKE %termo%` sobre **título, autor e ISBN** no `ProductRepository.paginate`,
       antes de paginar; `max_length=100`; termo só de espaços = sem busca).
       `POST /create`, `PATCH /update/{id}` e `DELETE /delete/{id}` exigem **admin
       do token** (`ProductService._ensure_admin`, mesmo padrão de categorias).
       Removidos como órfãos os endpoints de match exato `title`, `slug`, `isbn`,
       `publisher`, `year`, `language`, `stock` (rotas + métodos de service;
       `repo.get_by_title/get_by_slug` foram mantidos para a unicidade no
       create/update). O router de products agora traduz ValueErrors também em
       create/update/delete: duplicado → **409 `DUPLICATE_PRODUCT`**, categoria/
       produto inexistente → **404**, sem permissão → **403
       `INSUFFICIENT_PERMISSION`** (antes eram 500). `GET /active/{bool}` foi
       mantido — a Home usa (`home.js` chama `listarPorAtivo`).
     - **Frontend:** `listarPaginado` aceita `search`; `Acervo.jsx` ganhou barra
       de busca (debounce 300ms + Enter para comitar já, botão × para limpar),
       contagem "N títulos para “termo”" e estado vazio com ação "Limpar busca".
       O wrapper órfão `productService.listarPorCategoria` foi removido (sem
       chamadores; o backend mantém `GET /products/category/{id}`).
       **Correção pós-análise:** o debounce/`comitarBusca` só reseta para a
       página 1 quando o termo **muda de fato** (`buscaRef`); antes, digitar e
       apagar dentro dos 300ms (ou alternar espaços) resetava a página sem
       mudar o filtro.
     - **Validação:** 579 passed; ruff limpo nos arquivos tocados; eslint limpo;
       build OK (chunk >500 kB é pré-existente).
## 5e. Feature implementada: Newsletter (Parte 7)

    - **Backend:** novo modelo `NewsletterSubscriber` (`newsletter_subscribers`:
      `id`, `email` único/indexado, `subscribed_at`; **sem FK para users** — aceita
      visitantes sem conta). Migration `a1f2e3d4c5b6` aplicada. Router
      `/newsletter`:
      - `POST /newsletter/subscribe` — **público**; normaliza e-mail
        (lower/strip); duplicado → **409 `NEWSLETTER_ALREADY_SUBSCRIBED`**.
      - `POST /newsletter/unsubscribe` — **público**; e-mail inexistente →
        **404 `NEWSLETTER_SUBSCRIBER_NOT_FOUND`**; sucesso → 200 com mensagem.
      - `GET /newsletter/list` — **admin do token**; sem permissão → **403**,
        sem inscritos → **404**.
      Service/repo seguem o padrão do projeto (`ValueError` traduzido pela rota
      em `_traduzir_value_error`).
    - **Frontend:** `api/newsletter.js` deixou de fingir 404 — `inscrever` agora
      chama o endpoint real (409 vira mensagem amigável) e ganhou
      `listarInscritos()` (admin). O componente `Newsletter.jsx` da Home passou a
      funcionar sem alterações. O painel `Admin.jsx` já possuía um scaffold da aba
      (botão na sidebar/mobile, título e bloco de carga "3b"); ativada a seção com
      tabela de inscritos (ID, e-mail, data) e filtro `inscritosFiltradas`
      (busca por e-mail, usa o `termoBusca` do cabeçalho; sem botão "+" nessa aba).
    - **Validação:** 594 passed (15 novos: 7 service + 8 http); ruff limpo nos
      arquivos novos; eslint limpo; build OK (chunk >500 kB é pré-existente).

---

## 5f. Feature implementada: segurança em `/users` (Parte 8)

Fecha as **duas pendências de segurança** registradas na Parte A de Users.

### 5f.1. Bug 1 — `POST /users/create` público e com default ADMIN
- **Antes:** rota **pública** e schema `AdminUserCreate | CustomerUserCreate`
  (com `AdminUserCreate.role` default `ADMIN`) → qualquer visitante criava um
  **ADMIN** ao omitir `role`.
- **Agora:** rota exige `AuthUser` e o service valida admin
  (`UserService._ensure_admin`, mesmo padrão das outras escritas).
  - Sem token → **401**; cliente (customer) → **403 `INSUFFICIENT_PERMISSION`**.
  - Admin continua podendo escolher o papel via `role` (customer ou admin);
    admin que **omite** `role` cria outro ADMIN (default do schema, agora seguro).
- **Arquivos:** `app/api/v1/users.py` (rota `create_user` + `summary`),
  `app/services/user_service.py` (`create(data, current_user)`).

### 5f.2. Bug 2 — `GET /users/email/{email}` aberto
- **Antes:** sem autenticação → enumeração/vazamento de dados por e-mail.
- **Agora:** **admin-only**, simétrico a `GET /users/user_id/{id}`: rota exige
  `AuthUser` e o service chama `_ensure_admin`. Sem token → **401**;
  customer → **403 `INSUFFICIENT_PERMISSION`**.
- **Arquivos:** `app/api/v1/users.py` (rota `get_user_by_email` + `summary`),
  `app/services/user_service.py` (`get_by_email(email, current_user)`).

### 5f.3. Impacto
- **Frontend:** nenhuma mudança — o front **não** chama `POST /users/create`
  (o Admin só lista usuários) nem `GET /users/email/{email}`. O registro
  público (Home/`Registro`) usa `authService`/`auth_service`, que acessa o
  **repo** diretamente e **não** foi afetado.
- **Testes:** HTTP — todos os `TestCreateUser` passam a exigir admin; novos
  `test_create_requires_token`, `test_create_forbidden_for_customer`,
  `test_get_by_email_requires_token`, `test_get_by_email_forbidden_for_customer`;
  `test_create_without_role_defaults_to_admin` reescrito como comportamento
  seguro. Service — `create`/`get_by_email` recebem `current_user`; novos
  `test_create_forbidden_for_customer` e `test_get_by_email_forbidden_for_customer`.
- **Validação:** **600 passed** (+6); ruff limpo nos arquivos tocados; eslint
  limpo; build OK.

---

## 5g. Feature implementada: editar produto no Admin (Parte 9)

### 5g.1. Conceito
A aba **Acervo** do Admin só permitia criar e remover livros. Agora cada linha
(ao lado de "Remover") tem um botão **"Editar"** que abre o **mesmo modal** de
cadastro em modo edição — fechando a pendência do `productService.atualizar`
(existia no service desde a Parte 6c mas nenhuma tela o chamava).

### 5g.2. Frontend (`src/pages/Admin.jsx`) — único arquivo alterado
- **Estado:** novo `livroEditando` (`null` = modo criação).
- **Handlers:**
  - `handleNovoLivro()` — abre em criação (limpa form + `livroEditando`).
  - `handleEditarLivro(livro)` — pré-preenche título/autor/categoria/preço/estoque
    e abre o modal.
  - `handleSalvarLivro(e)` — substitui `handleCadastrarLivro`; ramifica:
    - **criar** (sem `livroEditando`): gera `slug` + `description` default,
      `is_active: true`, flags falsas; `productService.criar`.
    - **editar**: envia **apenas** `title`, `author`, `price`, `stock_qty`,
      `category_id` — e `description` **só se preenchida** (PATCH parcial; campos
      vazios omitidos). **Não regera o slug.** Chama
      `productService.atualizar(id, payload)` e atualiza a linha no estado.
  - `fecharModalLivro()` — fecha e limpa `livroEditando` (X e Cancelar).
  - `handleRemoverLivro` usa `setLivros(prev => ...)` (sem closure stale).
- **UI:** botão "Editar" (verde) + "Remover" na coluna Ações; título do modal
  ("Cadastrar Obra" ⇄ "Editar Obra"), label da Descrição ("(em branco mantém a
  atual)" no editar) e botão de submit ("Adicionar ao Catálogo" ⇄ "Salvar
  Alterações"). Os 2 gatilhos de abertura (botão do cabeçalho e "+ Adicionar
  Livro") usam `handleNovoLivro`.

### 5g.3. Backend
Nenhuma mudança — `PATCH /products/update/{id}` (admin, `ProductUpdate` parcial)
 já existia desde a Parte 6c.

### 5g.4. Validação
- Frontend: `npx eslint src/` limpo; `npm run build` OK (warning de chunk >500 kB
  é pré-existente).
- Backend: inalterado (**600 passed**).

---

## 5h. Feature implementada: limpeza de endpoints órfãos (Parte 10)

### 5h.1. Conceito
Remoção das rotas do backend que **nunca foram consumidas** pelo frontend
(código morto desde o início do projeto), seguindo o padrão das Partes 4/5/6.
Escopo desta parte: **Coupons** e **Wishlist**. **Addresses** e **Categories**
foram mantidos de propósito (decisão do usuário: `GET /addresses/zip/{zip}`
pode virar autopreenchimento de endereço; as buscas de Categories podem servir
a SEO/rotas públicas).

### 5h.2. Coupons — 9 rotas removidas
`GET /get/{id}`, `GET /code/{code}`, `GET /product/{id}`, `GET /valid-until/{d}`,
`GET /max-uses/{n}`, `GET /discount-type/{t}`, `GET /discount-value/{v}`,
`GET /min-purchase/{v}`, `GET /max-discount/{v}`.
- **Router** (`app/api/v1/coupons.py`): removidas as rotas + o import `datetime`
  (só usado por `valid-until`). Permanecem `create`, `list`, `update/{id}`,
  `delete/{id}`.
- **Service** (`app/services/coupon_service.py`): removidos `get_by_id`,
  `get_by_code`, `get_by_product_id`, `get_by_valid_until`, `get_by_max_uses`,
  `get_by_discount_type`, `get_by_discount_value`, `get_by_min_purchase`,
  `get_by_max_discount` + import `datetime`. Permanecem `get_all`, `create`,
  `update`, `delete`.
- **Repo** (`app/repositories/coupon_repo.py`): permanece só `get_by_code`
  (usado por `create`/`update`) — removidos os 7 lookups de filtro + os órfãos
  `get_by_created_at`/`get_by_updated_at`. `get_by_id`/`get_all` vêm da base.

### 5h.3. Wishlist — 2 rotas removidas
`GET /get/{id}` e `PATCH /update/{id}`.
- **Router** (`app/api/v1/wishlist.py`): removidas as rotas + import
  `WishlistUpdate`. Permanecem `create`, `list`, `all` (admin), `product/{id}`,
  `delete/{id}`.
- **Service** (`app/services/wishlist_service.py`): removidos `get_by_id`,
  `update` e os órfãos `get_by_created_at`/`get_by_updated_at` + import
  `datetime`. `_ensure_owner_or_admin` **permanece** (usado por `delete`).
- **Repo** (`app/repositories/wishlist_repo.py`): permanece `get_by_product_id`;
  removidos `get_by_created_at`/`get_by_updated_at`.
- **Schema** (`app/schemas/wishlist.py`): removido `WishlistUpdate` (ficou órfão).

### 5h.4. Testes
- **Coupons:** removidos `TestGetCoupon` e `TestCouponFilters` (HTTP) e os
  parametrizados `test_get_single_success/not_found` + metade de
  `test_get_list_*` (service).
- **Wishlist:** removidos `TestGetWishlistItem` e `TestUpdateWishlistItem`
  (HTTP) e os casos de `get_by_id`/`update`/`get_by_created_at`/`get_by_updated_at`
  (service).
- **Validação:** **561 passed** (era 600; −39); ruff limpo nos arquivos tocados
  (aproveitou-se para corrigir a ordenação de imports de `schemas/wishlist.py` e
  um whitespace pré-existente em `coupon_service.py`); OpenAPI confirma que as
  11 rotas sumiram (Coupons 13→4 paths, Wishlist 7→5).

---

## 9. Como pedir no novo chat (sugestão de prompt)

> "Estou no projeto E-commerce v1 (FastAPI + React/Vite). Leia o `HANDOFF.md` na raiz
> para contexto. Vamos trabalhar **parte por parte**. Próxima parte: [X]. Antes de
> alterar código, faça o levantamento e me apresente um plano."
