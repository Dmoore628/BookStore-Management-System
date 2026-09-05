import pytest
from httpx import AsyncClient
from bookstore.models.entities import User
from bookstore.models.enums import Role
from bookstore.security import hash_password

@pytest.mark.asyncio
async def test_auth_login_success(client: AsyncClient, db):
    user = User(username="testuser", password_hash=hash_password("password"), role=Role.CASHIER)
    db.add(user)
    db.commit()
    
    response = await client.post("/api/auth/login", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200
    assert response.json()["message"] == "Logged in"

@pytest.mark.asyncio
async def test_auth_login_failure(client: AsyncClient):
    response = await client.post("/api/auth/login", json={"username": "wronguser", "password": "password"})
    assert response.status_code == 401
