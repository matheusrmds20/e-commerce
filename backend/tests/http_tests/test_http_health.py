"""Testes HTTP da rota /api/v1/health.

Cobre o health check da API e do banco de dados:
- Sucesso: banco respondendo -> 200 com status "ok" e dependency database "ok".
- Falha: banco indisponível -> 503 com status "error" e dependency "error".
- Formato: campos do HealthResponse (app, version, dependencies).

NOTA: /health é PÚBLICO (sem token) — ferramentas de infra não têm autenticação.
"""
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
        # Por padrão Mock não lança; ``SELECT 1`` considera-se bem-sucedido.
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
        assert "connection refused" in db_dep["detail"]

    def test_health_is_public(self, client, health_db):
        # Sem qualquer token/header -> endpoint acessível.
        resp = client.get(PREFIX, headers={})
        assert resp.status_code == 200
