import sys
import os
import pytest

# Ensure root directory is on sys.path for backend imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.database import Base
from backend.services.ingestion_service import IngestionService

TEST_DB_URL = "sqlite:///./test_pharma.db"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_pharma.db"):
        try:
            os.remove("test_pharma.db")
        except OSError:
            pass

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def sample_dataset(db_session):
    with open("data/sample_pharma_sales.csv", "rb") as f:
        content = f.read()
    dataset = IngestionService.process_csv_file(db_session, content, "sample_pharma_sales.csv")
    return dataset
