import logging

import httpx

from app.api.exceptions import (
    IntegrationRejectedError,
    IntegrationUnavailableError,
)
from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

PROVIDER_NAME = "melhor_envio"


class MelhorEnvioGateway:


    def __init__(self):
        self.api_token = settings.MELHOR_ENVIO_API_TOKEN
        self.timeout = settings.MELHOR_ENVIO_TIMEOUT

    @property
    def base_url(self) -> str:
        if settings.MELHOR_ENVIO_SANDBOX:
            return "https://sandbox.melhorenvio.com.br"
        return "https://www.melhorenvio.com.br"

    def _headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
            "User-Agent": "bookcommerce-api",
        }

    def calculate_shipping(self, payload: dict) -> list[dict]:

        if not self.api_token:
            logger.error("MELHOR_ENVIO_API_TOKEN não configurado.")
            return []

        url = f"{self.base_url}/api/v2/me/shipment/calculate"

        try:
            resp = httpx.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            logger.error("Melhor Envio timeout: %s", exc)
            raise IntegrationUnavailableError(PROVIDER_NAME, "timeout") from exc
        except httpx.HTTPError as exc:
            logger.error("Melhor Envio erro HTTP: %s", exc)
            raise IntegrationUnavailableError(PROVIDER_NAME, str(exc)) from exc

        if 500 <= resp.status_code < 600:
            logger.error("Melhor Envio erro %s: %s", resp.status_code, resp.text)
            raise IntegrationUnavailableError(
                PROVIDER_NAME, str(resp.status_code)
            )

        if resp.status_code >= 400:
            logger.error("Melhor Envio erro %s: %s", resp.status_code, resp.text)
            raise IntegrationRejectedError(
                PROVIDER_NAME, f"{resp.status_code} {resp.text}"
            )

        data = resp.json()


        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for chave in ("data", "shipments", "shipment"):
                valor = data.get(chave)
                if isinstance(valor, list):
                    return valor
            return []

        return []
