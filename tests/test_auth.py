import pytest
from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_register_student(client):
    resp = await client.post("/auth/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "password1",
        "role": "student",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "student"
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_admin(client):
    resp = await client.post("/auth/register", json={
        "name": "Bob Admin",
        "email": "bob@admin.com",
        "password": "adminpass",
        "role": "admin",
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"name": "First", "email": "dup@test.com", "password": "abcdef1", "role": "student"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_role(client):
    resp = await client.post("/auth/register", json={
        "name": "Hacker",
        "email": "hack@test.com",
        "password": "whatever1",
        "role": "superuser",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    resp = await client.post("/auth/register", json={
        "name": "Short",
        "email": "short@test.com",
        "password": "ab",
        "role": "student",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, student_in_db):
    resp = await client.post("/auth/login", json={
        "email": "jane@test.com",
        "password": "secret123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, student_in_db):
    resp = await client.post("/auth/login", json={
        "email": "jane@test.com",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@nowhere.com",
        "password": "doesntmatter",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client, inactive_user_in_db):
    resp = await client.post("/auth/login", json={
        "email": "ghost@test.com",
        "password": "nope1234",
    })
    assert resp.status_code == 403
