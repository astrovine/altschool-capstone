import pytest
from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_get_profile(client, student_in_db, student_token):
    resp = await client.get("/users/me", headers=auth_header(student_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "jane@test.com"
    assert data["name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_get_profile_no_auth(client):
    resp = await client.get("/users/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_profile_bad_token(client):
    resp = await client.get("/users/me", headers=auth_header("totally.garbage.token"))
    assert resp.status_code == 401
