from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from .config import settings

# Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Sync Engine (for direct export and sync operations)
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False
)
SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def init_db():
    """
    Synchronously initialize all database tables.
    """
    from . import models  # Ensure all models are registered
    Base.metadata.create_all(bind=sync_engine)
