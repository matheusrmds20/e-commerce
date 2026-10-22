from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

_settings = get_settings()


def _client_key(request: Request) -> str:
    return get_remote_address(request)


limiter = Limiter(
    key_func=_client_key,
    default_limits=[_settings.RATE_LIMIT_DEFAULT],
    storage_uri=_settings.RATE_LIMIT_STORAGE_URI,
    enabled=_settings.RATE_LIMIT_ENABLED,
    headers_enabled=_settings.RATE_LIMIT_HEADERS_ENABLED,
)
