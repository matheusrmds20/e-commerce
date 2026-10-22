"""Lockout por conta no login (P1-5).

Defesa contra credential stuffing / brute force distribuído: o rate limit por
IP (limiter.py) não cobre um atacante que usa um IP diferente por tentativa.
Aqui controlamos o número de falhas por conta (e-mail), com lockout temporário
e backoff exponencial.

Resiliência (fail-open): se o Redis estiver indisponível, o login NÃO é
bloqueado, priorizando disponibilidade do serviço sobre anti-abuso.
A chave da conta é normalizada por SHA-256 para não expor o e-mail em Redis.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

import redis as redis_client

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()

_KEY_PREFIX = "login:lock"


@dataclass
class LockoutDecision:
    """Resultado da checagem de lockout para uma tentativa de login."""

    allowed: bool
    retry_after: int = 0


def _redis_url() -> str:
    if _settings.LOGIN_LOCKOUT_REDIS_URL:
        return _settings.LOGIN_LOCKOUT_REDIS_URL.strip().strip('"')
    return _settings.CELERY_BROKER_URL.strip().strip('"')


def _client() -> redis_client.Redis | None:
    try:
        return redis_client.from_url(
            _redis_url(),
            socket_connect_timeout=1,
            socket_timeout=2,
            decode_responses=True,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Falha ao conectar no Redis para lockout: %s", exc)
        return None


def _key(email: str) -> str:
    digest = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
    return f"{_KEY_PREFIX}:{digest}"


def _parse(value: str | None) -> tuple[int, int]:
    if not value:
        return 0, 0
    parts = value.split(":")
    if len(parts) != 2:
        return 0, 0
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return 0, 0


def check(email: str) -> LockoutDecision:
    """Retorna se a conta está liberada para nova tentativa."""
    if not _settings.LOGIN_LOCKOUT_ENABLED:
        return LockoutDecision(allowed=True)

    r = _client()
    if r is None:
        return LockoutDecision(allowed=True)

    try:
        value = r.get(_key(email))
        failures, lock_until = _parse(value)
        if lock_until and lock_until > _now():
            return LockoutDecision(
                allowed=False,
                retry_after=lock_until - _now(),
            )
        return LockoutDecision(allowed=True)
    except redis_client.RedisError as exc:
        logger.warning("Redis indisponível no check de lockout: %s", exc)
        return LockoutDecision(allowed=True)


def record_failure(email: str) -> LockoutDecision:
    """Registra uma falha de credencial e aplica lockout/backoff se necessário."""
    if not _settings.LOGIN_LOCKOUT_ENABLED:
        return LockoutDecision(allowed=True)

    r = _client()
    if r is None:  # pragma: no cover
        return LockoutDecision(allowed=True)

    key = _key(email)
    try:
        failures, lock_until = _parse(r.get(key))
        if lock_until and lock_until > _now():
            return LockoutDecision(allowed=False, retry_after=lock_until - _now())

        failures += 1
        max_failures = _settings.LOGIN_LOCKOUT_MAX_FAILURES

        if failures >= max_failures:
            lockout_seconds = min(
                _settings.LOGIN_LOCKOUT_MAX_SECONDS,
                _settings.LOGIN_LOCKOUT_BASE_SECONDS * (failures // max_failures),
            )
            lock_until = _now() + lockout_seconds
            r.set(key, f"{failures}:{lock_until}", ex=lockout_seconds + 60)
            logger.warning(
                "Conta bloqueada por tentativas de login (failures=%s): lockout=%ss",
                failures,
                lockout_seconds,
            )
            return LockoutDecision(allowed=False, retry_after=lockout_seconds)

        r.set(key, f"{failures}:0", ex=_settings.LOGIN_LOCKOUT_TTL_SECONDS)
        return LockoutDecision(allowed=True)
    except redis_client.RedisError as exc:  # pragma: no cover
        logger.warning("Redis indisponível ao registrar falha de login: %s", exc)
        return LockoutDecision(allowed=True)


def record_success(email: str) -> None:
    """Limpa o contador de falhas após login bem-sucedido."""
    if not _settings.LOGIN_LOCKOUT_ENABLED:
        return

    r = _client()
    if r is None:  # pragma: no cover
        return

    try:
        r.delete(_key(email))
    except redis_client.RedisError as exc:  # pragma: no cover
        logger.warning("Redis indisponível ao limpar contador de login: %s", exc)


def _now() -> int:
    import time

    return int(time.time())
