from unittest.mock import patch

import httpx
import pytest

from app.utils import storage
from app.utils.storage import StorageUnavailableError


def test_upload_receipt_sucesso():
    with patch("app.utils.storage.httpx.post") as post:
        resp = httpx.Response(200, content=b"ok")
        resp.request = httpx.Request("POST", "http://test")
        post.return_value = resp

        storage.upload_receipt("comprovantes/comprovante_order_7.pdf", b"%PDF")

    post.assert_called_once()
    kwargs = post.call_args
    assert "comprovantes/comprovante_order_7.pdf" in kwargs[0][0]


def test_upload_receipt_falha_status():
    with patch("app.utils.storage.httpx.post") as post:
        resp = httpx.Response(401, content=b"{}")
        resp.request = httpx.Request("POST", "http://test")
        post.return_value = resp

        with pytest.raises(StorageUnavailableError):
            storage.upload_receipt("x.pdf", b"%PDF")


def test_upload_receipt_retry_em_falha_de_rede():
    with patch("app.utils.storage.httpx.post", side_effect=httpx.ConnectError("boom")):
        with pytest.raises(StorageUnavailableError):
            storage.upload_receipt("x.pdf", b"%PDF")


def test_download_receipt_sucesso():
    with patch("app.utils.storage.httpx.get") as get:
        resp = httpx.Response(200, content=b"%PDF-1.4")
        resp.request = httpx.Request("GET", "http://test")
        get.return_value = resp

        content = storage.download_receipt("comprovantes/c.pdf")

    assert content == b"%PDF-1.4"


def test_download_receipt_nao_encontrado():
    with patch("app.utils.storage.httpx.get") as get:
        resp = httpx.Response(404, content=b"{}")
        resp.request = httpx.Request("GET", "http://test")
        get.return_value = resp

        with pytest.raises(StorageUnavailableError):
            storage.download_receipt("comprovantes/c.pdf")


def test_download_receipt_erro_de_rede():
    with patch("app.utils.storage.httpx.get", side_effect=httpx.ConnectError("boom")):
        with pytest.raises(StorageUnavailableError):
            storage.download_receipt("comprovantes/c.pdf")
