import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from bookstore.database import Base
from bookstore.models.entities import User

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()

def test_table_exists(db):
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    print(f"Tables: {result}")
    assert ('users',) in result
