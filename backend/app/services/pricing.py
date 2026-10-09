"""Cálculo monetário do pedido — fonte única de verdade.

Motivo: a regra de desconto estava **duplicada** em ``OrderService.create`` e
``OrderService._calculate_totals``, e ambas operavam em ``float``. Isso gerava
dois problemas:

1. Deriva de centavos: ``0.1 + 0.2 != 0.3``; um subtotal podia chegar ao
   provedor de pagamento como ``89.99999999999999`` e ser cobrado diferente do
   total registrado no pedido.
2. Comparações de ``min_purchase`` falhando por epsilon (``100.00000000000001
   >= 100`` quando o esperado era igualdade).

Aqui todo o cálculo é feito em ``Decimal`` e arredondado para 2 casas com
``ROUND_HALF_UP`` (arredondamento comercial, o que o cliente espera ao ver o
preço). A conversão para ``float`` só acontece na saída, para manter o contrato
dos modelos/schemas atuais (colunas ``Float``).
"""
from decimal import ROUND_HALF_UP, Decimal

# Quantizador para centavos: 2 casas, arredondamento comercial.
CENTAVO = Decimal("0.01")


def to_decimal(value) -> Decimal:
    """Converte ``float``/``int``/``str``/``Decimal``/``None`` para ``Decimal``.

    ``str(value)`` é usado em vez de ``Decimal(value)`` para floats: evita
    arrastar a representação binária (``Decimal(0.1)`` vira
    ``0.1000000000000000055511...``; ``Decimal(str(0.1))`` vira ``0.1``).
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize(valor: Decimal) -> Decimal:
    """Arredonda para centavos (HALF_UP)."""
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_desconto(subtotal: Decimal, coupon) -> Decimal:
    """Calcula o desconto do cupom sobre o subtotal (em centavos).

    Aplica, nesta ordem:
    - percentual (``discount_type == 'percentage'``) ou valor fixo;
    - teto de ``max_discount``, quando houver.

    Nunca devolve desconto maior que o subtotal (o total não pode ficar
    negativo).
    """
    if coupon is None:
        return Decimal("0")

    tipo = getattr(coupon, "discount_type", None)
    # ``DiscountType`` é StrEnum: compara tanto com o enum quanto com a string.
    if tipo == "percentage" or getattr(tipo, "value", None) == "percentage":
        desconto = subtotal * (to_decimal(coupon.discount_value) / Decimal("100"))
    else:
        desconto = to_decimal(coupon.discount_value)

    if coupon.max_discount is not None:
        desconto = min(desconto, to_decimal(coupon.max_discount))

    if desconto < 0:
        desconto = Decimal("0")

    return quantize(min(desconto, subtotal))


def calcular_totais(
    itens,
    coupon=None,
    shipping_cost=0,
):
    """Calcula ``(subtotal, discount_amount, shipping_cost, total)``.

    ``itens`` é qualquer iterável de objetos com ``price`` e ``quantity``
    (tanto ``OrderItem`` quanto os dicts validados no checkout).

    Levanta ``InvalidCouponException`` quando o subtotal não atinge
    ``min_purchase``. A comparação é feita em ``Decimal`` (ambos quantizados),
    então ``100.00 >= 100`` é verdadeiro sem surpresa de ponto flutuante.
    """
    # Import local: evita ciclo entre o pacote de exceções e este helper.
    from app.api.exceptions import InvalidCouponException

    subtotal = Decimal("0")
    for item in itens:
        preco = to_decimal(_get(item, "price"))
        quantidade = int(_get(item, "quantity") or 0)
        subtotal += preco * quantidade
    subtotal = quantize(subtotal)

    if coupon is not None:
        minimo = to_decimal(coupon.min_purchase)
        if subtotal < minimo:
            raise InvalidCouponException(
                f"O cupom '{coupon.code}' exige uma compra mínima "
                f"de {coupon.min_purchase}."
            )

    desconto = calcular_desconto(subtotal, coupon)
    frete = quantize(to_decimal(shipping_cost))

    total = quantize(subtotal - desconto + frete)

    return (
        float(subtotal),
        float(desconto),
        float(frete),
        float(total),
    )


def _get(item, campo):
    """Lê ``campo`` de um objeto (atributo) ou dict."""
    if isinstance(item, dict):
        return item.get(campo)
    return getattr(item, campo, None)
