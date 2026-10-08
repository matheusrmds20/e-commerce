import mercadopago
from mercadopago.config import RequestOptions

from app.core.config import get_settings

settings = get_settings()

# Timeout curto nas chamadas ao Mercado Pago. O SDK padrão usa 60s (e tem
# retries em alguns recursos), o que segura thread/conexão por tempo demais
# quando o MP está lento/fora. Aqui aplicamos um teto global de 8s.
MP_TIMEOUT_SECONDS = 8.0


class MercadoPagoGateway:

    def __init__(self):
        self.sdk = mercadopago.SDK(
            settings.MERCADO_PAGO_ACCESS_TOKEN,
            request_options=RequestOptions(
                connection_timeout=MP_TIMEOUT_SECONDS,
                max_retries=1,
            ),
        )

    def create_preference(self, data: dict) -> dict:
        response = self.sdk.preference().create(data)

        if response["status"] not in range(200, 300):
            raise RuntimeError(
                f"Mercado Pago error: {response}"
            )

        return response["response"]

    def get_preference(self, preference_id: str) -> dict:
        response = self.sdk.preference().get(preference_id)

        if response["status"] not in range(200, 300):
            raise RuntimeError(
                f"Mercado Pago error: {response}"
            )

        return response["response"]

    def get_payment(self, payment_id: str) -> dict:
        response = self.sdk.payment().get(payment_id)

        if response["status"] not in range(200, 300):
            raise RuntimeError(
                f"Mercado Pago error: {response}"
            )

        return response["response"]

    def get_merchant_order(self, merchant_order_id: str) -> dict:
        """Busca uma merchant_order (agrega vários payments de um checkout)."""
        response = self.sdk.merchant_order().get(merchant_order_id)

        if response["status"] not in range(200, 300):
            raise RuntimeError(
                f"Mercado Pago error: {response}"
            )

        return response["response"]
