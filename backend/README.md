# Backend — E-commerce API

API REST em FastAPI para o e-commerce (produtos, pedidos, pagamentos via
Mercado Pago Checkout Pro, cupons, avaliações, etc.).

## Pagamentos — Mercado Pago (Checkout Pro)

### Fluxo

1. `POST /api/v1/payments/checkout/{order_id}` cria uma *preference* no
   Mercado Pago e devolve `checkout_url` (`init_point`).
2. O cliente é redirecionado ao checkout do MP e conclui o pagamento.
3. O MP envia notificações (Webhooks) para
   `POST /api/v1/payments/webhook/`, que atualiza o status do pagamento e do
   pedido.

### Formatos de notificação aceitos

O endpoint processa **apenas o formato Webhook** (novo):

```
POST /api/v1/payments/webhook/?data.id=<id>&type=payment
POST /api/v1/payments/webhook/?data.id=<id>&type=topic_merchant_order_wh
```

Notificações **IPN** (clássico, `?id=...&topic=...`) são **ignoradas de
propósito** — a configuração no painel do Mercado Pago deve usar Webhooks.

Tipos processados: `payment`, `merchant_order`. Tipos como `mp-connect`
(vinculação OAuth), `claims` (disputas) etc. são respondidos com 200 e
ignorados, para que o MP não fique reenviando.

O endpoint aceita a rota com e sem barra final (`/webhook` e `/webhook/`).

### Validação de assinatura (`x-signature`)

Segue o padrão oficial do Mercado Pago:

- **Manifest**: `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`
  (pares vazios omitidos; sempre termina com `;`).
- **HMAC-SHA256** do manifest, usando o secret como bytes UTF-8.
- Comparação em tempo constante (`hmac.compare_digest`).

O `data.id` vem da **query string** (`?data.id=...`). O HMAC **não** usa o
corpo da requisição — diferente de Stripe/GitHub, que assinam o *raw body*.

#### `VALIDATE_WEBHOOK_SIGNATURE`

| Valor | Comportamento |
| --- | --- |
| `true` | Rejeita (401) webhooks com assinatura inválida. **Use em produção** com credenciais de produção. |
| `false` | Aceita o webhook sem validar a assinatura; registra um `INFO`. |

> **Por que existe essa flag?** Em ambiente de **teste/sandbox** com contas de
> teste, o Mercado Pago assina as notificações com um secret que **não** é o
> exibido no painel da aplicação (o envelope é assinado no contexto da conta de
> teste, não da aplicação). Isso torna a validação impossível em sandbox com o
> secret do painel. Neste projeto, o ambiente de demonstração roda em sandbox,
> então a flag fica `false`. Em produção, com credenciais de produção, a
> validação funciona e deve ser reativada.

Para suportar mais de uma aplicação MP enviando webhooks para a mesma URL,
use `MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA` (secrets separados por vírgula): o
endpoint tenta validar contra o secret principal e todos os extras.

### Idempotência e resiliência

- Pagamentos já `approved` não são reprocessados.
- Se o `id` recebido for de uma *merchant_order* (que agrega vários
  pagamentos), o service resolve o pagamento aprovado correspondente.
- Se `GET /v1/payments/{id}` retornar 404, o service tenta resolver o id como
  *merchant_order* (fallback) antes de desistir.
- Falhas de processamento retornam **200** (com log do stack trace) para evitar
  que o MP reenvie a mesma notificação por 15 minutos em loop.

## Configuração (variáveis de ambiente)

Veja `.env.example`. Principais:

```
MERCADO_PAGO_ACCESS_TOKEN=           # credencial (teste ou produção)
MERCADO_PAGO_WEBHOOK_SECRET=         # assinatura secreta da aplicação
MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA=  # opcional, separado por vírgula
VALIDATE_WEBHOOK_SIGNATURE=true      # false apenas em sandbox
```
