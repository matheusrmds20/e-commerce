# ADR-002 — Validação de assinatura do webhook de pagamento desligada (portfólio)

> Versão canônica desta decisão de arquitetura. O `README.md` da raiz mantém um
> resumo e aponta para este documento.

- **Status:** Aceito (vigente)
- **Data:** atual
- **Contexto técnico:** FastAPI + Uvicorn (plano free do Render), SDK do Mercado
  Pago, projeto de **portfólio** (sem pagamentos reais), `VALIDATE_WEBHOOK_SIGNATURE`
  configurado como `false`.

---

## Contexto

O endpoint `POST /api/v1/payments/webhook` recebe notificações do Mercado Pago
quando um pagamento muda de status. Para garantir a autenticidade do evento, o
fluxo ideal valida o cabeçalho `x-signature` (com `x-request-id` e `data.id`)
contra o segredo `MERCADO_PAGO_WEBHOOK_SECRET`, com suporte a rotação via
`MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA`.

Ver `WebhookSignatureValidator` em `app/core/security.py` e a validação em
`app/api/v1/payments.py`.

---

## Problema

Ao configurar o webhook para o ambiente de demonstração/portfólio, o Mercado
Pago **entrega** a notificação, mas a assinatura `x-signature` recebida **nunca
confere** com o valor esperado pelo validador. Foram esgotadas as tentativas
usuais:

- conferência do `x-secret` configurado no painel vs `.env`;
- suporte a múltiplos segredos (`MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA`);
- validação do formato de entrada e do cálculo do hash.

O problema persiste e **não houve disposição para continuar depurando**, pois o
fluxo de pagamento **não é usado de verdade** (projeto de portfólio, sem
pagamentos reais).

> Decisão explícita: se no futuro o webhook for **realmente usado** (produção
> com pagamentos reais), a validação da assinatura deve ser **reativada** e o
> problema de cálculo revisitado obrigatoriamente.

---

## Decisão

Manter a validação de assinatura **desligada** neste ambiente, por meio da
variável de configuração:

```env
VALIDATE_WEBHOOK_SIGNATURE=false
```

A implementação **não foi removida** do código. O ponto de decisão já existe em
`app/api/v1/payments.py`:

```python
if not assinatura_ok and not settings.VALIDATE_WEBHOOK_SIGNATURE:
    logger.info(
        "Webhook aceito SEM validar assinatura (VALIDATE_WEBHOOK_SIGNATURE=false). "
        "reason=%s request_id=%s",
        erro.reason.value if erro else "?",
        x_request_id,
    )
    assinatura_ok = True
```

Nesse modo, qualquer evento com `data.id` válido é aceito, **com log explícito**
de que a assinatura não foi validada.

### Por que não remover o validador do código?

- Preserva o trabalho já feito (`WebhookSignatureValidator`, múltiplos secrets,
  tolerância de timestamp, logging).
- Permite **reativar** com mudança de uma única variável quando o webhook passar
  a ser usado de verdade.
- Evita churn em imports, testes e documentação.

---

## Mitigação de risco (importante)

Desligar a assinatura **não** significa que o sistema "aprova pagamento fake"
cegamente. O fluxo real do webhook **não confia no payload recebido**:

```
webhook (POST) ──► usa data.id como gatilho ──► gateway.get_payment(payment_id)
                                                    │
                                                    ▼
                                    consulta REAL na API do Mercado Pago
                                                    │
                                                    ▼
                              usa status/valor/ref vindos da API (não do webhook)
```

Ver `process_webhook` em `app/services/payment_service.py` e
`get_payment` em `app/integrations/MercadoPago/geteway.py`.

Consequência prática: um webhook forjado com um `data.id` falso apenas dispara
uma consulta à API do Mercado Pago que retorna inexistente/erro — **não** marca
um pedido como pago.

---

## Consequências

### Positivas

- ✅ Fluxo de demonstração/portfólio funciona sem depender da correção da
  assinatura, já que o estado do pagamento é conferido na API do Mercado Pago.
- ✅ Decisão reversível com `true`.

### Negativas / cuidados

- ⚠️ **Definitivamente não usar em produção com pagamentos reais.** Sem assinatura,
  um atacante pode forjar os callbacks e **disparar chamadas à API do Mercado
  Pago** (consumo de quota/token) e **gatilhos de processamento** de pedidos.
  O risco de "aprovar pagamento fake" é baixo (por causa da consulta à API),
  mas a superfície de abuso existe.
- ⚠️ A flag fica exposta a **erro de configuração acidental** (ex.: esquecer de
  reativar ao ir a produção). Por isso o log de "aceito SEM validar" é essencial
  para auditoria de quando isso ocorre.

---

## Como reativar (quando o webhook for usado de verdade)

1. Corrigir o cálculo/segredo da assinatura no painel do Mercado Pago e no `.env`.
2. Voltar `VALIDATE_WEBHOOK_SIGNATURE=true`.
3. Confirmar que `WebhookSignatureValidator` aceita `x-signature`/`x-request-id`/
   `data.id` exibidos em um teste real.
4. (Opcional) exigir no startup que produção não rode com a flag desligada — ver
   decisão registrada em `README.md`.

---

## Referências

- `app/api/v1/payments.py` — rotas `/webhook` e validação da assinatura
- `app/core/security.py` — `WebhookSignatureValidator`
- `app/services/payment_service.py` — `process_webhook` (consulta real ao MP)
- `app/integrations/MercadoPago/geteway.py` — SDK + `get_payment`
- `README_WEBHOOK_DECISION.md` — ADR-001 (threadpool do webhook)