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

- 🛍️ **Frontend:** <https://e-commerce.matheuslab.xyz>
- ⚙️ **API:** <https://api-e-commerce.matheuslab.xyz> · docs interativas em `/docs`

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
- [Decisões de arquitetura (ADRs)](#-decisões-de-arquitetura-adrs)
  - [ADR-001 — Webhook de pagamento via threadpool (não Celery)](#adr-001--webhook-de-pagamento-via-threadpool-não-celery)
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
- Registro/login com **JWT**: access token curto em memória + refresh token **rotativo** em cookie `httpOnly`
- Senhas com hash **Argon2** (`pwdlib`)
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
| Qualidade | **pytest**, **ruff**, **black**, **mypy** (strict) |

### Frontend
| Item | Tecnologia |
|---|---|
| UI | **React 19** |
| Build / dev server | **Vite 8** |
| Estilo | **Tailwind CSS v4** (`@tailwindcss/vite`) |
| HTTP | **axios** (interceptor de refresh automático) |
| Formulários / validação | **react-hook-form** + **zod** |
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
│   │   │   ├── exceptions.py     # hierarquia de exceções + handlers globais
│   │   │   ├── router.py         # agrega todos os routers em /api/v1
│   │   │   └── v1/               # routers por recurso (auth, products, orders, …)
│   │   ├── core/
│   │   │   ├── config.py         # Settings (pydantic-settings) + get_settings()
│   │   │   └── security.py       # JWT (access/refresh), hash Argon2, cookie
│   │   ├── db/
│   │   │   ├── base.py           # Base declarativa (registry dos models)
│   │   │   └── database.py       # engine + SessionLocal
│   │   ├── models/               # tabelas SQLAlchemy (User, Product, Order, …)
│   │   ├── repositories/         # acesso a dados (uma por agregado)
│   │   ├── schemas/              # contratos Pydantic (request/response)
│   │   ├── services/             # regras de negócio (uma por domínio)
│   │   ├── integrations/
│   │   │   ├── MercadoPago/      # gateway de pagamento
│   │   │   └── MelhorEnvio/      # gateway de cotação de frete
│   │   └── utils/                # e-mail (Celery), PDF e tasks de comprovante
│   ├── tests/                    # pytest: http_tests, service_tests, schemas_tests,
│   │                             # integration_tests (Postgres real)
│   ├── scripts/
│   │   ├── seed.py               # popula catálogo (idempotente; --reset)
│   │   └── e2e_server.py         # sobe a API apontando ao banco de teste E2E
│   ├── docker-compose.yml        # Postgres + Redis (+ serviços api/worker)
│   ├── deploy.md                 # guia de deploy no Render (free)
│   ├── pyproject.toml            # deps, pytest, ruff, black, mypy
│   └── .env.example              # todas as variáveis de ambiente
│
├── frontend/Papiro/              # SPA React + Vite
│   ├── src/
│   │   ├── api/                  # client axios + um módulo por recurso
│   │   ├── components/           # componentes reutilizáveis
│   │   ├── context/              # AuthContext e CartContext
│   │   ├── pages/                # Home, Acervo, DetalheLivro, Checkout, Admin, …
│   │   ├── App.jsx               # navegação entre páginas (sem router dedicado)
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
1. Cliente monta o carrinho            POST /api/v1/cart/...
2. Cota o frete por CEP                POST /api/v1/shipping/quote
3. Cria o pedido (+ frete/cupom)       POST /api/v1/orders
4. Cria o checkout no Mercado Pago     POST /api/v1/payments/checkout/{order_id}
5. MP redireciona o cliente (back_urls success/failure/pending)
6. MP notifica o backend               POST /api/v1/payments/webhook
        └─ valida assinatura → atualiza o pedido → dispara e-mail + PDF (Celery)
7. Cliente vê o retorno em /payment/{status}
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
> `postgresql+psycopg2://bookcommerce:<senha>@localhost:5433/bookcommerce-db`
> (o `.env.example` aponta para `localhost:5432` por padrão).
> Os serviços `api` e `worker` também estão declarados no compose para cenários
> com imagem construída; para o dia a dia, rode a API e o worker localmente.

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

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | Conexão PostgreSQL (`postgresql+psycopg2://…`) |
| `SECRET_KEY` | Chave de assinatura dos JWT (≥ 32 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | TTL dos tokens |
| `FRONTEND_URL` / `BACKEND_URL` | URLs usadas em CORS e `back_urls` do MP |
| `MERCADO_PAGO_ACCESS_TOKEN` / `MERCADO_PAGO_WEBHOOK_SECRET` | Credenciais Mercado Pago |
| `VALIDATE_WEBHOOK_SIGNATURE` | `true` em produção (ver ADR-001) |
| `MELHOR_ENVIO_API_TOKEN` / `MELHOR_ENVIO_ORIGIN_ZIP` / `MELHOR_ENVIO_SANDBOX` | Cotação de frete |
| `SMTP_*` | Envio de e-mail de confirmação |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis para o worker |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_DEFAULT` / `RATE_LIMIT_STORAGE_URI` | Rate limiting por IP (slowapi). Com multi-worker use `RATE_LIMIT_STORAGE_URI=redis://…`; desligue em testes |

A lista completa, comentada, está em [`backend/.env.example`](backend/.env.example).

---

## 🧪 Testes

### Backend (pytest)

```bash
cd backend
pytest                 # suíte padrão: sqlite em memória, sem serviços externos
pytest -m integration  # requer um PostgreSQL real (bookcommerce_conc)
```

- Os testes usam **SQLite em memória** e mocks — nenhum serviço externo é chamado.
- Organização: `http_tests/` (rotas), `service_tests/` (regras de negócio),
  `schemas_tests/` (validação Pydantic) e `integration_tests/` (concorrência com
  Postgres real, marcados com `@pytest.mark.integration`).
- Lint e tipos: `ruff check .`, `black .`, `mypy` (modo estrito).

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
para `main` e `Frontend`:

1. **backend** — `ruff` + `pytest`
2. **frontend** — `eslint` + `vite build`
3. **e2e** — Playwright com serviços de Postgres e Redis (só roda se 1 e 2 passarem)

---

## 🔌 Endpoints da API

Base: `/api/v1` — documentação interativa completa em **`/docs`** (Swagger) e
**`/redoc`**.

| Recurso | Prefixo | Exemplos |
|---|---|---|
| Health | `/health` | `GET /health` |
| Auth | `/auth` | `POST /register`, `/login`, `/refresh`, `/logout`, `GET /me` |
| Usuários | `/users` | CRUD, troca de senha, soft delete |
| Produtos | `/products` | catálogo paginado, destaques, mais vendidos, por categoria/desconto |
| Categorias | `/categories` | CRUD |
| Carrinho | `/cart` | adicionar/atualizar/remover itens, esvaziar |
| Pedidos | `/orders` | criar, listar, atualizar, comprovante PDF |
| Pagamentos | `/payments` | `checkout/{order_id}`, `GET /history`, `POST /webhook` |
| Frete | `/shipping` | `POST /quote` (carrinho), cotação/aplicação por pedido |
| Endereços | `/addresses` | CRUD, endereço padrão, busca por CEP |
| Cupons | `/coupons` + `/user-coupons` | CRUD e resgate por usuário |
| Wishlist | `/wishlists` | adicionar/listar/remover |
| Avaliações | `/reviews` | CRUD por produto/usuário |
| Newsletter | `/newsletter` | inscrição pública + listagem (admin) |
| Admin | `/admin` | métricas (KPIs), pedidos, usuários |

---

## 🧭 Decisões de arquitetura (ADRs)

### ADR-001 — Webhook de pagamento via threadpool (não Celery)

> A versão completa deste ADR também é mantida localmente em
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
- ✅ Webhook responde **200** mesmo em falha de processamento (o MP reenvia por
  15 min em caso de 5xx); o erro vai para o log para investigação.
- ⚠️ A validação de assinatura (`VALIDATE_WEBHOOK_SIGNATURE`) é desativável em
  sandbox — em produção **mantenha `true`**.
- ⚠️ Se o volume crescer, o caminho de migração é isolar `process_webhook` numa
  task Celery.

---

## 📦 Deploy

O passo a passo detalhado é mantido localmente em `backend/deploy.md`
(Render, plano free). Resumo:
1. **PostgreSQL** (free) → pegue a *Internal Database URL*.
2. **Web Service** (free) — Root Directory `backend`,
   Build `pip install .`, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. **(Opcional)** **Key Value (Redis)** + **Background Worker**
   (`celery -A app.main.celery worker --loglevel=info`) — só se quiser e-mail/PDF.
4. Configure o Mercado Pago com `notification_url` apontando para
   `https://<seu-web-service>.onrender.com/api/v1/payments/webhook/`.

> ℹ️ No plano free o serviço hiberna após ~15 min sem tráfego (cold start de ~1 min)
> e o Postgres free expira em 30 dias — suficiente para demonstração, mas exige
> recriar/`pg_dump` periodicamente.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja `pyproject.toml` (`license = { text = "MIT" }`).
