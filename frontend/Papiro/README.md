# Papiro — Frontend

Vitrine de e-commerce de livros (React 19 + Vite + Tailwind v4), alimentada
pela API FastAPI do repositório (`../backend`). Este README cobre o básico de
dev e os **testes E2E (Playwright)**.

> Layout de referência (Painel): `node_modules` não entra no repo — a pasta
> raiz do projeto tem `HANDOFF.md` (contexto completo, incl. uma seção
> "Testes E2E") e `E2E_PLANO.md` (plano e progresso das fases 0–5).

## Requisitos

- Node 22+ (npm/npx).
- Backend local rodando em `http://localhost:8000` (ver `backend/` do repo).
- Para E2E: Postgres (Docker) com o banco de teste `bookcommerce-e2e`
  provisionado (migrations + seed) — ver "Testes E2E" abaixo.

## Scripts

| Comando | O que faz |
|---|---|
| `npm run dev` | Sobe o dev server (Vite) em `http://localhost:5173` |
| `npm run build` | Build de produção para `dist/` |
| `npm run lint` | ESLint no `src/` |
| `npm run e2e` | Roda a suíte E2E (Playwright) — **sobe sozinho** o backend de teste + o Vite |
| `npm run e2e:ui` | Modo interativo do Playwright (browser + timeline) |

> A API base é `VITE_API_URL`. O default (`https://api-e-commerce.matheuslab.xyz/api/v1`
> em `src/api/client.js`) é um **túnel para o backend local** (porta 8000), logo
> hoje não há risco de bater numa API remota de produção. Mesmo assim, o E2E
> **sempre força** `VITE_API_URL=http://localhost:8000/api/v1` no `webServer`
> (ou `npm run dev -- --mode e2e`, do `.env.e2e`): o backend local precisa ser
> apontado para o **banco de teste isolado** (`bookcommerce-e2e`), e não ao
> banco de dev — e sem depender do túnel/rede externa.

## Testes E2E (Playwright)

Suíte em `e2e/` — navega por cliques (o front ainda não tem roteador),
autentica pela UI de verdade e mocka o Mercado Pago por completo
(`page.route`), para nunca chamar o MP real.

**Pré-requisitos (uma vez):**

```bash
# 1. Instalar o Playwright + Chromium
npm i -D @playwright/test
npx playwright install chromium

# 2. Provisionar o banco de teste (da raiz do repo)
cd "C:/Users/mathe/OneDrive/Desktop/E-commerce v1"
DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5433/bookcommerce-e2e" ./venv/Scripts/alembic.exe upgrade head
cd backend
DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5433/bookcommerce-e2e" ../venv/Scripts/python.exe -m scripts.seed
```

**Rodar:**

```bash
npm run e2e        # suíte completa (11 testes)
npm run e2e:ui     # interativo
npx playwright test e2e/specs/04-carrinho.spec.js --workers=1   # 1 arquivo
```

O `playwright.config.js` sobe dois servidores via `webServer`: o backend E2E
(`backend/scripts/e2e_server.py`, porta 8000, banco `bookcommerce-e2e`) e o
Vite com `VITE_API_URL` local. Requer a **porta 8000 livre**.

**Cobertura:** home com dados reais · acervo → detalhe · registro/login
(reload restaura sessão) · carrinho (visitante + logado persistente) ·
wishlist · review · endereço (ViaCEP mockado) · checkout com **Mercado Pago
mockado** · tela de retorno do pagamento.

Detalhes de operação e limpeza de dados de teste: seção **"Testes E2E"** do
`HANDOFF.md` na raiz do repositório.

## Stack / estrutura

- `src/pages/` — telas (Home, Acervo, DetalheLivro, Carrinho, Checkout,
  Login, Registro, MinhaConta, Admin).
- `src/components/` — blocos de UI (BookCard, Navbar, PainelCompra, modais,
  seções retráteis, etc.).
- `src/context/` — `AuthProvider` (token JWT em `localStorage['papiro.token']`)
  e `CartProvider` (sincroniza com a API quando logado; memória para visitante).
- `src/api/` — cliente axios + serviços por domínio.
- `e2e/` — specs, fixtures e helpers do Playwright.