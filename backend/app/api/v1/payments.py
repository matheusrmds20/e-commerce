import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.exceptions import HTTPException
from mercadopago.webhook import (
    InvalidWebhookSignatureError,
    WebhookSignatureValidator,
)
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_current_user, get_db
from app.api.exceptions import (
    BookCommerceException,
    IntegrationUnavailableError,
)
from app.api.limiter import limiter
from app.core.config import get_settings
from app.models.user import User
from app.schemas.common import Page
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
    return get_payment_service(db).create(data, user.id)

@payment_router.get(
    "/get/{payment_id}",
    response_model=PaymentResponse,
    summary="Busca um pagamento pelo ID (somente o dono)",
)
def get_payment(
    payment_id: int, user: UserDb, db: DbSession
) -> PaymentResponse:

    return get_payment_service(db).get_by_id(payment_id, user.id)


@payment_router.get(
    "/order/{order_id}",
    response_model=list[PaymentResponse],
    summary="Busca pagamentos de um pedido",
)
def get_payments_by_order_id(
    order_id: int, user: UserDb, db: DbSession
) -> list:

    return get_payment_service(db).get_by_order_id(user, order_id)


@payment_router.get(
    "/history",
    response_model=Page[PaymentResponse],
    summary="Histórico de pagamentos do usuário autenticado (paginado)",
)
def get_payments_history(
    user: UserDb,
    db: DbSession,
    page: Annotated[int, Query(ge=1, description="Página (começa em 1)")] = 1,
    per_page: Annotated[
        int, Query(ge=1, le=100, description="Itens por página (max 100)")
    ] = 20,
) -> dict:

    return get_payment_service(db).get_history_paginated(user.id, page, per_page)

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
@limiter.limit("120/minute")
async def process_webhook(
    request: Request,
    db: DbSession,
) -> WebhookResponse:

    x_signature = request.headers.get("x-signature")
    x_request_id = request.headers.get("x-request-id")
    query = request.query_params


    data_id = query.get("data.id")
    tipo = query.get("type", "")

    if data_id is None or not tipo:
        logger.info(
            "Notificação ignorada (não é Webhook; provável IPN): query=%s",
            dict(query),
        )
        return {"status": "ignored"}

    topic = tipo.replace("topic_", "").replace("_wh", "")

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
        await run_in_threadpool(
            get_payment_service(db).process_webhook,
            str(payment_id),
            topic or None,
        )
    except IntegrationUnavailableError as exc:
        # D23b: falha transitória -> 5xx para o provedor reenviar.
        logger.warning(
            "Webhook indisponível, pedindo reenvio (id=%s, topic=%s): %s",
            payment_id,
            topic,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dependência indisponível, reenvie a notificação.",
        ) from exc
    except BookCommerceException:
        # D23b: erro de negócio definitivo -> o provedor não deve reenviar.
        logger.exception(
            "Webhook rejeitado por regra de negócio (id=%s, topic=%s)",
            payment_id,
            topic,
        )
        raise
    except Exception as exc:
        # D23b: erro inesperado -> 5xx para o provedor reenviar.
        logger.exception(
            "Falha inesperada ao processar webhook (id=%s, topic=%s)",
            payment_id,
            topic,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao processar a notificação, reenvie.",
        ) from exc

    return {"status": "ok"}
