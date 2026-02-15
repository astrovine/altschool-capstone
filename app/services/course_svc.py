from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sa_func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from datetime import datetime, timezone

from app.models.course import Course


async def list_courses(db: AsyncSession, page: int, size: int, title_filter: str | None = None, active_only: bool = True):
    try:
        q = select(Course).where(Course.deleted_at.is_(None))
        count_q = select(sa_func.count()).select_from(Course).where(Course.deleted_at.is_(None))

        if active_only:
            q = q.where(Course.is_active == True)
            count_q = count_q.where(Course.is_active == True)

        if title_filter:
            q = q.where(Course.title.ilike(f"%{title_filter}%"))
            count_q = count_q.where(Course.title.ilike(f"%{title_filter}%"))

        total_result = await db.execute(count_q)
        total = total_result.scalar()

        offset = (page - 1) * size
        q = q.offset(offset).limit(size).order_by(Course.created_at.desc())
        result = await db.execute(q)
        courses = result.scalars().all()

        return {"items": courses, "total": total, "page": page, "size": size}

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to list courses: {str(exc)}",
        )


async def get_course(db: AsyncSession, course_id: str) -> Course:
    try:
        result = await db.execute(select(Course).where(Course.id == course_id, Course.deleted_at.is_(None)))
        course = result.scalar_one_or_none()
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="course not found")
        return course

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to fetch course: {str(exc)}",
        )


async def create_course(db: AsyncSession, title: str, code: str, capacity: int) -> Course:
    try:
        dup_check = await db.execute(select(Course).where(Course.code == code))
        if dup_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="course code already exists")

        course = Course(title=title, code=code, capacity=capacity)
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="course code already exists")
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"course creation failed: {str(exc)}",
        )


async def update_course(db: AsyncSession, course_id: str, **fields) -> Course:
    try:
        course = await get_course(db, course_id)

        if "code" in fields and fields["code"] is not None and fields["code"] != course.code:
            dup = await db.execute(select(Course).where(Course.code == fields["code"], Course.id != course_id))
            if dup.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="course code already taken")

        for k, v in fields.items():
            if v is not None:
                setattr(course, k, v)

        await db.commit()
        await db.refresh(course)
        return course

    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="course code conflict during update")
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"course update failed: {str(exc)}",
        )


async def toggle_active(db: AsyncSession, course_id: str, active: bool) -> Course:
    try:
        course = await get_course(db, course_id)
        course.is_active = active
        await db.commit()
        await db.refresh(course)
        return course

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"toggle active failed: {str(exc)}",
        )


async def soft_delete(db: AsyncSession, course_id: str) -> None:
    try:
        course = await get_course(db, course_id)
        course.deleted_at = datetime.now(timezone.utc)
        course.is_active = False
        await db.commit()

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"soft delete failed: {str(exc)}",
        )
