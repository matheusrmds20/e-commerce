import logging

import httpx

from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class MelhorEnvioGateway:
    """Gateway HTTP para a API do Melhor Envio.

    Encapsula a chamada ao endpoint de cálculo de fretes
    (``POST /api/v2/me/shipment/calculate``) e normaliza o resultado para
    uma lista de ofertas. Espelha a responsabilidade de ``MercadoPagoGateway``
    (app/integrations/MercadoPago/geteway.py): o service orquestra, o gateway
    só conversa com a API externa.

    Autenticação: header ``Authorization: Bearer <token>`` (OAuth2 gerida no
    painel do Melhor Envio, Integrações > Área Dev).

    Sandbox: usa ``https://sandbox.melhorenvio.com.br`` (só Correios e Jadlog).
    Produção: ``https://www.melhorenvio.com.br`` (config ``MELHOR_ENVIO_SANDBOX``).
    """

    def __init__(self):
        self.api_token = settings.MELHOR_ENVIO_API_TOKEN
        # Segue o padrão de timout curto usado em integrações de terceiros.
        self.timeout = 15.0

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
        """Cotação de fretes.

        Faz ``POST /api/v2/me/shipment/calculate`` e devolve a lista de ofertas
        retornada pela API (ocorrências com ``id``, ``name``, ``price``,
        ``custom_price``, ``delivery_time`` etc.).

        Payload esperado (conforme docs do Melhor Envio):
            {
                "from": {"postal_code": "96020360"},
                "to": {"postal_code": "01018020"},
                "products": [
                    {
                        "id": "1", "width": 11, "height": 17, "length": 11,
                        "weight": 1, "insurance_value": 10.1, "quantity": 1,
                    }
                ],
                "options": {"receipt": False, "own_hand": False},
                "services": "1,2,18",
            }
        """
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
        except httpx.HTTPError as exc:
            logger.error("Melhor Envio erro HTTP: %s", exc)
            raise RuntimeError(f"Melhor Envio error: {exc}") from exc

        if resp.status_code not in range(200, 300):
            logger.error(
                "Melhor Envio erro %s: %s", resp.status_code, resp.text
            )
            raise RuntimeError(
                f"Melhor Envio error: {resp.status_code} {resp.text}"
            )

        data = resp.json()

        # A API retorna a lista de cotações diretamente no corpo, ou sob a
        # chave ``data``/``shipment`` dependendo da versão. Normalizamos para
        # uma lista simples de ofertas.
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for chave in ("data", "shipments", "shipment"):
                valor = data.get(chave)
                if isinstance(valor, list):
                    return valor
            return []

        return []
