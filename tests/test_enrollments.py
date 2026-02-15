import pytest
from tests.conftest import auth_header, TestSession
from app.models.audit import AuditLog
from sqlalchemy import select


@pytest.mark.asyncio
async def test_enroll_success(client, student_in_db, student_token, sample_course):
    resp = await client.post(
        "/enrollments",
        json={"course_id": sample_course.id},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["course_id"] == sample_course.id
    assert data["user_id"] == student_in_db.id


@pytest.mark.asyncio
async def test_enroll_creates_audit_log(client, student_in_db, student_token, sample_course):
    await client.post(
        "/enrollments",
        json={"course_id": sample_course.id},
        headers=auth_header(student_token),
    )
    async with TestSession() as db:
        result = await db.execute(select(AuditLog).where(AuditLog.action == "enrolled"))
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.actor_id == student_in_db.id


@pytest.mark.asyncio
async def test_enroll_duplicate_rejected(client, student_in_db, student_token, sample_course):
    await client.post("/enrollments", json={"course_id": sample_course.id}, headers=auth_header(student_token))
    resp = await client.post("/enrollments", json={"course_id": sample_course.id}, headers=auth_header(student_token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_enroll_full_course(client, student_in_db, student_token, full_course):
    resp = await client.post(
        "/enrollments",
        json={"course_id": full_course.id},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 400
    assert "full" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_enroll_inactive_course(client, student_in_db, student_token, inactive_course):
    resp = await client.post(
        "/enrollments",
        json={"course_id": inactive_course.id},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 400
    assert "not active" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_enroll_nonexistent_course(client, student_in_db, student_token):
    resp = await client.post(
        "/enrollments",
        json={"course_id": "does-not-exist"},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_enroll_admin_forbidden(client, admin_in_db, admin_token, sample_course):
    resp = await client.post(
        "/enrollments",
        json={"course_id": sample_course.id},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_student_deregister(client, student_in_db, student_token, sample_course):
    enroll_resp = await client.post(
        "/enrollments",
        json={"course_id": sample_course.id},
        headers=auth_header(student_token),
    )
    enrollment_id = enroll_resp.json()["id"]

    resp = await client.delete(f"/enrollments/{enrollment_id}", headers=auth_header(student_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_student_deregister_creates_audit(client, student_in_db, student_token, sample_course):
    enroll_resp = await client.post(
        "/enrollments",
        json={"course_id": sample_course.id},
        headers=auth_header(student_token),
    )
    enrollment_id = enroll_resp.json()["id"]
    await client.delete(f"/enrollments/{enrollment_id}", headers=auth_header(student_token))

    async with TestSession() as db:
        result = await db.execute(select(AuditLog).where(AuditLog.action == "deregistered"))
        log = result.scalar_one_or_none()
        assert log is not None


@pytest.mark.asyncio
async def test_student_cannot_deregister_others(client, student_in_db, student_token, admin_in_db, admin_token, sample_course):
    second_student_resp = await client.post("/auth/register", json={
        "name": "Other Student",
        "email": "other@test.com",
        "password": "otherpw1",
        "role": "student",
    })
    other_id = second_student_resp.json()["id"]
    from app.utils.security import mint_token as _mt
    other_token = _mt(other_id)

    enroll_resp = await client.post(
        "/enrollments",
        json={"course_id": sample_course.id},
        headers=auth_header(other_token),
    )
    enrollment_id = enroll_resp.json()["id"]

    resp = await client.delete(f"/enrollments/{enrollment_id}", headers=auth_header(student_token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_remove_student(client, student_in_db, student_token, admin_in_db, admin_token, sample_course):
    enroll_resp = await client.post(
        "/enrollments",
        json={"course_id": sample_course.id},
        headers=auth_header(student_token),
    )
    enrollment_id = enroll_resp.json()["id"]

    resp = await client.delete(f"/enrollments/{enrollment_id}", headers=auth_header(admin_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_remove_creates_audit(client, student_in_db, student_token, admin_in_db, admin_token, sample_course):
    enroll_resp = await client.post(
        "/enrollments",
        json={"course_id": sample_course.id},
        headers=auth_header(student_token),
    )
    enrollment_id = enroll_resp.json()["id"]
    await client.delete(f"/enrollments/{enrollment_id}", headers=auth_header(admin_token))

    async with TestSession() as db:
        result = await db.execute(select(AuditLog).where(AuditLog.action == "removed_by_admin"))
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.actor_id == admin_in_db.id


@pytest.mark.asyncio
async def test_admin_list_all_enrollments(client, student_in_db, student_token, admin_in_db, admin_token, sample_course):
    await client.post("/enrollments", json={"course_id": sample_course.id}, headers=auth_header(student_token))

    resp = await client.get("/enrollments", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_admin_list_enrollments_by_course(client, student_in_db, student_token, admin_in_db, admin_token, sample_course):
    await client.post("/enrollments", json={"course_id": sample_course.id}, headers=auth_header(student_token))

    resp = await client.get(f"/enrollments/course/{sample_course.id}", headers=auth_header(admin_token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert all(e["course_id"] == sample_course.id for e in items)


@pytest.mark.asyncio
async def test_student_cannot_list_all_enrollments(client, student_in_db, student_token):
    resp = await client.get("/enrollments", headers=auth_header(student_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_enrollment_list_pagination(client, student_in_db, student_token, admin_in_db, admin_token):
    for i in range(3):
        await client.post(
            "/courses",
            json={"title": f"Paginated {i}", "code": f"PAG{i:02d}", "capacity": 50},
            headers=auth_header(admin_token),
        )

    courses_resp = await client.get("/courses?size=100")
    for c in courses_resp.json()["items"]:
        await client.post("/enrollments", json={"course_id": c["id"]}, headers=auth_header(student_token))

    resp = await client.get("/enrollments?page=1&size=2", headers=auth_header(admin_token))
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 3


@pytest.mark.asyncio
async def test_no_auth_enroll(client, sample_course):
    resp = await client.post("/enrollments", json={"course_id": sample_course.id})
    assert resp.status_code in (401, 403)
