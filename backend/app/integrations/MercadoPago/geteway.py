import mercadopago

from app.core.config import get_settings

settings = get_settings()


class MercadoPagoGateway:

    def __init__(self):
        self.sdk = mercadopago.SDK(
            settings.MERCADO_PAGO_ACCESS_TOKEN
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
