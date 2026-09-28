from datetime import datetime, timedelta

import pytest

from app.models.coupon import Coupon, DiscountType
from app.schemas.coupon import CouponCreate, CouponUpdate


def future():
    return datetime.now() + timedelta(days=1)


def make_coupon(**kwargs):
    fields = dict(
        id=1,
        code="PROMO10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        valid_until=future(),
        is_active=True,
    )
    fields.update(kwargs)
    return Coupon(**fields)


def create_payload(**kwargs):
    fields = dict(code="PROMO10", discount_value=10.0, valid_until=future())
    fields.update(kwargs)
    return CouponCreate(**fields)


@pytest.mark.parametrize(
    "method,repo_method,lookup",
    [
        ("get_all", "get_all", None),
    ],
)
def test_get_list_success(coupon_service, coupon_repo, method, repo_method, lookup):
    coupons = [make_coupon()]
    getattr(coupon_repo, repo_method).return_value = coupons

    if lookup is None:
        result = getattr(coupon_service, method)()
    else:
        result = getattr(coupon_service, method)(lookup)

    assert result == coupons


@pytest.mark.parametrize(
    "method,repo_method,lookup,message",
    [
        ("get_all", "get_all", None, "No coupons found"),
    ],
)
def test_get_list_empty(coupon_service, coupon_repo, method, repo_method, lookup, message):
    getattr(coupon_repo, repo_method).return_value = []

    with pytest.raises(ValueError) as exc:
        if lookup is None:
            getattr(coupon_service, method)()
        else:
            getattr(coupon_service, method)(lookup)

    assert str(exc.value) == message


class TestCreate:
    def test_create_success(self, coupon_service, coupon_repo):
        coupon = make_coupon()
        coupon_repo.get_by_code.return_value = None
        coupon_repo.create.return_value = coupon

        result = coupon_service.create(create_payload())

        assert result is coupon
        created = coupon_repo.create.call_args[0][0]
        assert created.code == "PROMO10"
        assert created.discount_value == 10.0

    def test_create_code_already_exists(self, coupon_service, coupon_repo):
        coupon_repo.get_by_code.return_value = make_coupon()

        with pytest.raises(ValueError) as exc:
            coupon_service.create(create_payload())

        assert "already exists" in str(exc.value)

    def test_create_product_not_found(self, coupon_service, coupon_repo, product_repo):
        coupon_repo.get_by_code.return_value = None
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            coupon_service.create(create_payload(product_id=99))

        assert str(exc.value) == "No product found with id 99"


class TestUpdate:
    def test_update_success(self, coupon_service, coupon_repo):
        coupon = make_coupon()
        coupon_repo.get_by_id.return_value = coupon
        coupon_repo.get_by_code.return_value = None
        coupon_repo.update.return_value = coupon

        result = coupon_service.update(1, CouponUpdate(code="NOVO10"))

        assert result is coupon
        assert coupon.code == "NOVO10"
        coupon_repo.update.assert_called_once_with(coupon)

    def test_update_not_found(self, coupon_service, coupon_repo):
        coupon_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            coupon_service.update(1, CouponUpdate(code="NOVO10"))

        assert str(exc.value) == "No coupon found with id 1"

    def test_update_code_conflict(self, coupon_service, coupon_repo):
        coupon = make_coupon()
        other = make_coupon(id=2, code="NOVO10")
        coupon_repo.get_by_id.return_value = coupon
        coupon_repo.get_by_code.return_value = other

        with pytest.raises(ValueError) as exc:
            coupon_service.update(1, CouponUpdate(code="NOVO10"))

        assert "already exists" in str(exc.value)

    def test_update_product_not_found(self, coupon_service, coupon_repo, product_repo):
        coupon_repo.get_by_id.return_value = make_coupon()
        coupon_repo.get_by_code.return_value = None
        product_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            coupon_service.update(1, CouponUpdate(product_id=99))

        assert str(exc.value) == "No product found with id 99"


class TestDelete:
    def test_delete_success(self, coupon_service, coupon_repo):
        coupon = make_coupon()
        coupon_repo.get_by_id.return_value = coupon

        result = coupon_service.delete(1)

        assert result is coupon
        coupon_repo.delete.assert_called_once_with(coupon)

    def test_delete_not_found(self, coupon_service, coupon_repo):
        coupon_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            coupon_service.delete(1)

        assert str(exc.value) == "No coupon found with id 1"
