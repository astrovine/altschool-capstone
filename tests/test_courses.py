import pytest
from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_list_courses_empty(client):
    resp = await client.get("/courses")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_courses_with_data(client, sample_course):
    resp = await client.get("/courses")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["code"] == "PY101"


@pytest.mark.asyncio
async def test_list_courses_pagination(client, admin_in_db, admin_token):
    for i in range(5):
        await client.post(
            "/courses",
            json={"title": f"Course {i}", "code": f"C{i:03d}", "capacity": 10},
            headers=auth_header(admin_token),
        )
    resp = await client.get("/courses?page=1&size=2")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_courses_filter_by_title(client, admin_in_db, admin_token):
    await client.post("/courses", json={"title": "Machine Learning", "code": "ML01", "capacity": 30}, headers=auth_header(admin_token))
    await client.post("/courses", json={"title": "Web Dev", "code": "WB01", "capacity": 25}, headers=auth_header(admin_token))

    resp = await client.get("/courses?title=machine")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Machine Learning"


@pytest.mark.asyncio
async def test_get_course_by_id(client, sample_course):
    resp = await client.get(f"/courses/{sample_course.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sample_course.id


@pytest.mark.asyncio
async def test_get_course_not_found(client):
    resp = await client.get("/courses/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_course_admin(client, admin_in_db, admin_token):
    resp = await client.post(
        "/courses",
        json={"title": "Data Structures", "code": "DS200", "capacity": 40},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "DS200"


@pytest.mark.asyncio
async def test_create_course_student_forbidden(client, student_in_db, student_token):
    resp = await client.post(
        "/courses",
        json={"title": "Nope", "code": "NO01", "capacity": 10},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_course_duplicate_code(client, admin_in_db, admin_token, sample_course):
    resp = await client.post(
        "/courses",
        json={"title": "Another", "code": "PY101", "capacity": 20},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_course_zero_capacity(client, admin_in_db, admin_token):
    resp = await client.post(
        "/courses",
        json={"title": "Empty", "code": "EMP01", "capacity": 0},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_course_negative_capacity(client, admin_in_db, admin_token):
    resp = await client.post(
        "/courses",
        json={"title": "Negative", "code": "NEG01", "capacity": -5},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_course(client, admin_in_db, admin_token, sample_course):
    resp = await client.put(
        f"/courses/{sample_course.id}",
        json={"title": "Advanced Python"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Advanced Python"


@pytest.mark.asyncio
async def test_update_course_student_forbidden(client, student_in_db, student_token, sample_course):
    resp = await client.put(
        f"/courses/{sample_course.id}",
        json={"title": "Hacked"},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_activate_deactivate_course(client, admin_in_db, admin_token, sample_course):
    resp = await client.patch(
        f"/courses/{sample_course.id}/activate?active=false",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    resp2 = await client.patch(
        f"/courses/{sample_course.id}/activate?active=true",
        headers=auth_header(admin_token),
    )
    assert resp2.json()["is_active"] is True


@pytest.mark.asyncio
async def test_delete_course_soft(client, admin_in_db, admin_token, sample_course):
    resp = await client.delete(f"/courses/{sample_course.id}", headers=auth_header(admin_token))
    assert resp.status_code == 200

    resp2 = await client.get(f"/courses/{sample_course.id}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_course_student_forbidden(client, student_in_db, student_token, sample_course):
    resp = await client.delete(f"/courses/{sample_course.id}", headers=auth_header(student_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_inactive_courses_hidden_from_public_list(client, inactive_course):
    resp = await client.get("/courses")
    data = resp.json()
    assert data["total"] == 0
