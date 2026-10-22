# ADR-001 — Webhook de pagamento via threadpool (não Celery)

> Versão completa e canônica desta decisão de arquitetura. O `README.md` da raiz
> mantém um resumo e aponta para este documento.

- **Status:** Aceito
- **Data:** 2026
- **Contexto técnico:** FastAPI + Uvicorn (1 worker no plano free do Render),
  SDK síncrono do Mercado Pago, Celery/Redis disponíveis apenas para jobs de
  e-mail e PDF.

---

## Contexto

O endpoint `POST /api/v1/payments/webhook` (também exposto com barra final em
`/api/v1/payments/webhook/`, para tolerar a configuração de `notification_url`
do Mercado Pago) é chamado pelo Mercado Pago sempre que um pagamento muda de
status.

O trabalho real do handler é:

1. validar a assinatura (`x-signature` / `x-request-id` / `data.id`);
2. consultar o pagamento no Mercado Pago (SDK **síncrono**, HTTP **bloqueante**,
   com timeout de `MERCADO_PAGO_TIMEOUT` — padrão **8s**);
3. atualizar o pedido conforme o status;
4. disparar o e-mail de confirmação e a geração do comprovante PDF.

Ver `app/api/v1/payments.py`, `app/services/payment_service.py` e
`app/integrations/MercadoPago/geteway.py`.

---

## Problema

O handler é declarado como `async def` (é o que o FastAPI exige para receber o
`Request` e usar `Depends` de forma assíncrona). Chamar diretamente o SDK
síncrono do Mercado Pago dentro dele **bloquearia o event loop**.

Em um processo Uvicorn **single-worker** isso congela **todos** os endpoints
enquanto o Mercado Pago não responder (até 8s por notificação, e o MP reenvia a
notificação várias vezes até receber `2xx`). Em pico de reenvios, a API inteira
fica inacessível.

---

## Decisão

Executar o processamento em uma **thread** com
`starlette.concurrency.run_in_threadpool`, em vez de enfileirar uma task no
Celery:

```python
from starlette.concurrency import run_in_threadpool

# app/api/v1/payments.py
await run_in_threadpool(
    get_payment_service(db).process_webhook,
    str(payment_id),
    topic or None,
)
```

O `run_in_threadpool` move a chamada bloqueante para o threadpool do Starlette
(qualquerio), liberando o event loop para atender as demais requisições.

### Por que thread e não Celery aqui?

- O deploy é **plano free** (Render) e **não fica 24/7** — é um projeto de
  portfólio. Cada worker/processo dedicado consome RAM e horas de execução; o
  objetivo é **leveza e simplicidade** com **um único serviço web**.
- O processamento do webhook é **curto** (uma chamada HTTP com timeout de 8s no
  gateway). Não justifica broker + worker + monitoramento só para isso.
- `run_in_threadpool` resolve o problema real (bloqueio do event loop) **sem
  adicionar infraestrutura**.

---

## E o Celery?

Celery/Redis **continuam no projeto** e seguem sendo usados para os jobs
**pesados/assíncronos**, que não precisam de resposta imediata:

- `send_order_confirmation_email` — `app/utils/email.py`
- `generate_order_receipt` — `app/utils/receipt_tasks.py`

A decisão é **específica do webhook**, cujo custo não justifica um worker
dedicado. As tasks são registradas em `app/main.py`:

```python
celery.conf.imports = ("app.utils.email", "app.utils.receipt_tasks")
```

---

## Consequências

### Positivas

- ✅ API única; **nenhum worker é obrigatório** para o fluxo de pagamento.
- ✅ Menos RAM e menos infraestrutura no plano free.
- ✅ O event loop continua livre: outros endpoints respondem normalmente mesmo
  com o Mercado Pago lento.
- ✅ O webhook responde **200** mesmo quando o processamento falha — o Mercado
  Pago reenvia por até 15 minutos em caso de `5xx`, então responder `5xx` só
  multiplicaria o problema. O erro vai para o log para investigação.

### Negativas / cuidados

- ⚠️ O trabalho acontece **no processo da API**. Se o volume de notificações
  crescer muito, o threadpool pode saturar.
- ⚠️ A validação de assinatura (`VALIDATE_WEBHOOK_SIGNATURE`) está **desligada** neste
  projeto de portfólio (decisão e mitigação de risco em **ADR-002**,
  `README_WEBHOOK_SIGNATURE_DECISION.md`). Só reative com `true` em produção com
  pagamentos reais. Segredos extras podem ser informados em
  `MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA` (lista separada por vírgula) durante rotação de chaves.
- ⚠️ O endpoint tem rate limit próprio (`120/minute`, ver
  `app/api/v1/payments.py` e `app/api/limiter.py`) — se o MP reenviar em rajada
  acima disso, as notificações podem ser descartadas com `429`.

---

## Caminho de migração (se o volume crescer)

1. Extrair `process_webhook` para uma função pura que abre a própria sessão
   (`SessionLocal`), sem depender do `db` da requisição.
2. Criar uma task `@shared_task` que apenas chama essa função.
3. No handler, trocar o `run_in_threadpool(...)` por
   `process_payment_webhook_task.delay(payment_id, topic)`.
4. Subir o **Background Worker** no Render (`celery -A app.main.celery worker`)
   e manter o `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` apontando para o Redis.

O contrato HTTP do endpoint **não muda** — apenas o local de execução.

---

## Referências

- `app/api/v1/payments.py` — rotas `/checkout/{order_id}`, `/history`,
  `/webhook` e `/webhook/`
- `app/services/payment_service.py` — regra de negócio do webhook
- `app/integrations/MercadoPago/geteway.py` — SDK + validação de assinatura
- `backend/deploy.md` — deploy no Render (free)
- `README.md` (raiz) — resumo na seção “Decisões de arquitetura (ADRs)”
