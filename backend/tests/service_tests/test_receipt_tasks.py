"""Testes das tasks de geração do comprovante PDF e do gerador de PDF.

Cobre:
- ``pdf.generate_receipt``: gera um arquivo PDF válido a partir do payload.
- ``receipt_tasks.generate_order_receipt`` (task Celery): busca o pedido,
  chama o gerador e persiste o caminho em ``orders.receipt_path``.
- Retry/erro quando o pedido não existe.

O banco é substituído (mock de ``SessionLocal``) e a função de geração de PDF
é patchada no teste da task — nada é gravado de verdade no banco nem no disco
salvo o teste isolado do próprio gerador.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.utils import pdf
from app.utils.receipt_tasks import generate_order_receipt


def _payload(order_id=7):
    return {
        "order_id": order_id,
        "created_at": "04/10/2026 14:00",
        "status": "completed",
        "customer_name": "João",
        "customer_email": "joao@example.com",
        "address": "Rua A, 10 - Centro, São Paulo/SP - 01001000",
        "subtotal": 100.0,
        "shipping_cost": 10.0,
        "discount_amount": 5.0,
        "total": 105.0,
        "items": [{"name": "Livro X", "quantity": 2, "price": 50.0}],
    }


class TestGenerateReceipt:
    def test_gera_arquivo_pdf_valido(self, tmp_path):
        out = tmp_path / "receipts" / "comprovante_order_7.pdf"
        result = pdf.generate_receipt(_payload(), out)

        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0
        assert out.read_bytes()[:5] == b"%PDF-"

    def test_cria_diretorio_inexistente(self, tmp_path):
        out = tmp_path / "sub" / "outro" / "recibo.pdf"
        pdf.generate_receipt(_payload(), out)
        assert out.exists()


class TestGenerateOrderReceipt:
    def _mock_session_with_order(self, order, db):
        """Configura o mock de query do order no SessionLocal mockado."""
        query = MagicMock()
        query.options.return_value = query
        query.filter.return_value = query
        query.first.return_value = order
        db.query.return_value = query
        return query

    def test_sucesso_chama_gerador_e_persiste_caminho(self, tmp_path):
        from datetime import datetime

        order = MagicMock()
        order.id = 7
        order.created_at = datetime(2026, 10, 4, 14, 0)
        order.status = "completed"
        order.subtotal = 100.0
        order.shipping_cost = 10.0
        order.discount_amount = 5.0
        order.total = 105.0
        order.receipt_path = None
        order.users.full_name = "João"
        order.users.email = "joao@example.com"
        order.addresses.street = "Rua A"
        order.addresses.number = "10"
        order.addresses.neighborhood = "Centro"
        order.addresses.city = "São Paulo"
        order.addresses.state = "SP"
        order.addresses.zip_code = "01001000"
        item = MagicMock()
        item.products.title = "Livro X"
        item.quantity = 2
        item.price = 50.0
        order.order_items = [item]

        db = MagicMock()
        self._mock_session_with_order(order, db)

        fake_path = tmp_path / "comprovante_order_7.pdf"
        captured = {}

        def _fake_generate(payload, path):
            captured["payload"] = payload
            # Simula: a task seta receipt_path com o caminho "gerado".
            order.receipt_path = str(fake_path)
            return fake_path

        with patch("app.utils.receipt_tasks.SessionLocal", return_value=db), patch(
            "app.utils.receipt_tasks.generate_receipt", side_effect=_fake_generate
        ), patch("app.utils.receipt_tasks.get_settings") as get_settings:
            get_settings.return_value.COMPROVANTES_DIR = "comprovantes"
            # ``generate_order_receipt.run`` injeta o payload ``order_id``;
            # como o caminho de sucesso nunca chama ``self.retry``, o self real
            # da task não interfere no teste.
            result = generate_order_receipt.run("7")

        assert result["status"] == "success"
        assert result["order_id"] == 7
        assert result["receipt_path"] == str(fake_path)
        assert captured["payload"]["total"] == 105.0
        assert captured["payload"]["items"][0] == {
            "name": "Livro X",
            "quantity": 2,
            "price": 50.0,
        }
        db.commit.assert_called_once()
        db.close.assert_called_once()

    def test_pedido_inexistente_retry(self):
        """Pedido não encontrado → a task agenda retry (via ``self.retry``)."""
        db = MagicMock()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None

        retried = {"chamado": False}

        def _fake_retry(**kwargs):
            retried["chamado"] = True
            raise RuntimeError("retry programado")

        with patch("app.utils.receipt_tasks.SessionLocal", return_value=db), \
             patch.object(
                 generate_order_receipt, "retry", side_effect=_fake_retry
             ):
            with pytest.raises(RuntimeError, match="retry programado"):
                generate_order_receipt.run("999")

        assert retried["chamado"] is True
        db.rollback.assert_called_once()
        db.close.assert_called_once()
