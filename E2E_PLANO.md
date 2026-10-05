# Plano — Testes E2E (Playwright) — E-commerce "Papiro"

> Documento de trabalho para implementação dos testes **E2E** com **Playwright**.
> Escrito para ser executado por um modelo menor: cada passo é explícito, com
> comandos copiáveis e critérios de "pronto".
>
> Última atualização: **levantamento + Fase 0 + Fase 1 + Fase 2 (data-testid)**.

---

## 0. Contexto (leia antes de começar)

- **Raiz do repo:** `C:/Users/mathe/OneDrive/Desktop/E-commerce v1`
- **Backend:** FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL. Raiz `backend/`, app `backend/app/`.
- **Frontend:** React 19 + Vite 8 + Tailwind v4 + axios. Raiz `frontend/Papiro/`, código `frontend/Papiro/src/`.
- **Venv Python:** `./venv/Scripts/` (na raiz do repo). Python 3.13.2.
- **Node:** v22 (`node --version`). npm/npx disponíveis.
- **DB de dev:** `postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce-db` (usuário/senha em `backend/.env`)
- **DB de teste E2E:** `postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce-e2e`
- **API local:** `http://localhost:8000/api/v1`
- **Frontend local:** `http://localhost:5173`

### Regras de trabalho do usuário
- Implementar **parte por parte**; apresentar levantamento/plano **antes** de tocar em código.
- **Atualizar o `HANDOFF.md`** ao final de cada task concluída.

---

## 1. Decisões travadas

| Decisão | Valor | Motivo |
|---|---|---|
| Ferramenta | **Playwright** (`@playwright/test`) | Melhor suporte a React/Vite, retry, trace, interceptação de rede |
| Banco de dados | **Isolado** `bookcommerce-e2e` | Não suja dados de dev/prod |
| `/admin/*` sem auth | **BUG — fora de escopo** | Rotas `/admin/*` não exigem Bearer/role; não testar até corrigir |
| Backend no E2E | **Playwright sobe automaticamente** | `webServer` do Playwright |
| Mercado Pago | **Sempre mockado** via `page.route` | Nunca chamar MP real |

---

## 2. Achados críticos do levantamento

1. **Frontend NÃO tem roteador.** `frontend/Papiro/src/App.jsx` alterna páginas por `useState('home')` + uma **nav flutuante fixa** com botões para:
   `['home','acervo','detalhe','carrinho','checkout','minhaconta','login','registro','admin']`.
   Único path real lido: `/payment/{success|failure|pending}` (retorno do MP).
   → **E2E navega clicando na nav**, não por URL.

2. **`VITE_API_URL` default é o túnel `https://api-e-commerce.matheuslab.xyz`**
   (`src/api/client.js:34`: `import.meta.env.VITE_API_URL ?? 'https://.../api/v1'`).
   Esse host é um **túnel para o backend local (porta 8000)** — hoje não é uma
   API remota de produção, mas o E2E **não pode depender dele**: (a) o backend
   por trás do túnel usa o `.env` com o **banco de DEV** (`bookcommerce-db`),
   não o isolado `bookcommerce-e2e`; (b) dependência de rede externa/latência.
   → O dev server **precisa** receber `VITE_API_URL=http://localhost:8000/api/v1`.

3. **Zero `data-testid`** no front (confirmado por grep). → Fase 2 é obrigatória.

4. **`/admin/*` não tem autenticação** (`backend/app/api/v1/admin.py` não importa/usa `get_current_user`). **Bug de segurança** — E2E de admin fica fora de escopo.

5. **Criar admin exige admin** (`UserService._ensure_admin`). Não dá para criar admin pela API pública → precisa de `seed_e2e.py` (inserção direta no banco).

6. **`scripts/seed.py` estava desatualizado** (faltavam imports de `newsletter`, `payment`, `user_coupon`) → quebrava com `InvalidRequestError: ...failed to locate a name ('UserCoupon')`. **CORRIGIDO** na Fase 0.

7. **Alembic lê `DATABASE_URL` do `.env`** via `get_settings()` (`alembic/env.py`). Para o DB de teste, **exportar `DATABASE_URL` no ambiente** (env tem precedência sobre `.env`).

8. **`get_settings()` é `@lru_cache`.** O env precisa ser setado **antes** do primeiro import de `app.core.config`. Por isso o backend E2E sobe via script wrapper.

9. **CORS já cobre** `localhost:5173` e `:4173` (`app/main.py`). Nada a fazer.

10. **Login é form-urlencoded** (`POST /auth/login`, campo `username`=email), NÃO JSON. Token JWT em `localStorage`, chave `papiro.token`.

---

## 3. Estrutura de arquivos a criar

```
frontend/Papiro/
├── playwright.config.js          # config: webServer(backend + vite), projects
├── e2e/
│   ├── fixtures/
│   │   ├── base.js               # test estendido: helpers navegar/login
│   │   └── api-client.js         # chamadas diretas à API p/ setup/teardown
│   ├── helpers/
│   │   ├── navegar.js            # cliques na nav por testid
│   │   └── auth.js               # login via UI ou injeção de token
│   └── specs/
│       ├── 01-home.spec.js
│       ├── 02-acervo-detalhe.spec.js
│       ├── 03-registro-login.spec.js
│       ├── 04-carrinho.spec.js
│       ├── 05-wishlist.spec.js
│       ├── 06-review.spec.js
│       ├── 07-endereco.spec.js
│       ├── 08-cupom-checkout.spec.js
│       └── 09-retorno-pagamento.spec.js
└── .env.e2e                      # VITE_API_URL local (NÃO usar default de prod)

backend/
└── scripts/
    ├── seed_e2e.py               # cria usuário cliente + fixtures (idempotente)
    └── e2e_server.py             # sobe uvicorn apontando p/ bookcommerce-e2e
```

---

## 4. Fases — passo a passo

### ✅ FASE 0 — Provisionamento (CONCLUÍDA)

- [x] DB `bookcommerce-e2e` criado no Postgres (`docker exec bookcommerce-db psql -U postgres -c 'CREATE DATABASE "bookcommerce-e2e";'`).
- [x] Migrations aplicadas:
  ```bash
  cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1"
  DATABASE_URL="postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce-e2e" ./venv/Scripts/alembic.exe upgrade head
  ```
- [x] Seed rodado (4 categorias, 24 produtos):
  ```bash
  cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1/backend"
  DATABASE_URL="postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce-e2e" ../venv/Scripts/python.exe -m scripts.seed
  ```
- [x] **Bug corrigido:** `backend/scripts/seed.py` agora importa `app.models.newsletter`, `app.models.payment` e `app.models.user_coupon`.

**Critério de pronto:** `SELECT count(*) FROM products;` no DB de teste retorna 24.

---

### ✅ FASE 1 — Instalação e config do Playwright (CONCLUÍDA)

**O que foi feito:**

1. ✅ Instalado `@playwright/test` + Chromium no frontend:
   ```bash
   cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1/frontend/Papiro"
   npm i -D @playwright/test
   npx playwright install chromium
   ```
2. ✅ Criado `backend/scripts/e2e_server.py` — sobe uvicorn com `DATABASE_URL`
   de teste **antes** do primeiro import do app (respeita o `lru_cache` do
   `get_settings`); autolocaliza `backend/` no `sys.path` (roda de qualquer cwd);
   aceita `--port N` (default 8000; o E2E usa 8001).
3. ✅ Criado `frontend/Papiro/playwright.config.js`:
   - `testDir: './e2e/specs'`; `baseURL: 'http://localhost:5173'`
   - `webServer` **array com 2 entradas**:
     - Backend: `cd ..\\..\\backend && ..\\venv\\Scripts\\python.exe scripts\\e2e_server.py --port 8001`,
       `url: 'http://localhost:8001/'`, `reuseExistingServer: false`.
     - Vite: `command: 'npm run dev'`, `env: { VITE_API_URL: 'http://localhost:8001/api/v1' }`,
       `url: 'http://localhost:5173'`, `reuseExistingServer: !process.env.CI`.
   - `trace: 'on-first-retry'`, `retries: process.env.CI ? 2 : 0`.
4. ✅ Criado `frontend/Papiro/.env.e2e` (`VITE_API_URL=http://localhost:8001/api/v1`;
   uso manual: `npm run dev -- --mode e2e`).
5. ✅ Scripts no `frontend/Papiro/package.json`: `"e2e": "playwright test"`
   e `"e2e:ui": "playwright test --ui"`.

> **Nota de contexto (porta):** durante a implementação a 8000 estava ocupada
> pelo backend de dev; o E2E rodou temporariamente em **8001**. Com a 8000
> livre, o config foi **revertido para 8000** (default do `e2e_server.py`).

**Critério de pronto (validado):** `npx playwright test --list` lista
**0 testes sem erro de config**; um smoke temporário passou com os 2 servidores
subindo via `webServer` (backend na 8001 com DB de teste + Vite local; home
renderizou "Dom Casmurro" vindo da API de teste). Smoke removido após validação
(a Fase 3 cria os specs).

---

### ✅ FASE 2 — Instrumentação (`data-testid`) (CONCLUÍDA)

**Testids adicionados (sem quebrar `id`/`aria` existentes):**

| Local | testid |
|---|---|
| Nav flutuante (`App.jsx`) | `nav-home`, `nav-acervo`, `nav-detalhe`, `nav-carrinho`, `nav-checkout`, `nav-minhaconta`, `nav-login`, `nav-registro`, `nav-admin` (via `` `nav-${nome}` ``) |
| Navbar | `navbar-sacola` (botão sacola), `navbar-login` (botão de conta/entrar) |
| `BookCard.jsx` | `book-card-{id}` (no `<article>`) |
| `PainelCompra.jsx` | `btn-add-carrinho`, `btn-wishlist` |
| Form login | `input-email`, `input-password`, `btn-entrar` |
| Form registro | `input-full-name`, `input-email`, `input-password`, `input-confirmacao`, `btn-registrar` |
| `ItemCarrinho.jsx` / `Quantidade.jsx` | `cart-item-{id}`, `btn-qtd-mais`, `btn-qtd-menos`, `btn-remover` |
| Checkout | `btn-finalizar` (submit "Concluir compra") |
| `SecaoCupons.jsx` | `cupom-item-{id}` (clique = aplicar), `btn-remover-cupom` |
| `SeletorEndereco.jsx` | `btn-novo-endereco` (modal novo) |
| Form review (submit) | `btn-criar-review` |

> **Divergência do plano:** `btn-aplicar-cupom` não existe no UI real — o checkout
> aplica cupom clicando no card do cupom (`SecaoCupons`). Substituído por
> `` `cupom-item-${cupom.id}` `` (o teste da Fase 4 clica no card).

**Critério de pronto (validado):** grep em `src/` encontra todos os testids
acima; `npm run build` continua passando (1.9s).

**Lint (corrigido após a Fase 2):** havia 2 erros **pré-existentes** —
`DetalhesLivro.jsx` (`autenticado` unused; removido do destructure — o form já
é controlado por `comprou`) e `DetalheLivro.jsx` (`set-state-in-effect` no
effect de "comprou"; guard clause refatorada para reset via `.catch`).
`npx eslint src/` agora passa limpo. `.gitignore` do frontend ganhou
`test-results/`, `playwright-report/`, `playwright/.cache`.

---

### ✅ FASE 3 — Testes core (CONCLUÍDA)

Criados e passando com `npm run e2e` (6 testes / 2 runs consecutivas ~17s):

1. ✅ **01-home.spec.js** — home carrega; navbar + nav flutuante visíveis;
   renderiza "Dom Casmurro" vindo da API local (prova banco de teste, não
   o de dev).
2. ✅ **02-acervo-detalhe.spec.js** — `nav-acervo` → primeiro `book-card-{id}`
   → clique na capa → detalhe com H1 (título) + `btn-add-carrinho` + preço.
3. ✅ **03-registro-login.spec.js** — registra usuário único (timestamp) → login
   automático (token em `localStorage['papiro.token']`) → **reload** restaura
   sessão (aria-label da conta + dados da home); 2º teste: logout + login via
   form com credenciais existentes.
4. ✅ **04-carrinho.spec.js** (2 testes) — (a) visitante: add detalhe → badge `1` →
   carrinho → `btn-qtd-mais`/`btn-qtd-menos` (badge 2↔1) → `btn-remover` →
   sacola vazia e badge some. (b) **logado: carrinho persiste no backend** —
   registra usuário novo (exercita o handshake `No cart found` → cria carrinho),
   add 1 livro, `reload` → badge `1` e item (com título) recarregado da API.
5. ✅ **09-retorno-pagamento.spec.js** — `page.goto('/payment/success')` → tela
   de retorno renderiza sem login (H1 tema + "Voltar para a loja" + selo MP).

Notas/descobertas:
- **`App.jsx` oculta Navbar e nav flutuante na tela de retorno** (`!retornoPagamento`)
  — o spec 09 não pode assertar navbar; a independência de auth é a própria
  renderização sem login.
- **Log do backend: `No cart found` CORRIGIDO (Parte 15).** `cart.py` ganhou
  `_traduzir_value_error` (padrão de products/addresses/orders): `GET /cart/me`
  de usuário sem carrinho agora responde **404 CART_NOT_FOUND** (warning no log)
  em vez de 500 + traceback. Teste novo em `test_http_cart.py` +
  suíte completa 608 passed. O handshake do front continua idêntico (catch
  incondicional → cria carrinho).
- Usuários `e2e_*@exemplo.com` acumulam no DB de teste entre runs (email único
  por execução evita colisão; limpeza via API no teardown fica para a Fase 4).
- **Atenção por contrato:** no carrinho vindo da API, `item.id` é o id da
  **linha** do carrinho (não o product_id) — `cart-item-{id}` logado não casa
  com o id do card; assertar pelo **título**. (No carrinho de visitante, em
  memória, o id É o product_id.)

**Critério de pronto (validado):** os 5 specs passam localmente com `npm run e2e`
(7 testes — 04 tem 2: visitante + logado/persistente) — rodado 2x seguidas sem quakes.

---

### ✅ FASE 4 — Testes secundários (CONCLUÍDA)

6. ✅ **05-wishlist.spec.js** — logar → detalhe → `btn-wishlist` (vira "Remover dos
   desejos") → Minha Conta → aba "Lista de desejos" → livro presente.
7. ✅ **06-review.spec.js** — setup via API (endereço + pedido — a UI exige
   `comprou` para mostrar o form) → detalhe → seção Avaliações → nota 4 +
   comentário → `btn-criar-review` → editar (nota 3 + novo comentário) → salvar.
8. ✅ **07-endereco.spec.js** — checkout → `btn-novo-endereco` → modal: CEP com
   **ViaCEP mockado** (`page.route`) → auto-preenchimento → salvar → endereço
   no seletor e na aba Endereços de Minha Conta.
9. ✅ **08-cupom-checkout.spec.js** — logar → endereço via API → item na sacola
   → checkout → seleciona endereço → finaliza com **MP 100% mockado**:
   `page.route` intercepta `POST /api/v1/payments/checkout/*` (o backend NEM
   chama o SDK) e `https://sandbox.mercadopago.com.br/**` (redirect) → pedido
   real criado (`orderId` capturado via `page.on('response')`).

**Critério de pronto (validado):** 11 testes passam (3 runs consecutivas ~24–26s);
nenhuma chamada real ao MP — 2 `page.route` cobrem checkout do backend + site.

**Ajustes/descobertas da Fase 4:**
- **Pool do SQLAlchemy saturava em paralelo**: engine sem `pool_size` (padrão
  5 + overflow 10); 11 workers → "Carregando títulos…" eterno. Fix:
  `workers: 3` no `playwright.config.js` (CI: 2).
- **`DetalhesLivro` remonta ao recarregar** (`carregar()` seta `carregando`),
  resetando a seção retrátil para fechada → reabrir condicionalmente antes de
  editar a review (`aria-expanded`).
- **`sessionStorage` é por origem** — após o redirect ao sandbox do MP, o
  storage de 5173 fica inacessível; `orderId` capturado via `page.on('response')`.
- Segunda execução da suíte: `request` do setup vira mais 404/409 legítimos no
  log (addresses/orders criados via API são o ponto).

---

### ✅ FASE 5 — Documentação (CONCLUÍDA)

- ✅ Seção **"Testes E2E (Playwright) — como rodar"** adicionada ao
  `HANDOFF.md`: pré-requisitos (Docker/Postgres, DB de teste provisionado com
  migrations + seed, Playwright + Chromium, porta 8000 livre), comandos
  (`npm run e2e`, `e2e:ui`, 1 arquivo), cobertura (11 testes), **limpeza de
  dados** (ordem reversa das FKs — sem `ON DELETE CASCADE` no schema) e notas
  operacionais (workers 3, `CART_NOT_FOUND` normal, MP nunca chamado).
- ✅ `frontend/Papiro/README.md` reescrito (era o template default do Vite):
  scripts dev/build/lint/e2e, seção completa de E2E apontando para o HANDOFF,
  estrutura do `src/`.

**Critério de pronto (validado):** um novo dev consegue rodar o E2E seguindo só
os passos do HANDOFF (todos os comandos documentados foram usados nas Fases
0–4; a limpeza respeita o schema real das FKs).

---

## 5. Fora de escopo (explícito)

- **`/admin/*`** — bloqueado até corrigir a falta de auth (bug registrado).
- **Pagamento real** — nunca chamar o MP real.
- **Deploy/staging** — fase posterior; a suíte será reaproveitada com outro `baseURL`.
- **Correção do roteador do front** — não vamos adicionar react-router agora; a nav por clique é o que existe.

---

## 6. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Sem roteador → seletores frágeis | `data-testid` na nav e ações (Fase 2) |
| `VITE_API_URL` default = túnel (banco de dev) | `webServer` força env local (`bookcommerce-e2e`) |
| Backend já rodando em modo dev/prod | `e2e_server.py` usa DB de teste; `reuseExistingServer: false` no backend |
| Colisão de dados entre specs | usuários únicos por run (timestamp) + limpeza via API no teardown |
| MP externo | `page.route` mock |
| `get_settings()` cacheado | exportar `DATABASE_URL` **antes** de importar app (script wrapper) |

---

## 7. Comandos de referência

```bash
# --- Provisionar/recriar DB de teste (idempotente) ---
cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1"
docker exec bookcommerce-db psql -U postgres -c 'CREATE DATABASE "bookcommerce-e2e";'   # só na 1ª vez
DATABASE_URL="postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce-e2e" ./venv/Scripts/alembic.exe upgrade head
cd backend
DATABASE_URL="postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce-e2e" ../venv/Scripts/python.exe -m scripts.seed

# --- Rodar E2E ---
cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1/frontend/Papiro"
npm run e2e
npm run e2e:ui
```

---

## 8. Registro de progresso

| Fase | Estado | Observação |
|---|---|---|
| 0 — Provisionamento | ✅ Concluída | DB `bookcommerce-e2e` + migrations + seed (24 produtos). Bug do `seed.py` corrigido. |
| 1 — Playwright config | ✅ Concluída | Backend E2E na **porta 8000** . Playwright + Chromium instalados; `e2e_server.py`; `playwright.config.js` (webServer x2); scripts `e2e`/`e2e:ui`; `.env.e2e`. Smoke validado; `--list` = 0 testes. |
| 2 — data-testid | ✅ Concluída | Testids em 12 arquivos (nav, navbar, cards, forms, carrinho, checkout, cupom, endereço, review). `npm run build` ok. Lint: 1 erro pré-existente em `DetalhesLivro.jsx` (não relacionado). |
| 3 — Specs core | ✅ Concluída | 6 testes (01, 02, 03×2, 04, 09) — 2 runs verdes (~17s). Descoberta: App oculta navbar na tela de retorno; log `No cart found` é fluxo normal. |
| 4 — Specs secundários | ✅ Concluída | 4 specs novos (05–08) → total 11 testes, 3 runs verdes ~24–26s. MP 100% mockado (page.route no checkout + sandbox). Fixes: workers 3 (pool SQLAlchemy); seção retrátil reabre (remount); orderId via response (sessionStorage por origem). |
| 5 — Documentação | ✅ Concluída | Seção "Testes E2E" no HANDOFF (pré-requisitos, como rodar, limpeza por ordem reversa de FKs) + README do front reescrito. Um novo dev consegue rodar pelo HANDOFF. |
