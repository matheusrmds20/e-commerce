from unittest.mock import Mock

import pytest

from app.api.deps import get_db

PREFIX = "/api/v1/health"


@pytest.fixture
def health_db(client):
    """Banco mockado com ``execute`` controlado para o health check."""
    db = Mock(name="db")
    client.app.dependency_overrides[get_db] = lambda: db
    return db


class TestHealth:
    def test_health_ok(self, client, health_db):
        resp = client.get(PREFIX)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["app"]
        assert body["version"]
        assert body["dependencies"] == [{"name": "database", "status": "ok", "detail": None}]

    def test_health_database_down(self, client, health_db):
        health_db.execute.side_effect = RuntimeError("connection refused")

        resp = client.get(PREFIX)

        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "error"
        db_dep = body["dependencies"][0]
        assert db_dep["name"] == "database"
        assert db_dep["status"] == "error"
        # P1-3: em produção o detalhe é mascarado (não vaza internals do banco).
        assert db_dep["detail"] == "unavailable"

    def test_health_database_down_leaks_only_in_debug(self, client, health_db, monkeypatch):
        # Em DEBUG=True o detalhe completo pode ser exposto para troubleshooting.
        from app.api.v1 import health as health_module

        monkeypatch.setattr(health_module.settings, "DEBUG", True)
        health_db.execute.side_effect = RuntimeError("connection refused")

        resp = client.get(PREFIX)
        assert resp.status_code == 503
        db_dep = resp.json()["dependencies"][0]
        assert "connection refused" in db_dep["detail"]

    def test_health_is_public(self, client, health_db):
        # Sem qualquer token/header -> endpoint acessível.
        resp = client.get(PREFIX, headers={})
        assert resp.status_code == 200
