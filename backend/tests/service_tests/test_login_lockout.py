"""Testes do lockout por conta no login (P1-5)."""

from unittest.mock import patch

import pytest

import app.services.login_lockout as lockout
from app.core.config import get_settings


def _set(**kwargs):
    """Ajusta settings de lockout para o teste e restaura depois."""
    settings = get_settings()
    saved = {k: getattr(settings, k) for k in kwargs}
    for k, v in kwargs.items():
        setattr(settings, k, v)
    return saved


def _fake_client(store: dict):
    """Cliente Redis fake com memória (get/set/delete)."""
    class FakeRedis:
        def get(self, key):
            return store.get(key)

        def delete(self, key):
            store.pop(key, None)

        def set(self, key, value, ex=None):  # noqa: A002
            store[key] = value

    return FakeRedis(), store


@pytest.fixture(autouse=True)
def reset_lua_module_cache():
    """Garante teste isolado das settings de lockout."""
    yield
    # restaura defaults
    _set(
        LOGIN_LOCKOUT_ENABLED=True,
        LOGIN_LOCKOUT_MAX_FAILURES=5,
        LOGIN_LOCKOUT_TTL_SECONDS=300,
        LOGIN_LOCKOUT_BASE_SECONDS=300,
        LOGIN_LOCKOUT_MAX_SECONDS=1800,
    )


def test_check_allowed_when_no_previous_failures():
    saved = _set(LOGIN_LOCKOUT_ENABLED=True)
    fake, store = _fake_client({})

    with patch.object(lockout, "_client", return_value=fake):
        decision = lockout.check("user@example.com")

    assert decision.allowed is True
    assert decision.retry_after == 0
    _set(**saved)


def test_record_failure_accumulates_without_locking_under_threshold():
    saved = _set(
        LOGIN_LOCKOUT_ENABLED=True,
        LOGIN_LOCKOUT_MAX_FAILURES=5,
        LOGIN_LOCKOUT_TTL_SECONDS=300,
        LOGIN_LOCKOUT_BASE_SECONDS=300,
    )
    fake, store = _fake_client({})

    with patch.object(lockout, "_client", return_value=fake):
        for _ in range(4):
            decision = lockout.record_failure("user@example.com")

    assert decision.allowed is True
    # 4 falhas, ainda abaixo de 5 -> não trava.
    value = store[next(iter(store))]
    failures, lock_until = lockout._parse(value)
    assert failures == 4
    assert lock_until == 0
    _set(**saved)


def test_lockout_after_threshold():
    saved = _set(
        LOGIN_LOCKOUT_ENABLED=True,
        LOGIN_LOCKOUT_MAX_FAILURES=3,
        LOGIN_LOCKOUT_BASE_SECONDS=300,
        LOGIN_LOCKOUT_MAX_SECONDS=1800,
    )
    fake, store = _fake_client({})

    with patch.object(lockout, "_client", return_value=fake):
        for _ in range(2):
            lockout.record_failure("user@example.com")
        decision = lockout.record_failure("user@example.com")

    assert decision.allowed is False
    assert 0 < decision.retry_after <= 300
    _set(**saved)


def test_check_rejects_when_locked():
    saved = _set(LOGIN_LOCKOUT_ENABLED=True)
    # Força estado de lockout ativo.
    lock_until = lockout._now() + 120
    fake, store = _fake_client({})
    # precisa de uma chave já existente
    from app.services.login_lockout import _key

    with patch.object(lockout, "_client", return_value=fake):
        store[_key("user@example.com")] = f"3:{lock_until}"
        decision = lockout.check("user@example.com")

    assert decision.allowed is False
    assert 0 < decision.retry_after <= 120
    _set(**saved)


def test_record_success_clears_counter():
    saved = _set(LOGIN_LOCKOUT_ENABLED=True)
    fake, store = _fake_client({})
    from app.services.login_lockout import _key

    with patch.object(lockout, "_client", return_value=fake):
        store[_key("user@example.com")] = "2:0"
        lockout.record_success("user@example.com")
        assert lockout._key("user@example.com") not in store
    _set(**saved)


def test_disabled_lockout_allows_everything():
    saved = _set(LOGIN_LOCKOUT_ENABLED=False)

    decision = lockout.check("user@example.com")
    assert decision.allowed is True
    _set(**saved)


def test_fail_open_when_redis_unavailable():
    saved = _set(LOGIN_LOCKOUT_ENABLED=True)

    with patch.object(lockout, "_client", return_value=None):
        assert lockout.check("user@example.com").allowed is True
        assert lockout.record_failure("user@example.com").allowed is True
    _set(**saved)


def test_email_normalized_in_key():
    k1 = lockout._key("User@Example.COM ")
    k2 = lockout._key("user@example.com")
    assert k1 == k2
    assert "user@example.com" not in k1  # não expõe o e-mail na chave
