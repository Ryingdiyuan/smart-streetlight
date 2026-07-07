"""Cloud database engine and session factory.

Reads CLOUD_MYSQL_* settings from env and provides a separate SQLAlchemy engine
for one-way cloud-to-local database synchronization.
"""

from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

cloud_engine = create_engine(
    settings.cloud_database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
)

CloudSessionLocal = sessionmaker(
    bind=cloud_engine,
    autoflush=False,
    autocommit=False,
)


def get_cloud_db():
    """Yield a cloud database session (FastAPI dependency compatible)."""
    db = CloudSessionLocal()
    try:
        yield db
    finally:
        db.close()
