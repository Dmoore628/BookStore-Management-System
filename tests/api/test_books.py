import pytest
from httpx import AsyncClient
from bookstore.models.entities import User
from bookstore.models.enums import Role
from bookstore.security import hash_password

@pytest.fixture
def owner_client(client, db):
    user = User(username="owner", password_hash=hash_password("password"), role=Role.OWNER)
    db.add(user)
    db.commit()
    # Need to simulate login or just mock the dependency if possible.
    # Given the session middleware, login is required.
    client.post("/api/auth/login", json={"username": "owner", "password": "password"}).result()
    return client

@pytest.mark.asyncio
async def test_list_books(client: AsyncClient, db):
    response = await client.get("/api/books/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_add_book_unauthorized(client: AsyncClient):
    response = await client.post("/api/books/", json={"title": "New Book", "author": "Author", "price": "10.00", "quantity": 1})
    assert response.status_code == 401
