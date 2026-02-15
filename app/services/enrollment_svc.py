from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sa_func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import json

from app.models.enrollment import Enrollment
from app.models.course import Course
from app.models.audit import AuditLog


async def _write_audit(db: AsyncSession, entity_id: str, action: str, actor_id: str, extra: dict | None = None):
    try:
        log = AuditLog(
            entity_type="enrollment",
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            details=json.dumps(extra) if extra else None,
        )
        db.add(log)
    except Exception:
        pass


async def enroll(db: AsyncSession, user_id: str, course_id: str) -> Enrollment:
    try:
        course_result = await db.execute(select(Course).where(Course.id == course_id, Course.deleted_at.is_(None)))
        course = course_result.scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="course not found")

        if not course.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="course is not active")

        dup = await db.execute(
            select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already enrolled in this course")

        count_result = await db.execute(
            select(sa_func.count()).select_from(Enrollment).where(Enrollment.course_id == course_id)
        )
        current_count = count_result.scalar()
        if current_count >= course.capacity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="course is full")

        enrollment = Enrollment(user_id=user_id, course_id=course_id)
        db.add(enrollment)
        await db.flush()

        await _write_audit(db, enrollment.id, "enrolled", user_id, {"course_id": course_id})
        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="enrollment conflict, possibly duplicate")
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"enrollment failed: {str(exc)}",
        )


async def deregister(db: AsyncSession, user_id: str, enrollment_id: str) -> None:
    try:
        result = await db.execute(
            select(Enrollment).where(Enrollment.id == enrollment_id, Enrollment.user_id == user_id)
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="enrollment not found")

        await _write_audit(db, enrollment.id, "deregistered", user_id, {"course_id": enrollment.course_id})
        await db.delete(enrollment)
        await db.commit()

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"deregistration failed: {str(exc)}",
        )


async def admin_remove(db: AsyncSession, admin_id: str, enrollment_id: str) -> None:
    try:
        result = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="enrollment not found")

        await _write_audit(
            db, enrollment.id, "removed_by_admin", admin_id,
            {"course_id": enrollment.course_id, "student_id": enrollment.user_id},
        )
        await db.delete(enrollment)
        await db.commit()

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"admin removal failed: {str(exc)}",
        )


async def list_all(db: AsyncSession, page: int, size: int):
    try:
        count_q = select(sa_func.count()).select_from(Enrollment)
        total_result = await db.execute(count_q)
        total = total_result.scalar()

        offset = (page - 1) * size
        q = select(Enrollment).offset(offset).limit(size).order_by(Enrollment.created_at.desc())
        result = await db.execute(q)
        enrollments = result.scalars().all()

        items = []
        for e in enrollments:
            items.append({
                "id": e.id,
                "user_id": e.user_id,
                "course_id": e.course_id,
                "student_name": e.student.name if e.student else None,
                "course_title": e.course.title if e.course else None,
                "created_at": e.created_at,
            })

        return {"items": items, "total": total, "page": page, "size": size}

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to list enrollments: {str(exc)}",
        )


async def list_by_course(db: AsyncSession, course_id: str, page: int, size: int):
    try:
        count_q = select(sa_func.count()).select_from(Enrollment).where(Enrollment.course_id == course_id)
        total_result = await db.execute(count_q)
        total = total_result.scalar()

        offset = (page - 1) * size
        q = (
            select(Enrollment)
            .where(Enrollment.course_id == course_id)
            .offset(offset)
            .limit(size)
            .order_by(Enrollment.created_at.desc())
        )
        result = await db.execute(q)
        enrollments = result.scalars().all()

        items = []
        for e in enrollments:
            items.append({
                "id": e.id,
                "user_id": e.user_id,
                "course_id": e.course_id,
                "student_name": e.student.name if e.student else None,
                "course_title": e.course.title if e.course else None,
                "created_at": e.created_at,
            })

        return {"items": items, "total": total, "page": page, "size": size}

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to list course enrollments: {str(exc)}",
        )
