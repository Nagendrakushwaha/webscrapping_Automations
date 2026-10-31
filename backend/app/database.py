from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

engine = create_engine(
    settings.SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Keep aliases for backwards compatibility
SyncSessionLocal = SessionLocal

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes all database tables and auto-migrates missing columns on SQLite.
    """
    from . import models
    Base.metadata.create_all(bind=engine)

    try:
        with engine.connect() as conn:
            cursor = conn.exec_driver_sql("PRAGMA table_info(companies)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            
            for col in models.Company.__table__.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(engine.dialect)
                    try:
                        conn.exec_driver_sql(f"ALTER TABLE companies ADD COLUMN {col.name} {col_type}")
                        conn.commit()
                    except Exception:
                        pass
    except Exception:
        pass
