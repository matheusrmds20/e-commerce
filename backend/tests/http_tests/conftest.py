"""Fixtures compartilhadas dos testes HTTP (camada de rotas).

Estrutura segue o padrão do conftest raiz (``backend/tests/conftest.py``):
mocks via ``unittest.mock`` e ``patch`` em context managers.

Estratégia dos testes HTTP:
- O banco de dados é substituído (``get_db``) por um ``Mock`` — nenhuma query real.
- Os serviços são mockados no factory de cada rota (ex.: ``get_auth_service``),
  então os testes validam rota + schema + serialização da resposta.
- Os exception handlers definidos em ``app.api.exceptions`` são registrados no
  app dentro do fixture ``client`` para que os testes validem o CONTRATO de
  erros (400/401/403/404/409/422) — ver RELATORIO_TESTES_HTTP.md: em produção
  o ``app.main`` NÃO chama ``register_exception_handlers``, então todos os
  erros de domínio viram 500 até que isso seja corrigido.
"""
from unittest.mock import Mock

import pytest


@pytest.fixture
def client():
    """TestClient sobre o app real, com banco mockado e handlers de exceção ativos."""
    from fastapi.testclient import TestClient

    from app.api.deps import get_db
    from app.api.exceptions import register_exception_handlers
    from app.main import app

    def _override_db():
        yield Mock(name="db")

    app.dependency_overrides[get_db] = _override_db
    register_exception_handlers(app)

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def patch_service():

    from unittest.mock import patch

    def _patch_service(module: str, factory: str, service: Mock):
        return patch(f"app.api.v1.{module}.{factory}", return_value=service)

    return _patch_service
