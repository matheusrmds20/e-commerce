"""Testes do cálculo monetário único (``app.services.pricing``).

Motivação: a regra de desconto estava duplicada em `OrderService.create` e
`_calculate_totals`, e ambas operavam em `float`. Estes testes travam o
comportamento correto em `Decimal` e cobrem os casos que o `float` errava.
"""
from decimal import Decimal

import pytest

from app.api.exceptions import InvalidCouponException
from app.models.coupon import Coupon, DiscountType
from app.services.pricing import (
    calcular_desconto,
    calcular_totais,
    quantize,
    to_decimal,
)


def make_coupon(**kwargs):
    fields = dict(
        id=1,
        code="PROMO10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        min_purchase=None,
        max_discount=None,
        is_active=True,
        used_count=0,
    )
    fields.update(kwargs)
    return Coupon(**fields)


class Item:
    def __init__(self, price, quantity):
        self.price = price
        self.quantity = quantity


class TestToDecimal:
    def test_float_sem_lixo_binario(self):
        """`Decimal(str(0.1))` = 0.1; `Decimal(0.1)` arrastaria 0.1000...55."""
        assert to_decimal(0.1) == Decimal("0.1")

    def test_none_vira_zero(self):
        assert to_decimal(None) == Decimal("0")

    def test_decimal_passa_intacto(self):
        d = Decimal("1.23")
        assert to_decimal(d) is d


class TestCalcularTotaisSemCupom:
    def test_soma_simples(self):
        itens = [Item(50.0, 2)]
        subtotal, desconto, frete, total = calcular_totais(itens)

        assert subtotal == 100.0
        assert desconto == 0.0
        assert frete == 0.0
        assert total == 100.0

    def test_sem_deriva_de_centavos(self):
        """Caso clássico: 0.1 + 0.2 em float != 0.3."""
        itens = [Item(0.1, 1), Item(0.2, 1)]
        subtotal, _, _, total = calcular_totais(itens)

        assert subtotal == 0.3
        assert total == 0.3

    def test_arredonda_para_centavos(self):
        # 3 x 10.005 = 30.015 -> HALF_UP -> 30.02 (float daria 30.014999...).
        itens = [Item(10.005, 3)]
        subtotal, _, _, _ = calcular_totais(itens)

        assert subtotal == 30.02

    def test_aceita_dict(self):
        """O checkout valida itens como dict antes de persistir."""
        subtotal, _, _, total = calcular_totais(
            [{"price": 25.0, "quantity": 4}]
        )

        assert subtotal == 100.0
        assert total == 100.0


class TestCalcularTotaisComCupom:
    def test_percentual(self):
        subtotal, desconto, _, total = calcular_totais(
            [Item(100.0, 1)], coupon=make_coupon(discount_value=10.0)
        )

        assert subtotal == 100.0
        assert desconto == 10.0
        assert total == 90.0

    def test_fixo(self):
        _, desconto, _, total = calcular_totais(
            [Item(100.0, 1)],
            coupon=make_coupon(
                discount_type=DiscountType.FIXED, discount_value=15.0
            ),
        )

        assert desconto == 15.0
        assert total == 85.0

    def test_teto_max_discount(self):
        _, desconto, _, total = calcular_totais(
            [Item(100.0, 1)],
            coupon=make_coupon(discount_value=50.0, max_discount=20.0),
        )

        assert desconto == 20.0
        assert total == 80.0

    def test_desconto_nunca_ultrapassa_subtotal(self):
        """Cupom fixo maior que a compra não deixa o total negativo."""
        _, desconto, _, total = calcular_totais(
            [Item(30.0, 1)],
            coupon=make_coupon(
                discount_type=DiscountType.FIXED, discount_value=100.0
            ),
        )

        assert desconto == 30.0
        assert total == 0.0

    def test_frete_entra_no_total(self):
        subtotal, desconto, frete, total = calcular_totais(
            [Item(100.0, 1)],
            coupon=make_coupon(discount_value=10.0),
            shipping_cost=27.5,
        )

        assert subtotal == 100.0
        assert desconto == 10.0
        assert frete == 27.5
        assert total == 117.5


class TestMinPurchase:
    def test_exatamente_no_limite_e_aceito(self):
        """`100.00 >= 100` em Decimal — em float isso podia falhar por epsilon.

        Especificamente: 10 x 10.0 somado em float pode dar 100.00000000000001,
        mas com preços que geram 99.99999999999999 a comparação erraria.
        """
        itens = [Item(33.33, 3)]  # 99.99
        with pytest.raises(InvalidCouponException):
            calcular_totais(
                itens, coupon=make_coupon(min_purchase=100.0)
            )

        # 100.00 exato passa.
        _, _, _, total = calcular_totais(
            [Item(100.0, 1)], coupon=make_coupon(min_purchase=100.0)
        )
        assert total == 90.0

    def test_abaixo_do_minimo_falha(self):
        with pytest.raises(InvalidCouponException):
            calcular_totais(
                [Item(50.0, 1)], coupon=make_coupon(min_purchase=100.0)
            )

    def test_sem_min_purchase_nao_falha(self):
        _, _, _, total = calcular_totais(
            [Item(1.0, 1)], coupon=make_coupon(min_purchase=None)
        )
        assert total == 0.9


class TestCalcularDescontoIsolado:
    def test_sem_cupom_e_zero(self):
        assert calcular_desconto(Decimal("100"), None) == Decimal("0")

    def test_quantiza_centavos(self):
        # 10% de 33.33 = 3.333 -> 3.33
        coupon = make_coupon(discount_value=10.0)
        assert calcular_desconto(Decimal("33.33"), coupon) == Decimal("3.33")


class TestQuantize:
    def test_half_up(self):
        # 2.345 -> 2.35 (HALF_UP), não 2.34 (banker's rounding).
        assert quantize(Decimal("2.345")) == Decimal("2.35")
