from datetime import datetime

from app.api.exceptions import (
    ForbiddenException,
    OrderNotFoundException,
    ShippingCalculationException,
)
from app.core.config import get_settings
from app.integrations.MelhorEnvio.gateway import MelhorEnvioGateway
from app.models.order import OrderStatus
from app.repositories.address_repo import AddressRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.order_repo import OrderRepository
from app.services.pricing import quantize as centavos
from app.services.pricing import to_decimal

settings = get_settings()


class ShippingService:
    """Orquestra a cotação de frete via Melhor Envio.

    Responsabilidades (espelhando a divisão de `PaymentService`):
    - montar o payload de cotação a partir dos itens/endereço do pedido;
    - chamar o `MelhorEnvioGateway`;
    - normalizar as ofertas e apontar a melhor (menor preço);
    - aplicar o frete escolhido no pedido (grava ``shipping_cost`` e recalcula
      ``total``).
    """

    def __init__(self, db):
        self.order_repo = OrderRepository(db)
        self.address_repo = AddressRepository(db)
        self.cart_repo = CartRepository(db)
        self.gateway = MelhorEnvioGateway()
        self.session = db

    # ------------------------------------------------------------------
    # Cálculo
    # ------------------------------------------------------------------

    def quote(self, user_id: int, postal_code: str) -> dict:
        """Cota o frete a partir do CARTão do usuário, sem criar pedido.

        Usado antes do checkout para o cliente ver/escolher as opções reais de
        frete. Não baixa estoque nem limpa o carrinho (ao contrário de criar um
        pedido).
        """
        cart_items = self.cart_repo.get_by_user_id_cart_items(user_id)
        if not cart_items:
            return self._fallback_quote(postal_code, "carrinho vazio")

        # Verifica se a integração está pronta para cotar de verdade.
        if not self._is_configured():
            return self._fallback_quote(postal_code, "frete ainda não configurado")

        products = self._build_products(cart_items)
        if products is None:
            return self._fallback_quote(
                postal_code, "produtos sem peso/dimensões cadastrados"
            )

        payload = {
            "from": {"postal_code": settings.MELHOR_ENVIO_ORIGIN_ZIP},
            "to": {"postal_code": self._normalize_zip(postal_code)},
            "products": products,
            "options": {"receipt": False, "own_hand": False},
        }

        try:
            raw_offers = self.gateway.calculate_shipping(payload)
        except RuntimeError as exc:
            raise ShippingCalculationException(str(exc)) from exc

        if not raw_offers:
            return self._fallback_quote(postal_code, "nenhuma oferta retornada")

        offers = [self._normalize_offer(o) for o in raw_offers]
        offers = [o for o in offers if o is not None]
        if not offers:
            return self._fallback_quote(postal_code, "nenhuma oferta válida")

        return {
            "postal_code": self._normalize_zip(postal_code),
            "offers": offers,
            "best_offer_index": self._best_offer_index(offers),
            "is_real": True,
        }

    def _fallback_quote(self, postal_code: str, motivo: str) -> dict:
        return {
            "postal_code": self._normalize_zip(postal_code),
            "offers": [],
            "best_offer_index": None,
            "is_real": False,
            "fallback_reason": motivo,
        }

    def calculate(self, order_id: int, user_id: int) -> dict:
        order = self._get_owned_order(order_id, user_id)

        address = self.address_repo.get_by_id(order.address_id)
        if address is None:
            raise ShippingCalculationException(
                "O endereço de entrega do pedido não foi encontrado."
            )

        items = self.order_repo.get_with_items_products(order.id)

        # Verifica se a integração está pronta para cotar de verdade.
        if not self._is_configured():
            return self._fallback(order.id, "frete ainda não configurado")

        if not items:
            raise ShippingCalculationException(
                "O pedido não possui itens para calcular o frete."
            )

        # Valida que todos os itens têm peso/dimensões e monta o payload.
        products = self._build_products(items)
        if products is None:
            return self._fallback(
                order.id,
                "produtos sem peso/dimensões cadastrados",
            )

        payload = {
            "from": {"postal_code": settings.MELHOR_ENVIO_ORIGIN_ZIP},
            "to": {"postal_code": self._normalize_zip(address.zip_code)},
            "products": products,
            "options": {"receipt": False, "own_hand": False},
        }

        try:
            raw_offers = self.gateway.calculate_shipping(payload)
        except RuntimeError as exc:
            raise ShippingCalculationException(str(exc)) from exc

        if not raw_offers:
            return self._fallback(order.id, "nenhuma oferta retornada")

        offers = [self._normalize_offer(o) for o in raw_offers]
        offers = [o for o in offers if o is not None]

        best_index = self._best_offer_index(offers)

        return {
            "order_id": order.id,
            "offers": offers,
            "best_offer_index": best_index,
            "is_real": True,
        }

    # ------------------------------------------------------------------
    # Aplicar no pedido
    # ------------------------------------------------------------------

    def apply_to_order(
        self,
        order_id: int,
        user_id: int,
        price: float,
        delivery_time: int | None = None,
        status: OrderStatus | None = None,
    ) -> dict:
        """Grava o frete escolhido no pedido e recalcula o total.

        ``delivery_time`` não é persistido (não existe coluna no ``Order``);
        é aceito apenas para consistência do contrato.
        """
        # A transação é aberta antes de qualquer query: no SQLAlchemy 2.0, uma
        # autocommit=False já inicia transação implícita ao consultar; abrir o
        # `with session.begin()` depois de uma query lançaria
        # "transaction is already begun".
        with self.session.begin():
            order = self._get_owned_order(order_id, user_id)

            # Recalcula `total = subtotal - desconto + frete` com o helper
            # único (Decimal, arredondado a centavos). Antes a soma era feita
            # direto em float nos atributos do pedido.
            order.shipping_cost = round(float(price), 2)
            order.total = float(
                centavos(
                    to_decimal(order.subtotal)
                    - to_decimal(order.discount_amount)
                    + to_decimal(order.shipping_cost)
                )
            )
            order.updated_at = datetime.now()

            # Atualiza o status de envio quando solicitado (ex.: marcando o
            # pedido em processamento/enviado).
            if status is not None:
                order.status = status

            self.session.flush()

            return {
                "order_id": order.id,
                "applied": True,
                "shipping_cost": order.shipping_cost,
                "total": order.total,
                "status": (
                    order.status.value
                    if hasattr(order.status, "value")
                    else str(order.status)
                ),
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_owned_order(self, order_id: int, user_id: int):
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundException()
        if order.user_id != user_id:
            raise ForbiddenException(
                "Este pedido pertence a outro usuário.",
                code="ORDER_FORBIDDEN",
            )
        return order

    def _is_configured(self) -> bool:
        token = settings.MELHOR_ENVIO_API_TOKEN
        origin = settings.MELHOR_ENVIO_ORIGIN_ZIP
        return bool(token and origin)

    def _fallback(self, order_id: int, motivo: str) -> dict:
        """Retorna um resultado de frete "grátis" (R$ 0) quando a cotação real
        não é possível (token/CEP ausente ou produtos sem peso/dimensões).

        Mantém o fluxo funcionando e sinaliza ``is_real=False`` para o front
        saber que o valor é provisional.
        """
        return {
            "order_id": order_id,
            "offers": [],
            "best_offer_index": None,
            "is_real": False,
            "fallback_reason": motivo,
        }

    def _build_products(self, items) -> list[dict] | None:
        """Monta o payload ``products``. Retorna ``None`` se houver item sem
        peso/dimensões (cotação não pode ser feita).

        Aceita tanto ``OrderItem`` (atributo ``product``/``.products``) quanto
        ``CartItem`` (atributo ``product``).
        """
        products = []
        for item in items:
            product = (
                getattr(item, "product", None)
                or getattr(item, "products", None)
            )
            if product is None:
                return None
            weight = getattr(product, "weight_kg", None)
            height = getattr(product, "height_cm", None)
            width = getattr(product, "width_cm", None)
            length = getattr(product, "length_cm", None)
            if not all(
                v is not None and float(v) > 0
                for v in (weight, height, width, length)
            ):
                return None

            products.append(
                {
                    "id": str(product.id),
                    "width": float(width),
                    "height": float(height),
                    "length": float(length),
                    "weight": float(weight),
                    # CartItem não tem ``price``; reusa o preço do produto.
                    "insurance_value": float(
                        getattr(item, "price", None) or product.price
                    ),
                    "quantity": int(item.quantity),
                }
            )

        return products

    def _normalize_offer(self, raw: dict):
        """Converte uma oferta bruta da API na estrutura do schema.

        Usa ``custom_price``/``custom_delivery_time`` quando presentes (refletem
        as taxas/descontos configurados na conta), senão cai nos valores
        originais.
        """
        if not raw or not raw.get("id"):
            return None

        price = raw.get("custom_price", raw.get("price"))
        if price is None:
            return None

        name = raw.get("name") or ""
        company = (raw.get("company") or {}).get("name")
        delivery = raw.get("custom_delivery_time", raw.get("delivery_time"))

        return {
            "service_id": str(raw["id"]),
            "name": name,
            "company_name": company,
            "price": float(price),
            "delivery_time": int(delivery) if delivery not in (None, "") else None,
            "delivery_time_text": raw.get("delivery_time_text"),
        }

    def _best_offer_index(self, offers: list[dict]) -> int | None:
        if not offers:
            return None
        menores = min(o["price"] for o in offers)
        for i, o in enumerate(offers):
            if o["price"] == menores:
                return i
        return 0

    @staticmethod
    def _normalize_zip(zip_code: str) -> str:
        """Remove caracteres não numéricos do CEP."""
        if not zip_code:
            return ""
        return "".join(ch for ch in zip_code if ch.isdigit())
