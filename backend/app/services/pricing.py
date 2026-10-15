
from decimal import ROUND_HALF_UP, Decimal

# Quantizador para centavos: 2 casas, arredondamento comercial.
CENTAVO = Decimal("0.01")


def to_decimal(value) -> Decimal:


    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize(valor: Decimal) -> Decimal:

    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_desconto(subtotal: Decimal, coupon) -> Decimal:

    if coupon is None:
        return Decimal("0")

    tipo = getattr(coupon, "discount_type", None)

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

    if isinstance(item, dict):
        return item.get(campo)
    return getattr(item, campo, None)
