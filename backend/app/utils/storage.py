"""Integração com o Supabase Storage (server-side).

Armazena e recupera os PDFs de comprovante usando a API REST de Storage do
Supabase, em vez de gravar em disco local. Assim worker (Miget) e API (Render)
compartilham o mesmo armazenamento, independentemente da máquina.
"""

import httpx

from app.core.config import get_settings

_MAX_RETRIES = 2


class StorageUnavailableError(Exception):
    """Falha de comunicação com o Supabase Storage."""


def _storage_base() -> str:
    settings = get_settings()
    url = settings.SUPABASE_URL.rstrip("/")
    return f"{url}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}"


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {get_settings().SUPABASE_SERVICE_KEY}",
    }


def upload_receipt(path: str, content: bytes, *, max_retries: int = _MAX_RETRIES) -> None:
    """Faz upload de um objeto sujeito a retry. Lança StorageUnavailableError."""
    headers = _auth_headers()
    headers["Content-Type"] = "application/pdf"
    url = f"{_storage_base()}/{path.lstrip('/')}"

    for attempt in range(max_retries + 1):
        try:
            resp = httpx.post(url, content=content, headers=headers, timeout=30.0)
            if resp.is_success:
                return
            raise StorageUnavailableError(
                f"upload falhou ({resp.status_code}): {resp.text[:200]}"
            )
        except httpx.HTTPError as exc:
            if attempt >= max_retries:
                raise StorageUnavailableError(str(exc)) from exc
    raise StorageUnavailableError("upload falhou")


def download_receipt(path: str) -> bytes:
    """Baixa um objeto do storage. Levanta StorageUnavailableError se não estiver."""
    try:
        resp = httpx.get(
            f"{_storage_base()}/{path.lstrip('/')}",
            headers=_auth_headers(),
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        raise StorageUnavailableError(str(exc)) from exc

    if not resp.is_success:
        raise StorageUnavailableError(
            f"download falhou ({resp.status_code}): {resp.text[:200]}"
        )
    return resp.content
