"""Testes do NewsletterService.

Cobre subscribe (novo e-mail, duplicado, normalização), unsubscribe
(inexistente e existente) e list_all (restrição a administradores).
"""
from datetime import datetime
from unittest.mock import Mock

import pytest

from app.models.newsletter import NewsletterSubscriber
from app.models.user import User, UserRole
from app.schemas.newsletter import NewsletterSubscribe, NewsletterUnsubscribe


def make_subscriber(**kwargs):
    fields = dict(id=1, email="reader@example.com", subscribed_at=datetime(2026, 1, 1))
    fields.update(kwargs)
    return NewsletterSubscriber(**fields)


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


def make_admin(**kwargs):
    return make_user(id=99, role=UserRole.ADMIN, **kwargs)


class TestSubscribe:
    def test_subscribe_success(self, newsletter_service, newsletter_repo):
        newsletter_repo.get_by_email.return_value = None
        newsletter_repo.create.side_effect = lambda sub: sub

        result = newsletter_service.subscribe(
            NewsletterSubscribe(email="Reader@Example.com ")
        )

        assert result.email == "reader@example.com"
        created = newsletter_repo.create.call_args[0][0]
        assert created.email == "reader@example.com"

    def test_subscribe_duplicate(self, newsletter_service, newsletter_repo):
        newsletter_repo.get_by_email.return_value = make_subscriber()

        with pytest.raises(ValueError) as exc:
            newsletter_service.subscribe(NewsletterSubscribe(email="reader@example.com"))

        assert "already subscribed" in str(exc.value)
        newsletter_repo.create.assert_not_called()


class TestUnsubscribe:
    def test_unsubscribe_success(self, newsletter_service, newsletter_repo):
        subscriber = make_subscriber()
        newsletter_repo.get_by_email.return_value = subscriber

        result = newsletter_service.unsubscribe(
            NewsletterUnsubscribe(email="reader@example.com")
        )

        assert result is subscriber
        newsletter_repo.delete.assert_called_once_with(subscriber)

    def test_unsubscribe_not_found(self, newsletter_service, newsletter_repo):
        newsletter_repo.get_by_email.return_value = None

        with pytest.raises(ValueError) as exc:
            newsletter_service.unsubscribe(
                NewsletterUnsubscribe(email="ghost@example.com")
            )

        assert "No subscriber found" in str(exc.value)
        newsletter_repo.delete.assert_not_called()


class TestListAll:
    def test_list_all_admin(self, newsletter_service, newsletter_repo):
        subscribers = [make_subscriber(), make_subscriber(id=2, email="a@b.com")]
        newsletter_repo.get_all.return_value = subscribers

        assert newsletter_service.list_all(make_admin()) == subscribers

    def test_list_all_customer_forbidden(self, newsletter_service, newsletter_repo):
        with pytest.raises(ValueError) as exc:
            newsletter_service.list_all(make_user())

        assert "Admin permission required" in str(exc.value)
        newsletter_repo.get_all.assert_not_called()

    def test_list_all_empty(self, newsletter_service, newsletter_repo):
        newsletter_repo.get_all.return_value = []

        with pytest.raises(ValueError) as exc:
            newsletter_service.list_all(make_admin())

        assert "No newsletter subscribers found" in str(exc.value)
