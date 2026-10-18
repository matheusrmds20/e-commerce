import mercadopago
from mercadopago.config import RequestOptions

from app.api.exceptions import (
    IntegrationRejectedError,
    IntegrationUnavailableError,
)
from app.core.config import get_settings

settings = get_settings()

PROVIDER_NAME = "mercado_pago"


class MercadoPagoGateway:

    def __init__(self):
        self.sdk = mercadopago.SDK(
            settings.MERCADO_PAGO_ACCESS_TOKEN,
            request_options=RequestOptions(
                connection_timeout=settings.MERCADO_PAGO_TIMEOUT,
                # Cobrança não é idempotente (D23/B16): sem retry automático.
                max_retries=0,
            ),
        )

    def _handle(self, response: dict) -> dict:
        """Traduz a resposta do SDK em payload ou exceção de domínio."""
        status_code = response.get("status", 0)

        if 500 <= status_code < 600 or status_code == 0:
            raise IntegrationUnavailableError(PROVIDER_NAME, str(response))

        if status_code >= 400:
            raise IntegrationRejectedError(PROVIDER_NAME, str(response))

        return response["response"]

    def create_preference(self, data: dict) -> dict:
        return self._handle(self.sdk.preference().create(data))

    def get_preference(self, preference_id: str) -> dict:
        return self._handle(self.sdk.preference().get(preference_id))

    def get_payment(self, payment_id: str) -> dict:
        return self._handle(self.sdk.payment().get(payment_id))

    def get_merchant_order(self, merchant_order_id: str) -> dict:
        return self._handle(self.sdk.merchant_order().get(merchant_order_id))
