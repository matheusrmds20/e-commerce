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
