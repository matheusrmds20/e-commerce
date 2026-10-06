
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.schemas.common import DependencyHealth, HealthResponse

health_router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]

settings = get_settings()


def _check_database(db: Session) -> DependencyHealth:
    try:
        db.execute(text("SELECT 1"))
        return DependencyHealth(name="database", status="ok")
    except Exception as exc: 
        return DependencyHealth(
            name="database",
            status="error",
            detail=f"{type(exc).__name__}: {exc}",
        )


@health_router.get(
    "/",
    response_model=HealthResponse,
    summary="Health check da API e do banco de dados",
    tags=["health"],
)

def health_check(response: Response, db: DbSession):
    """Retorna o status da API e do banco de dados."""
    database = _check_database(db)

    all_ok = database.status == "ok"

    response.status_code = (
        status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return HealthResponse(
        status="ok" if all_ok else "error",
        app=settings.APP_NAME,
        version="1.0.0",
        dependencies=[database],
    )
