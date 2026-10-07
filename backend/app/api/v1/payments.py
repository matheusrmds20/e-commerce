import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.exceptions import HTTPException
from mercadopago.webhook import (
    InvalidWebhookSignatureError,
    WebhookSignatureValidator,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.models.user import User
from app.schemas.payment import (
    PaymentCheckoutResponse,
    PaymentCreate,
    PaymentResponse,
    WebhookResponse,
)
from app.services.payment_service import PaymentService

settings = get_settings()

logger = logging.getLogger(__name__)

payment_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
UserDb = Annotated[User, Depends(get_current_user)]

def get_payment_service(db: DbSession) -> PaymentService:
    return PaymentService(db)

@payment_router.post(
    "/create",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo pagamento para o usuário autenticado",
)
def create_payment(
    data: PaymentCreate, user: UserDb, db: DbSession
):

    return get_payment_service(db).create(data)

@payment_router.get(
    "/get/{payment_id}",
    response_model=PaymentResponse,
    summary="Busca um pagamento pelo ID",
)
def get_payment(
    payment_id: int, user: UserDb, db: DbSession
) -> PaymentResponse:

    return get_payment_service(db).get_by_id(payment_id)


@payment_router.get(
    "/order/{order_id}",
    response_model=list[PaymentResponse],
    summary="Busca pagamentos de um pedido",
)
def get_payments_by_order_id(
    order_id: int, user: UserDb, db: DbSession
) -> list:

    return get_payment_service(db).get_by_order_id(user, order_id)

@payment_router.post(
    "/checkout/{order_id}",
    response_model=PaymentCheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo pagamento para o usuário autenticado",
)
def create_payment_checkout(
    order_id: int, user: UserDb, db: DbSession
):

    return get_payment_service(db).create_checkout(order_id, user.id)

@payment_router.post(
    "/webhook",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Processa um webhook de pagamento (sem barra final)",
    include_in_schema=False,
)
@payment_router.post(
    "/webhook/",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Processa um webhook de pagamento",
)
async def process_webhook(
    request: Request,
    db: DbSession,
) -> WebhookResponse:

    x_signature = request.headers.get("x-signature")
    x_request_id = request.headers.get("x-request-id")
    query = request.query_params

    # Este endpoint processa apenas notificações no formato Webhook (novo):
    #     ?data.id=...&type=payment | topic_merchant_order_wh
    # Notificações IPN (clássico) usam ?id=...&topic=... e são ignoradas de
    # propósito — a configuração no painel do Mercado Pago deve usar Webhooks.
    data_id = query.get("data.id")
    tipo = query.get("type", "")

    if data_id is None or not tipo:
        logger.info(
            "Notificação ignorada (não é Webhook; provável IPN): query=%s",
            dict(query),
        )
        return {"status": "ignored"}

    # Normaliza "topic_merchant_order_wh" -> "merchant_order".
    topic = tipo.replace("topic_", "").replace("_wh", "")

    # Mais de uma aplicação do Mercado Pago pode enviar webhooks para a mesma
    # URL, cada uma assinando com o seu próprio secret. Tentamos o secret
    # principal e os extras (MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA).
    secrets = [settings.MERCADO_PAGO_WEBHOOK_SECRET]
    secrets += [
        s.strip()
        for s in settings.MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA.split(",")
        if s.strip()
    ]

    erro: InvalidWebhookSignatureError | None = None
    assinatura_ok = False
    for secret in secrets:
        try:
            WebhookSignatureValidator.validate(
                x_signature, x_request_id, data_id, secret
            )
            assinatura_ok = True
            break
        except InvalidWebhookSignatureError as exc:
            erro = exc

    if not assinatura_ok and not settings.VALIDATE_WEBHOOK_SIGNATURE:
        # Validação de assinatura DESLIGADA por configuração (VALIDATE_WEBHOOK_SIGNATURE=false).
        #
        # Motivo: em ambiente de TESTE/sandbox, o Mercado Pago assina as
        # notificações com um secret que NÃO é o exibido no painel da aplicação
        # (o envelope é assinado no contexto da conta de teste, não da app),
        # tornando impossível validar em sandbox com o secret do painel.
        # Em produção, com credenciais de produção, a validação funciona e deve
        # ser reativada (VALIDATE_WEBHOOK_SIGNATURE=true).
        logger.info(
            "Webhook aceito SEM validar assinatura (VALIDATE_WEBHOOK_SIGNATURE=false). "
            "reason=%s request_id=%s",
            erro.reason.value if erro else "?",
            x_request_id,
        )
        assinatura_ok = True

    if not assinatura_ok:
        assert erro is not None
        err = erro
        # Loga a razão exata (SIGNATURE_MISMATCH, MISSING_SIGNATURE_HEADER, etc.)
        # para permitir distinguir secret errado de header ausente/malformado.
        # Calcula a idade do ts: webhooks antigos demais indicam reenvios da
        # fila de retry do MP assinados com um secret anterior.
        idade_s = None
        if err.timestamp and err.timestamp.isdigit():
            idade_s = int(time.time()) - int(err.timestamp)
        logger.warning(
            "Webhook signature rejected: reason=%s request_id=%s ts=%s "
            "idade_ts_s=%s data_id=%s has_signature=%s query=%s",
            err.reason.value,
            err.request_id,
            err.timestamp,
            idade_s,
            data_id,
            x_signature is not None,
            dict(query),
        )
        if idade_s is not None and idade_s > 86400:
            logger.warning(
                "Webhook com ts de %.1f dias atrás — provavelmente reenvio da "
                "fila do MP assinado com secret antigo; a rejeição é esperada "
                "e independe do secret atual.",
                idade_s / 86400,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        ) from err

    data = await request.json()

    # Notificações que não são de pagamento/pedido não devem ser processadas:
    #  - mp-connect: vinculação de conta via OAuth
    #  - claims / etc.: disputas, integrações, etc.
    # Retornar 200 evita que o MP fique reenviando a notificação.
    tipos_de_pagamento = {
        "payment",
        "merchant_order",
        "topic_payment",
        "topic_merchant_order",
        "topic_payment_wh",
        "topic_merchant_order_wh",
    }
    if tipo not in tipos_de_pagamento:
        logger.info("Webhook ignorado (type=%s)", tipo)
        return {"status": "ignored"}

    # No formato Webhook o id vem em data.id (corpo ou query).
    payment_id = data.get("data", {}).get("id") or data_id

    if not payment_id:
        return {"status": "ignored"}

    try:
        get_payment_service(db).process_webhook(
            str(payment_id), topic=topic or None
        )
    except Exception:  # noqa: BLE001
        # Registra o erro mas responde 200: o MP reenvia por 15 min em caso de
        # 5xx, o que só repete a falha. O log permite investigar depois.
        logger.exception(
            "Falha ao processar webhook (id=%s, topic=%s)", payment_id, topic
        )
        return {"status": "error"}

    return {"status": "ok"}
