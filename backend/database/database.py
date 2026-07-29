import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Detect Vercel serverless read-only environment
IS_VERCEL = os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None or not os.access(".", os.W_OK)

if IS_VERCEL:
    DEFAULT_DB_URL = "sqlite:////tmp/pharma_analytics.db"
else:
    DEFAULT_DB_URL = "sqlite:///./pharma_analytics.db"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

try:
    if DATABASE_URL.startswith("postgresql"):
        import psycopg2
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    else:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
except Exception:
    DATABASE_URL = "sqlite:////tmp/pharma_analytics.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for API endpoints to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
