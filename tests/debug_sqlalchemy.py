import pytest
from sqlalchemy import create_engine
from bookstore.database import Base
from bookstore.models.entities import User
from bookstore.models.enums import Role
from bookstore.security import hash_password
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = User(username="testuser", password_hash=hash_password("password"), role=Role.CASHIER)
    session.add(user)
    session.commit()
    return session

def test_user_query(db_session):
    user = db_session.query(User).filter_by(username="testuser").first()
    assert user is not None
    assert user.username == "testuser"
