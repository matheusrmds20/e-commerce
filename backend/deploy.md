# Deploy no Render (API) + Supabase (banco)

Guia de deploy para a **API no Render** (plano **gratuito**) e o **banco
PostgreSQL no Supabase** (plano **free**). Foi desenhado para ser
**leve** (1 serviço web) — adequado para um projeto de portfolio que não fica
24/7.

> ⚠️ **Decisões importantes que afetam o deploy:**
> - O endpoint de webhook do pagamento roda em **thread** (`run_in_threadpool`),
>   **não** em worker Celery dedicado — por isso **não há serviço worker extra**
>   nem broker obrigatório para o fluxo de pagamento. Ver
>   `backend/README_WEBHOOK_DECISION.md`.
> - E-mail de confirmação e comprovante PDF **usam Celery/Redis**. Se você quiser
>   esses envios, crie o **worker** e um **Redis (Key Value)** no Render. Se não
>   quiser, desligue essas tasks para manter só 1 serviço.

---

## 1. Serviços no Render

| Serviço | Tipo | Necessário? |
|---|---|---|
| Web API (FastAPI) | **Web Service** (free) | Sim |
| Postgres | **Supabase** (free) | Sim |
| Redis (para Celery de e-mail/PDF) | **Key Value** (free) | Só se usar Celery |
| Celery Worker | **Background Worker** | Só se usar Celery |

---

## 2. Web Service (FastAPI)

**Definições no dashboard do Render (Web Service → New):**

- **Build Command** (o projeto usa `pyproject.toml`, Python >= 3.11):
  ```bash
  pip install .
  ```
  (ou `pip install -e .` para modo editable; se houver `requirements.txt`, use-o).

- **Start Command**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
  > Use `$PORT` (o Render define a porta). **Não use `--workers`** — no plano
  > free a RAM é 512 MB; 1 worker é o correto.

- **Root Directory:** `backend`

- **Health check path:** `"/api/v1/health/"` (a raiz `/` responde `204` quando
  `DEBUG=false`).

### Variáveis de ambiente (Web Service)

Preencha no painel **Environment** (valores de produção):

```
DATABASE_URL=<connection string do Supabase (pooler, porta 6543)>
SECRET_KEY=<string longa e aleatória>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256
BACKEND_URL=https://<seu-web-service>.onrender.com
FRONTEND_URL=https://<seu-front>.onrender.com
MERCADO_PAGO_ACCESS_TOKEN=<seu token MP>
MERCADO_PAGO_WEBHOOK_SECRET=<seu secret MP>
VALIDATE_WEBHOOK_SIGNATURE=false  # portfólio (ver checklist 5.2 / ADR-002)
SMTP_HOST=...
SMTP_PORT=...
SMTP_USER=...
SMTP_PASSWORD=...
MELHOR_ENVIO_API_TOKEN=...        # se usar frete
MELHOR_ENVIO_ORIGIN_ZIP=...
MELHOR_ENVIO_SANDBOX=false        # produção
# Só se usar Celery:
CELERY_BROKER_URL=<redis://... do Key Value>
CELERY_RESULT_BACKEND=<redis://... do Key Value>
```

---

## 3. Banco — PostgreSQL no Supabase (free)

- Crie um **projeto no Supabase** → plano **Free**.
- Copie a **Connection String** (Project Settings → Database) — prefira o
  **pooler** (porta 6543) para usar com a API.
- Use essa connection string como `DATABASE_URL` do web service.
- ⚠️ **Limitações do free:** o projeto é **pausado após ~7 dias de inatividade**
  (volta com um clique no painel) e tem limite de storage/bandas. Para um
  projeto de demonstração isso costuma ser suficiente; se o projeto pausar, só
  reative no dashboard do Supabase.
- ⚠️ Tráfego entre a API (Render, região padrão US) e o Supabase é externo —
  use a **connection string de pooler externa** (`aws-0-<região>.pooler.supabase.com`),
  não a interna.

> ℹ️ **Nota sobre pg_dump:** o Supabase free não "expira" como o Postgres free
> da Render fazia — o maior risco é a pausa por inatividade, que não apaga
> dados. Mesmo assim, mantenha backups (`pg_dump`) ou exports do projeto se os
> dados forem importantes.

---

## 4. Celery (opcional — e-mail/PDF)

Se mantiver os jobs de e-mail e comprovante:

- Crie um **Key Value (Redis)** free e use o broker nas env vars do web service.
- Crie um **Background Worker** com o mesmo código e start command:
  ```bash
  celery -A app.main.celery worker --loglevel=info
  ```
- ⚠️ **Render não tem plano free para workers** em muitos casos e **cada worker
  conta horas**. Para não 24/7 dá para usar sob demanda, mas o mais leve é
  desligar esses jobs e rodar só o web service.

---

## 5. Notas do plano free

- **Spin-down:** o web service cai após ~15 min sem tráfego e leva ~1 min pra
  subir (cold start). Aceitável para portfolio.
- **750 horas/mês:** um serviço ligado 24/7 estoura em ~30 dias. Para demo, veja
  sempre que mostrar.
- **CORS e hosts:** configure `CORS_ORIGINS` (origem do front, ex.:
  `["https://papiro.matheuslab.xyz"]`) e `ALLOWED_HOSTS` (host da API, ex.:
  `["api-e-commerce.matheuslab.xyz"]`) por variável de ambiente — não edite
  `main.py`. Com `DEBUG=false`, `CORS_ORIGINS` com `*` aborta o startup.

---

## 5.1 Aplicar migrations (Alembic) em produção

O Alembic fica na **raiz do repo** (`alembic/`) e o `alembic/env.py` **lê a URL
correta do banco das env vars** (via `get_settings().DATABASE_URL`) — não precisa
de configuração extra por ambiente.

### Fluxo diário (local) — gerar e testar

A partir da **raiz do repo**, com o Postgres local (docker-compose) rodando:

```bash
# autogenera a migration a partir dos models
alembic revision --autogenerate -m "descricao"

# revise o arquivo gerado em alembic/versions/ antes de aplicar

# aplica no seu banco local
alembic upgrade head
```

> Gerar uma migration **delega a comparação** ao seu banco local → sempre revise
> o arquivo gerado (índices, nullability, server_default) antes de subir.

### Aplicar em produção (Render) — Opção A (recomendada): Pre-Deploy Command

No painel do Render (Web Service → **Pre-Deploy Command**), rode a migration
**antes** do app subir, na hora do deploy:

```bash
alembic upgrade head
```

O start command segue normal:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Assim, **toda vez que você faz deploy**, as migrations pendentes são aplicadas
automaticamente — sem precisar de acesso manual ao banco. É idempotente
(`upgrade head` só aplica o que falta): se o banco do Supabase for recriado do
zero, o deploy aplica o schema automaticamente.

### Alternativas (se não usar Pre-Deploy Command)

- **Render Shell** (web service): `alembic upgrade head`.

### Boas práticas desta base

- Nunca edite uma migration **já aplicada** em produção (crie uma nova para
  corrigir).
- Sempre rode `alembic upgrade head` localmente antes de abrir o PR.
- Comite o arquivo gerado em `alembic/versions/` junto com o model.

---

## 5.2 Checklist obrigatório antes de subir para produção

Dois itens **não têm default que funcione sozinho** para este projeto e precisam
ser configurados no painel do Render:

1. **`VALIDATE_WEBHOOK_SIGNATURE=false`** (Web Service → Environment) — **apenas
   na demo**; em produção com pagamentos reais deixe `true`

   O default no código é `true`, mas este projeto opera com o webhook **sem
   validação de assinatura** (decisão de portfólio, ver ADR-002). Se essa
   variável **não existir no painel**, produção vai subir com `true` e o webhook
   do Mercado Pago será rejeitado. Garanta que está **explicitamente `false`**
   no painel (o `.env` local não vai para o Render).

2. **Pre-Deploy Command: `alembic upgrade head`** (Web Service → Pre-Deploy
   Command)

   Necessário para criar tabelas novas como `refresh_tokens` (P1-1) no banco
   antes do app subir. Ver seção 5.1.

### Redis — simplificação para o plano gratuito (não criar infra nova)

- **Não crie um Redis novo** para lockout/rate limit.
- `LOGIN_LOCKOUT_REDIS_URL` **deixe vazio** → o lockout herda o
  `CELERY_BROKER_URL` (Upstash) que já está no painel; os contadores têm TTL e
  não atrapalham a fila do Celery.
- `RATE_LIMIT_STORAGE_URI` mantenha **`memory://`** (padrão): com **1 worker**
  no Render free, o rate limit em memória é consistente. Só troque por Redis
  quando escalar para múltiplos workers.

---

## 6. Ordem recomendada de criação

1. **Projeto no Supabase** (para pegar a `DATABASE_URL`).
2. **Web Service** (com as env vars, apontando pra `DATABASE_URL`).
3. **(Opcional)** **Key Value (Redis)** + **Worker** se quiser e-mail/PDF.
4. Configure o **Mercado Pago** com `notification_url` apontando para
   `https://<seu-web-service>.onrender.com/api/v1/payments/webhook/`.