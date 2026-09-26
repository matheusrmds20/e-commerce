import pytest

from app.models.coupon import Coupon, DiscountType
from app.models.user import User, UserRole
from app.models.user_coupon import UserCoupon
from app.schemas.user_coupon import UserCouponCreate


def make_user(**kwargs):
    fields = dict(
        id=1,
        email="user@example.com",
        full_name="John Doe",
        password_hash="hashed",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    fields.update(kwargs)
    return User(**fields)


def make_coupon(**kwargs):
    from datetime import datetime, timedelta

    fields = dict(
        id=1,
        code="PAPIRO10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        valid_until=datetime.now() + timedelta(days=30),
        is_active=True,
    )
    fields.update(kwargs)
    return Coupon(**fields)


def make_user_coupon(**kwargs):
    fields = dict(id=1, user_id=1, coupon_id=1)
    fields.update(kwargs)
    return UserCoupon(**fields)


class TestGet:
    def test_get_by_id_success(self, user_coupon_service, user_coupon_repo):
        link = make_user_coupon()
        user_coupon_repo.get_by_id.return_value = link

        assert user_coupon_service.get_by_id(1, 1) is link

    def test_get_by_id_not_found(self, user_coupon_service, user_coupon_repo):
        user_coupon_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            user_coupon_service.get_by_id(99, 1)

        assert str(exc.value) == "No user coupon found with id 99"

    def test_get_by_id_not_owned(self, user_coupon_service, user_coupon_repo):
        user_coupon_repo.get_by_id.return_value = make_user_coupon(user_id=2)

        with pytest.raises(ValueError) as exc:
            user_coupon_service.get_by_id(1, 1)

        assert str(exc.value) == "User coupon is not owned by user"

    def test_get_by_user_id_success(self, user_coupon_service, user_repo, user_coupon_repo):
        user_repo.get_by_id.return_value = make_user()
        links = [make_user_coupon()]
        user_coupon_repo.get_by_user_id.return_value = links

        assert user_coupon_service.get_by_user_id(1) == links

    def test_get_by_user_id_user_not_found(self, user_coupon_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            user_coupon_service.get_by_user_id(1)

        assert str(exc.value) == "No user found with id 1"

    def test_get_by_coupon_id_success(self, user_coupon_service, coupon_repo, user_coupon_repo):
        coupon_repo.get_by_id.return_value = make_coupon()
        links = [make_user_coupon()]
        user_coupon_repo.get_by_coupon_id.return_value = links

        assert user_coupon_service.get_by_coupon_id(1) == links

    def test_get_by_coupon_id_not_found(self, user_coupon_service, coupon_repo):
        coupon_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            user_coupon_service.get_by_coupon_id(99)

        assert str(exc.value) == "No coupon found with id 99"

    def test_get_all(self, user_coupon_service, user_coupon_repo):
        links = [make_user_coupon()]
        user_coupon_repo.get_all.return_value = links

        assert user_coupon_service.get_all() == links

    def test_list_coupons_by_user_success(self, user_coupon_service, user_repo, user_coupon_repo):
        user_repo.get_by_id.return_value = make_user()
        coupon = make_coupon()
        link = make_user_coupon()
        link.coupons = coupon
        user_coupon_repo.get_by_user_id.return_value = [link]

        assert user_coupon_service.list_coupons_by_user(1) == [coupon]

    def test_list_coupons_by_user_not_found(self, user_coupon_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            user_coupon_service.list_coupons_by_user(1)

        assert str(exc.value) == "No user found with id 1"


class TestCreate:
    def test_success(self, user_coupon_service, user_repo, coupon_repo, user_coupon_repo):
        user_repo.get_by_id.return_value = make_user()
        coupon_repo.get_by_id.return_value = make_coupon()
        user_coupon_repo.get_by_user_and_coupon.return_value = None
        link = make_user_coupon()
        user_coupon_repo.create.return_value = link

        result = user_coupon_service.create(
            UserCouponCreate(user_id=1, coupon_id=1)
        )

        assert result is link
        created = user_coupon_repo.create.call_args[0][0]
        assert created.user_id == 1
        assert created.coupon_id == 1

    def test_user_not_found(self, user_coupon_service, user_repo):
        user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            user_coupon_service.create(UserCouponCreate(user_id=1, coupon_id=1))

        assert str(exc.value) == "No user found with id 1"

    def test_coupon_not_found(self, user_coupon_service, user_repo, coupon_repo):
        user_repo.get_by_id.return_value = make_user()
        coupon_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            user_coupon_service.create(UserCouponCreate(user_id=1, coupon_id=99))

        assert str(exc.value) == "No coupon found with id 99"

    def test_duplicate(self, user_coupon_service, user_repo, coupon_repo, user_coupon_repo):
        user_repo.get_by_id.return_value = make_user()
        coupon_repo.get_by_id.return_value = make_coupon()
        user_coupon_repo.get_by_user_and_coupon.return_value = make_user_coupon()

        with pytest.raises(ValueError) as exc:
            user_coupon_service.create(UserCouponCreate(user_id=1, coupon_id=1))

        assert "already has coupon" in str(exc.value)


class TestDelete:
    def test_success(self, user_coupon_service, user_coupon_repo):
        link = make_user_coupon()
        user_coupon_repo.get_by_id.return_value = link

        result = user_coupon_service.delete(1, 1)

        assert result is link
        user_coupon_repo.delete.assert_called_once_with(link)

    def test_not_found(self, user_coupon_service, user_coupon_repo):
        user_coupon_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc:
            user_coupon_service.delete(99, 1)

        assert str(exc.value) == "No user coupon found with id 99"

    def test_not_owned(self, user_coupon_service, user_coupon_repo):
        user_coupon_repo.get_by_id.return_value = make_user_coupon(user_id=2)

        with pytest.raises(ValueError) as exc:
            user_coupon_service.delete(1, 1)

        assert str(exc.value) == "User coupon is not owned by user"
