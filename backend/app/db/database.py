from sqlalchemy import create_engine
from app.core.config import get_settings
from sqlalchemy.orm import sessionmaker

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)
