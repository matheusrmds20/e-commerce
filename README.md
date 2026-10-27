# 📚 Papiro — E-commerce de Livraria

![CI](https://github.com/matheusrmds20/e-commerce/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Loja virtual completa de livraria — catálogo, carrinho, cupons, wishlist, checkout,
frete real e pagamento — com **API REST em FastAPI** e **SPA em React + Vite**.

- 🛍️ **Frontend (demo):** <https://papiro.matheuslab.xyz>
- ⚙️ **API (demo):** <https://api-e-commerce.matheuslab.xyz>
- 📖 **Docs interativas (Swagger/ReDoc):** só com `DEBUG=true` — em produção ficam desligadas (ver [Segurança](#-segurança))

---

## 📑 Sumário

- [Funcionalidades](#-funcionalidades)
- [Stack](#-stack)
- [Arquitetura](#-arquitetura)
  - [Visão geral](#visão-geral)
  - [Estrutura de pastas](#-estrutura-de-pastas)
  - [Camadas do backend](#camadas-do-backend)
  - [Fluxo de compra e pagamento](#fluxo-de-compra-e-pagamento)
- [Como rodar](#-como-rodar)
- [Testes](#-testes)
- [Endpoints da API](#-endpoints-da-api)
- [Segurança](#-segurança)
  - [Controles implementados](#controles-implementados)
  - [Sessão e anti-abuso](#sessão-e-anti-abuso)
  - [Como foi verificado](#como-foi-verificado)
  - [Limites conhecidos](#limites-conhecidos)
  - [Reportar vulnerabilidades](#reportar-vulnerabilidades)
- [Decisões técnicas](#-decisões-técnicas)
  - [ADR-001 — Webhook de pagamento via threadpool (não Celery)](#adr-001--webhook-de-pagamento-via-threadpool-não-celery)
  - [ADR-002 — Validação de assinatura do webhook](#adr-002--validação-de-assinatura-do-webhook)
  - [ADR-003 — Refresh token rotativo e revogável](#adr-003--refresh-token-rotativo-e-revogável)
  - [ADR-004 — Rate limit por IP + lockout por conta](#adr-004--rate-limit-por-ip--lockout-por-conta)
- [Deploy](#-deploy)
- [Licença](#-licença)
---

## ✨ Funcionalidades

**Loja (cliente)**
- Catálogo com paginação, busca, filtro por categoria, destaques, mais vendidos e descontos
- Página de detalhe do livro, galeria e avaliações (com estrelas)
- Carrinho persistido por usuário, wishlist e histórico de pedidos
- Checkout com endereços, seleção de frete real e aplicação de cupons
- Pagamento via **Mercado Pago** (Checkout Pro) com página de retorno `success` / `failure` / `pending`
- Comprovante do pedido em **PDF** e e-mail de confirmação

**Conta e segurança**
- Registro/login com **JWT**: access token curto (15 min) em memória + refresh token **rotativo** (7 dias) em cookie `HttpOnly` / `Secure` / `SameSite=Lax`, com `Path=/api/v1/auth`
- Refresh tokens **persistidos por hash (SHA-256)** e revogáveis: logout invalida o token apresentado; reuso de token já rotacionado revoga a **família inteira** (detecção de replay); troca de senha encerra todas as sessões
- Senhas com hash **Argon2id** (`pwdlib`), sem enumeração de e-mail no login nem no cadastro
- **Rate limit por IP** (slowapi) + **lockout por conta** com backoff exponencial em Redis (*fail-open* se o Redis cair)
- Cabeçalhos de segurança (CSP, HSTS, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`), remoção do header `Server`, CORS e `TrustedHost` com allowlist explícita
- Swagger/ReDoc/OpenAPI **desligados com `DEBUG=false`**; `SECRET_KEY` fraca e CORS com `*` abortam o startup em produção
- Soft delete de usuário, controle de papéis (`customer` / `admin`)

**Administração**
- Painel com métricas consolidadas (KPIs), gestão de pedidos, produtos, categorias, cupons, usuários e newsletter
- Controle de status de entrega/processamento dos pedidos

---

## 🧱 Stack

### Backend
| Camada | Tecnologia |
|---|---|
| Framework HTTP | **FastAPI** + Uvicorn |
| ORM / Migrations | **SQLAlchemy 2.0** + **Alembic** |
| Banco | **PostgreSQL 16** (`psycopg2`) |
| Validação / settings | **Pydantic v2** + `pydantic-settings` |
| Autenticação | `python-jose` (JWT) + `pwdlib[argon2]` |
| Fila / jobs assíncronos | **Celery** + **Redis** |
| PDF | **ReportLab** |
| Integrações | SDK **Mercado Pago**, **httpx** (Melhor Envio) |
| Rate limiting | **slowapi** (limite global + limites por rota) |
| Armazenamento de PDFs | **Supabase Storage** (bucket privado, via `httpx`) |
| Cabeçalhos de segurança | middleware ASGI próprio (`app/core/middleware.py`) |
| Lockout de login | **Redis** (contador por conta com backoff exponencial) |
| Qualidade | **pytest**, **ruff**, **black**, **mypy** (strict) |

### Frontend
| Item | Tecnologia |
|---|---|
| UI | **React 19** |
| Build / dev server | **Vite 8** |
| Estilo | **Tailwind CSS v4** (`@tailwindcss/vite`) |
| HTTP | **axios** (interceptor de refresh automático) |
| Formulários / validação | **react-hook-form** + **zod** |
| Roteamento | **react-router-dom v7** (rotas lazy + guard de admin) |
| Testes E2E | **Playwright** |
| Lint | **ESLint** |

### Infra / DevOps
- **GitHub Actions** — CI em 3 jobs: backend (lint + testes), frontend (lint + build) e E2E (Playwright com Postgres + Redis)
- **Docker Compose** — provisiona Postgres e Redis para o ambiente local
- **Render** — deploy do plano gratuito (ver [Deploy](#-deploy))

---

## 🏛️ Arquitetura

### Visão geral

```
┌──────────────────────────┐        HTTPS/JSON        ┌──────────────────────────────┐
│   SPA React + Vite       │  ───────────────────────▶ │        API FastAPI           │
│   (Papiro)               │  ◀─────────────────────── │   /api/v1 (routers REST)     │
│  axios + AuthContext     │   Bearer + cookie        │  Service → Repository → ORM   │
└──────────────────────────┘   httpOnly (refresh)     └───────────────┬──────────────┘
                                                                      │
                    ┌─────────────────────┬───────────────────┬───────┴───────────┐
                    ▼                     ▼                   ▼                   ▼
             ┌────────────┐        ┌────────────┐     ┌─────────────┐     ┌──────────────┐
             │ PostgreSQL │        │   Redis    │     │ Mercado Pago│     │ Melhor Envio │
             │  (dados)   │        │ (Celery)   │     │ (pagamento) │     │   (frete)    │
             └────────────┘        └─────┬──────┘     └─────────────┘     └──────────────┘
                                          │
                                   ┌──────▼───────┐
                                   │ Celery worker│  e-mail de confirmação + PDF
                                   └──────────────┘
```

### 📂 Estrutura de pastas

```
E-commerce v1/
├── backend/                      # API FastAPI
│   ├── app/
│   │   ├── main.py               # cria o FastAPI, CORS, Celery e registra o router
│   │   ├── api/
│   │   │   ├── deps.py           # dependências (get_db, get_current_user)
│   │   │   ├── limiter.py        # rate limit por IP (slowapi)
│   │   │   ├── exceptions.py     # hierarquia de exceções + handlers globais
│   │   │   ├── router.py         # agrega todos os routers em /api/v1
│   │   │   └── v1/               # routers por recurso (auth, products, orders, …)
│   │   ├── core/
│   │   │   ├── config.py         # Settings (pydantic-settings) + get_settings()
│   │   │   ├── middleware.py     # headers de segurança (CSP, HSTS, no-store)
│   │   │   └── security.py       # JWT (access/refresh), hash Argon2, cookie
│   │   ├── db/
│   │   │   ├── base.py           # Base declarativa (registry dos models)
│   │   │   ├── database.py       # engine + SessionLocal
│   │   │   └── transaction.py    # contexto de transação (begin / savepoint)
│   │   ├── models/               # tabelas SQLAlchemy (User, Product, Order, …)
│   │   ├── repositories/         # acesso a dados (uma por agregado)
│   │   ├── schemas/              # contratos Pydantic (request/response)
│   │   ├── services/             # regras de negócio (inclui order_state_machine,
│   │   │                         # pricing e login_lockout)
│   │   ├── integrations/
│   │   │   ├── MercadoPago/      # gateway de pagamento
│   │   │   └── MelhorEnvio/      # gateway de cotação de frete
│   │   └── utils/                # e-mail, PDF, tasks Celery e storage (Supabase)
│   ├── tests/                    # pytest: http_tests, service_tests, schemas_tests,
│   │                             # integration_tests (Postgres real)
│   ├── scripts/
│   │   ├── seed.py               # popula catálogo (idempotente; --reset)
│   │   └── e2e_server.py         # sobe a API apontando ao banco de teste E2E
│   ├── docker-compose.yml        # Postgres + Redis (+ serviços api/worker)
│   ├── Dockerfile                # imagem da API/worker (usada pelo compose)
│   ├── deploy.md                 # guia de deploy no Render (free)
│   ├── README_WEBHOOK_DECISION.md           # ADR-001 (decisão do webhook)
│   ├── README_WEBHOOK_SIGNATURE_DECISION.md # ADR-002 (assinatura do webhook)
│   ├── README.md                 # ponteiro para a documentação da raiz
│   ├── pyproject.toml            # deps, pytest, ruff, black, mypy
│   └── .env.example              # todas as variáveis de ambiente
│
├── frontend/Papiro/              # SPA React + Vite
│   ├── src/
│   │   ├── api/                  # client axios + um módulo por recurso
│   │   ├── components/           # componentes reutilizáveis
│   │   ├── context/              # AuthContext e CartContext
│   │   ├── pages/                # Home, Acervo, DetalheLivro, Checkout, Admin, …
│   │   ├── router/
│   │   │   ├── Rotas.jsx         # rotas (react-router-dom v7) + lazy + guard de admin
│   │   │   └── AppLayout.jsx     # moldura (Navbar + Footer) das páginas da loja
│   │   ├── App.jsx               # BrowserRouter → Rotas
│   │   └── main.jsx
│   ├── e2e/                      # specs, fixtures e helpers do Playwright
│   ├── playwright.config.js      # sobe backend E2E + Vite automaticamente
│   └── package.json
│
├── alembic/                      # migrations (na RAIZ do repositório)
├── alembic.ini                   # prepend_sys_path = backend
├── .github/workflows/ci.yml      # pipeline de CI
└── README.md
```

> ℹ️ As migrations ficam na **raiz** (`alembic/` + `alembic.ini`) porque o
> `env.py` importa a aplicação como `app.*` e o `prepend_sys_path` aponta para
> `backend`. Por isso os comandos do Alembic rodam a partir da raiz.

### Camadas do backend

O backend segue uma separação em camadas, do HTTP até o banco:

```
HTTP request
   │
   ▼
api/v1/*.py         Router   → valida entrada, injeta dependências (db, user)
   │
   ▼
services/*.py       Service  → regra de negócio, orquestra repositórios e gateways
   │
   ▼
repositories/*.py   Repo     → queries SQLAlchemy, isolamento de persistência
   │
   ▼
models/*.py         Model    → tabelas / relações
```

- **`schemas/`** definem os contratos de entrada/saída (Pydantic) e são reexportados
  por `app/schemas/__init__.py` para permitir `from app.schemas import X`.
- **`api/exceptions.py`** centraliza uma hierarquia (`BookCommerceException` e
  subclasses) convertida em respostas JSON padronizadas por handlers globais:
  ```json
  { "error": { "code": "EMAIL_ALREADY_EXISTS", "message": "…" } }
  ```
- **`integrations/`** isola os SDKs externos atrás de gateways, mantendo os
  services testáveis com mocks.

### Fluxo de compra e pagamento

```
1. Cliente monta o carrinho            POST /api/v1/cart/create + /cart/me
2. Cota o frete por CEP                POST /api/v1/shipping/quote
3. Cria o pedido (+ frete/cupom)       POST /api/v1/orders/create
4. Cria o checkout no Mercado Pago     POST /api/v1/payments/checkout/{order_id}
5. MP redireciona o cliente (back_urls success/failure/pending)
6. MP notifica o backend               POST /api/v1/payments/webhook
        ├─ valida `x-signature` (com suporte a secrets extras p/ rotação)
        ├─ 401 se a assinatura for inválida · 503/500 pedem reenvio ao MP
        └─ consulta o pagamento no MP → atualiza pedido → e-mail + PDF (Celery)
7. Cliente vê o retorno em /payment/{status}
8. Comprovante PDF vai para o bucket privado do Supabase Storage e é
   baixado por GET /api/v1/orders/{order_id}/comprovante
```

---

## 🚀 Como rodar

### Pré-requisitos
- **Python ≥ 3.11** · **Node.js ≥ 22** · **Docker** (para Postgres/Redis) · **Git**

### 1. Banco e Redis (Docker)

O `docker-compose.yml` sobe o Postgres (expondo a porta **5433** no host, para não
conflitar com um Postgres local) e o Redis (6379):

```bash
cd backend
cp .env.example .env        # edite os valores (ver abaixo)
docker compose up -d db redis
```

> ⚠️ Ajuste o `DATABASE_URL` do seu `.env` para o banco do compose:
> `postgresql+psycopg2://postgres:<senha>@localhost:5433/bookcommerce-db`
> (o `.env.example` aponta para `localhost:5432` por padrão).
> Os serviços `api` e `worker` também sobem pelo compose (`build: .`, usando o
> `backend/Dockerfile`) e herdam o `backend/.env`; nesse caso o `DATABASE_URL` é
> sobrescrito para apontar ao serviço `db` (porta interna 5432).
> O compose exige `POSTGRES_PASSWORD` definido no `.env` (não há default).

### 2. Backend

```bash
# a partir da raiz do repositório
python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash)  |  Linux/macOS: source venv/bin/activate
pip install -e "./backend[dev]"   # ou: cd backend && pip install -e ".[dev]"

# migrations (rodar da RAIZ — ver nota acima)
python -m alembic upgrade head

# catálogo de demonstração (idempotente)
cd backend
python -m scripts.seed            # use --reset para recriar

# sobe a API (http://localhost:8000 · docs em /docs)
uvicorn app.main:app --reload
```

Para os jobs de e-mail/PDF, suba um worker Celery em outro terminal:

```bash
cd backend
celery -A app.main.celery worker --loglevel=info
```

### 3. Frontend

```bash
cd frontend/Papiro
npm ci
cp .env.example .env              # VITE_API_URL aponta para a API
npm run dev                       # http://localhost:5173
```

Variável principal:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Variáveis de ambiente (principais)

Tabela resumida. A lista completa e comentada está em [`backend/.env.example`](backend/.env.example).

| Variável | Obrig. | Descrição |
|---|---|---|
| `DEBUG` | não (`false`) | Com `false` desliga `/docs`, `/redoc` e `/openapi.json` e mascara detalhes no `/health` |
| `DATABASE_URL` | sim | Conexão PostgreSQL (`postgresql+psycopg2://…`) |
| `SECRET_KEY` | sim | Assinatura dos JWT (≥ 32 chars, sem `change-me`); validada no startup em produção |
| `ALGORITHM` | não (`HS256`) | Algoritmo do JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | não (`15` / `7`) | TTL dos tokens |
| `COOKIE_SECURE` / `COOKIE_SAMESITE` / `COOKIE_DOMAIN` | não (`true` / `lax` / vazio) | Atributos do cookie de refresh |
| `FRONTEND_URL` / `BACKEND_URL` | sim | URLs usadas em CORS e nas `back_urls` do MP |
| `CORS_ORIGINS` | não | Lista JSON de origens; `*` aborta o startup em produção |
| `ALLOWED_HOSTS` | não | Hosts aceitos pelo `TrustedHostMiddleware` |
| `FORCE_HTTPS` | não (`false`) | Redireciona HTTP → HTTPS |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_DEFAULT` / `RATE_LIMIT_STORAGE_URI` | não | Rate limit por IP (slowapi); com mais de um worker use Redis em vez de `memory://` |
| `RATE_LIMIT_HEADERS_ENABLED` / `RATE_LIMIT_TRUST_XFF` | não (`false`) | Headers `X-RateLimit-*`; confiar em `X-Forwarded-For` só atrás de proxy confiável |
| `LOGIN_LOCKOUT_ENABLED` / `LOGIN_LOCKOUT_MAX_FAILURES` / `LOGIN_LOCKOUT_REDIS_URL` | não | Lockout por conta com backoff; sem URL própria herda o `CELERY_BROKER_URL` |
| `MERCADO_PAGO_ACCESS_TOKEN` / `MERCADO_PAGO_WEBHOOK_SECRET` | sim | Credenciais Mercado Pago |
| `MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA` | não | Secrets adicionais (vírgula) para rotação |
| `VALIDATE_WEBHOOK_SIGNATURE` | não (`true` no código) | `false` apenas na demo de portfólio — ver [ADR-002](#adr-002--validação-de-assinatura-do-webhook) |
| `MERCADO_PAGO_TIMEOUT` / `MELHOR_ENVIO_TIMEOUT` | não | Timeouts das integrações (segundos) |
| `MELHOR_ENVIO_API_TOKEN` / `MELHOR_ENVIO_ORIGIN_ZIP` / `MELHOR_ENVIO_SANDBOX` | não | Cotação de frete |
| `SMTP_*` | sim | Envio de e-mail de confirmação |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | sim | Redis do worker (e fallback do lockout) |
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` / `SUPABASE_STORAGE_BUCKET` | não | Storage privado dos PDFs; a `SERVICE_KEY` é `service_role` e só pode existir no backend |

---

## 🧪 Testes

### Backend (pytest)

```bash
cd backend
pytest                 # suíte padrão: sqlite em memória, sem serviços externos
pytest -m integration  # requer PostgreSQL real (ex.: bookcommerce_conc; ver docstring do teste)
```

- Os testes usam **SQLite em memória** e mocks — nenhum serviço externo é chamado.
- Organização: `http_tests/` (rotas), `service_tests/` (regras de negócio),
  `schemas_tests/` (validação Pydantic) e `integration_tests/` (concorrência com
  Postgres real, marcados com `@pytest.mark.integration`).
- Lint e tipos: `ruff check .`, `black .`, `mypy` (modo estrito).
- Testes de segurança e robustez: lockout (`test_login_lockout`), `/health` sem vazamento
  (`test_http_health`), transações (`test_transactions`) e índices (`test_indexes`).

### Frontend (Playwright E2E)

```bash
cd frontend/Papiro
npx playwright install --with-deps chromium
npm run e2e            # ou: npm run e2e:ui
```

O `playwright.config.js` sobe automaticamente o backend E2E (via
`backend/scripts/e2e_server.py`, apontando para o banco isolado
`bookcommerce-e2e`) e o dev server do Vite. Os specs cobrem home, catálogo,
registro/login, carrinho, wishlist, avaliações, endereço, cupom/checkout e
retorno de pagamento.

### CI

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda em push/PR
para `main`, `Frontend` e `Backend` (e também via `workflow_dispatch` manual),
com `concurrency` por ref sem cancelar runs em andamento:

1. **backend** — Python 3.13, `ruff check .` + `pytest` com `DEBUG=false`
   (reproduzindo produção, inclusive o `/health` mascarado)
2. **frontend** — Node 22, `eslint` + `vite build`
3. **e2e** — Playwright com serviços de Postgres 16 e Redis; aplica migrations,
   roda o seed e publica o relatório como artefato (só roda se 1 e 2 passarem)

---

## 🔌 Endpoints da API

Base: `/api/v1`. A documentação interativa (`/docs` Swagger e `/redoc`) só
existe com `DEBUG=true`; em produção a referência são os routers em
`backend/app/api/v1/`.

| Recurso | Prefixo | Exemplos |
|---|---|---|
| Health | `/health` | `GET /health/` — status da API + banco (`503` se o banco falhar) |
| Auth | `/auth` | `POST /register`, `/login`, `/refresh`, `/logout`, `GET /me` |
| Usuários | `/users` | `/create`, `/user_id/{id}`, `/update/{id}`, `/change_password/{id}/change-password`, `/delete/{id}` |
| Produtos | `/products` | `/paginated`, `/featured`, `/bestsellers`, `/recommendations`, `/category/{id}`, `/discount/{pct}` + CRUD |
| Categorias | `/categories` | `/list`, `/slug/{slug}`, `/name/{name}` + CRUD |
| Carrinho | `/cart` | `/cart/me`, `/{cart_id}/items/add`, `/update/{item_id}`, `/delete/{item_id}`, `/clear` |
| Pedidos | `/orders` | `/create`, `/list`, `/update/{id}`, `/{id}/comprovante`, `/send-confirmation-email` |
| Pagamentos | `/payments` | `/create`, `/get/{id}`, `/order/{id}`, `/history`, `/checkout/{order_id}`, `POST /webhook/` |
| Frete | `/shipping` | `POST /quote` (carrinho), `POST /calculate/{order_id}`, `POST /apply` |
| Endereços | `/addresses` | CRUD, `/default`, `/zip/{cep}` |
| Cupons | `/coupons` + `/user-coupons` | CRUD de cupons e resgate/atribuição por usuário |
| Wishlist | `/wishlists` | `/create`, `/list`, `/product/{id}`, `/delete/{id}` |
| Avaliações | `/reviews` | `/create`, `/product/{id}`, update e delete |
| Newsletter | `/newsletter` | `POST /subscribe`, `/unsubscribe`, `GET /list` (admin) |
| Admin | `/admin` | `/dashboard/stats`, `/orders`, `PATCH /orders/{id}/status`, `/users` |

---

## 🔐 Segurança

Resumo dos controles ativos — detalhes de exploração não são
documentados aqui de propósito.

### Controles implementados

| Área | Medidas |
|---|---|
| Transporte e cabeçalhos | HSTS (só em HTTPS), CSP restritiva na API, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, remoção do header `Server` |
| Sessão | JWT com `jti`/`type`/`iat`/`exp`, access token de 15 min em memória, refresh de 7 dias rotativo e revogável, cookie `HttpOnly`/`Secure`/`SameSite=Lax` |
| Senhas | Argon2id, mensagens de erro genéricas, sem enumeração de e-mail no login |
| Abuso | Rate limit por IP (slowapi) + lockout por conta com backoff exponencial |
| Superfície | `TrustedHost` com allowlist, CORS explícito (sem `*`), Swagger/OpenAPI desligados com `DEBUG=false`, `no-store` em `/auth` e `/payments` |
| Configuração | `SECRET_KEY` sem default funcional e validada no startup, `.env` fora do git, secrets de webhook com suporte a rotação |
| Pagamentos | Assinatura `x-signature` verificada (desligável só por env var), status consultado direto no MP, unicidade em `payments(provider, provider_payment_id)` |
| Integrações | Timeouts explícitos, tradução de erros do provedor (502/503/422) e TLS obrigatório no broker/backend do Celery |
| Dados | `/health` não expõe detalhes internos em produção, erros 500 genéricos, PDFs em bucket privado |

### Sessão e anti-abuso

- **Refresh token**: persistido com hash SHA-256, `jti`, `family_id` e `revoked`;
  rotacionado a cada `/auth/refresh`; replay de um token já revogado derruba a
  família (ADR-003). `logout` revoga o token apresentado; troca de senha revoga
  todos os tokens do usuário.
- **Cookie**: `papiro_refresh`, `HttpOnly` + `Secure` + `SameSite=Lax` +
  `Path=/api/v1/auth`; o access token fica apenas em memória no frontend.
- **Rate limit por IP** (`slowapi`): global `200/minute` e por rota — login e
  registro `10/minute`, refresh `30/minute`, newsletter `5/minute`, cotação de
  frete `30/minute`, webhook `120/minute` (ADR-004).
- **Lockout por conta**: chave do e-mail normalizada em SHA-256 (não guarda o
  e-mail no Redis), bloqueio após 5 falhas com backoff exponencial até 30 min,
  contador zerado em login bem-sucedido.

### Como foi verificado

- **Testes dedicados**: `test_login_lockout`, `test_http_health` (não vaza
  detalhes com `DEBUG=false`), `test_transactions`, `test_indexes`.
- **CI em modo produção**: o job de backend roda com `DEBUG=false`; o job E2E
  valida o fluxo de token em memória + cookie `httpOnly`.
- **Teste manual** dos headers de segurança e do bloqueio de `Host` inválido
  (`TrustedHostMiddleware` → `400`).

### Limites conhecidos

- O rate limit em `memory://` é por processo: com vários workers é preciso
  Redis (`RATE_LIMIT_STORAGE_URI`).
- O lockout de login é **fail-open** por desenho: sem Redis, não bloqueia.
- `VALIDATE_WEBHOOK_SIGNATURE=false` é aceitável **apenas** na demo (ver
  [ADR-002](#adr-002--validação-de-assinatura-do-webhook)).

### Reportar vulnerabilidades

Não abra issue pública para falhas de segurança. Envie um relatório privado ao
mantenedor (ou use *Security Advisories* do GitHub) com passos de reprodução e
impacto. Este é um projeto de portfólio: não deve ser usado com pagamentos
reais enquanto `VALIDATE_WEBHOOK_SIGNATURE=false`.

---

## 🧭 Decisões técnicas

**ADR-001** e **ADR-002** registam decisões **arquiteturais**, com alternativas
descartadas. **ADR-003** e **ADR-004** registam decisões de **implementação de
segurança** no mesmo formato, para preservar o histórico dos trade-offs — os
detalhes de implementação estão em [Segurança](#-segurança).

### ADR-001 — Webhook de pagamento via threadpool (não Celery)

> Versão completa da decisão: `backend/README_WEBHOOK_DECISION.md`.
> `backend/README_WEBHOOK_DECISION.md`.

**Contexto.** O endpoint `POST /api/v1/payments/webhook` é chamado pelo Mercado
Pago quando um pagamento muda de status. Seu trabalho real (consultar o Mercado
Pago, atualizar o pedido, disparar e-mail/comprovante) depende do SDK **síncrono**
do Mercado Pago, que é **HTTP bloqueante**.

**Problema.** O handler é `async def`. Rodar uma chamada de rede síncrona nele
bloquearia o **event loop** — o que, num processo uvicorn single-worker, congela
**todos** os endpoints enquanto o Mercado Pago não responder.

**Decisão.** O webhook executa o processamento em uma **thread** via
`starlette.concurrency.run_in_threadpool`, em vez de enfileirar uma task no
Celery.

```python
await run_in_threadpool(
    get_payment_service(db).process_webhook,
    str(payment_id),
    topic or None,
)
```

**Por que thread (e não Celery) aqui?**
- Este deploy é **plano free** (Render) e **não fica 24/7** (projeto de
  portfólio). Cada worker/processo dedicado custa RAM e horas; o objetivo é
  **leveza e simplicidade** com um único serviço.
- O processamento do webhook é **curto** (a chamada ao MP tem timeout de 8s no
  gateway). `run_in_threadpool` tira o bloqueio do event loop sem adicionar
  infraestrutura (broker, worker).

**E o Celery?** Celery/Redis **continuam no projeto** e seguem usados para os
jobs **pesados/assíncronos** — envio de e-mail de confirmação
(`send_order_confirmation_email`) e geração do comprovante PDF
(`generate_order_receipt`). A decisão é **específica do webhook**, cujo custo
não justifica um worker dedicado. Se no futuro houver fila/volume altos, basta
trocar `run_in_threadpool` por uma task Celery com `process_webhook` isolada.

**Consequências:**
- ✅ API única, sem worker obrigatório para o fluxo de pagamento; menos RAM e
  menos infraestrutura no plano free.
- ✅ O webhook responde **401** para assinatura inválida e **503/500** quando
  a dependência falha, pedindo reenvio ao provedor; erros de negócio
  definitivos não são reenviados.
- ⚠️ A validação de assinatura está **implementada**; na demo ela é desligada por env var (ver ADR-002).
- ⚠️ Se o volume crescer, o caminho de migração é isolar `process_webhook` numa
  task Celery.

---

### ADR-002 — Validação de assinatura do webhook

> Implementação em `app/api/v1/payments.py`. O histórico da decisão original
> (quando a validação foi desligada) está em
> `backend/README_WEBHOOK_SIGNATURE_DECISION.md`.

**Contexto.** O Mercado Pago envia `x-signature` e `x-request-id`, e a assinatura
é calculada com o `data.id` e um secret da aplicação. A primeira versão do
projeto não validava a assinatura (decisão de portfólio) e a documentação dizia
que o validador “ainda existia, mas não era usado”.

**Decisão (estado atual).** A validação está **implementada e ligada por
omissão** (`VALIDATE_WEBHOOK_SIGNATURE=True` no código):

- tenta validar com `MERCADO_PAGO_WEBHOOK_SECRET` e com os secrets extras de
  `MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA` (rotação sem downtime);
- assinatura inválida → **401**, sem processar nada;
- a rejeição é logada com motivo, `request_id` e idade do timestamp (ajuda a
  diagnosticar reenvios antigos da fila do MP).

**Exceção consciente da demo.** No ambiente de portfólio a variável fica
`VALIDATE_WEBHOOK_SIGNATURE=false` porque a assinatura não conferia no sandbox.
A rejeição é logada e o fluxo segue.

**Mitigação.** Mesmo com a validação desligada não é possível “aprovar
pagamento fake”: o webhook usa `data.id` apenas como gatilho e **consulta o
pagamento direto na API do Mercado Pago** (`gateway.get_payment`) para obter
status e valor reais. Um id forjado apenas provoca uma consulta a um pagamento
inexistente.

**Consequências:**
- ✅ Implementação pronta para produção; reativar é só configurar a env var.
- ⚠️ Com a validação desligada, um atacante pode forjar callbacks e consumir
  quota da API do MP, além de disparar processamento.
- ⚠️ Risco de esquecer a variável no deploy. O default do **código** é `true`
  (seguro); o `false` existe apenas no `.env.example` e no painel da demo.

**Como reativar:** corrigir o secret no painel do MP, definir
`VALIDATE_WEBHOOK_SIGNATURE=true`, garantir que o `notification_url` aponta para
`/api/v1/payments/webhook/` e validar com uma notificação real.

---

### ADR-003 — Refresh token rotativo e revogável

**Contexto.** JWT é *stateless*: sem estado no servidor um refresh token roubado
continua válido até expirar e o logout não invalida nada.

**Decisão.** Abrir mão do stateless **só** para o refresh token: cada token é
persistido (hash SHA-256) com `jti`, `family_id` e `revoked`, rotacionado a cada
`/auth/refresh`; reapresentar um token já revogado revoga a família inteira.
O access token continua stateless (15 min).

**Consequências:**
- ✅ Logout e troca de senha têm efeito real; roubo de refresh é detectável.
- ⚠️ Exige a migration `79e7e5c655ad_add_refresh_tokens` e limpeza de expirados.
- ⚠️ Duas abas em corrida podem derrubar a sessão (intencional).

---

### ADR-004 — Rate limit por IP + lockout por conta

**Contexto.** Rate limit por IP sozinho não trava credential stuffing
distribuído (um IP por tentativa), e ser agressivo por IP penaliza NAT/CGNAT.

**Decisão.** Duas camadas: limite por IP (`slowapi`) e lockout por conta com
backoff exponencial até 30 min. O lockout é **fail-open** — prioriza
disponibilidade sobre anti-abuso quando o Redis cai. Limites por rota e
variáveis estão em [Segurança](#-segurança) e no `.env.example`.

**Consequências:**
- ✅ Cobre ataque de um único IP e distribuído, sem confiar em `X-Forwarded-For`.
- ⚠️ Em `memory://` o limite é por processo: vários workers exigem Redis.
- ⚠️ Sem Redis o lockout não atua (decisão consciente).

---

## 📦 Deploy

O passo a passo detalhado é mantido localmente em `backend/deploy.md`
(Render, plano free). Resumo:
1. **PostgreSQL** (free) → pegue a *Internal Database URL*.
2. **Web Service** (free) — Root Directory `backend`,
   Build `pip install .`, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. **(Opcional)** **Key Value (Redis)** + **Background Worker**
   (`celery -A app.main.celery worker --loglevel=info`) — só se quiser e-mail/PDF.
4. Defina `DEBUG=false`, `SECRET_KEY` forte, `CORS_ORIGINS`/`ALLOWED_HOSTS` com os
   domínios reais e `VALIDATE_WEBHOOK_SIGNATURE=false` apenas na demo (ADR-002).
   Com `DEBUG=false` a aplicação **não sobe** se a `SECRET_KEY` for fraca ou se
   `CORS_ORIGINS` contiver `*`.
5. **Pre-Deploy Command:** `alembic upgrade head`.
6. Health check: `/api/v1/health/` (a raiz `/` responde `204` em produção).
7. Configure o Mercado Pago com `notification_url` apontando para
   `https://<seu-web-service>.onrender.com/api/v1/payments/webhook/`.

> ℹ️ No plano free o serviço hiberna após ~15 min sem tráfego (cold start de ~1 min)
> e o Postgres free expira em 30 dias — suficiente para demonstração, mas exige
> recriar/`pg_dump` periodicamente.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja `pyproject.toml` (`license = { text = "MIT" }`).
