from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut, CourseListOut
from app.schemas.common import Msg
from app.services import course_svc
from app.utils.deps import require_role

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=CourseListOut)
async def list_courses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    title: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await course_svc.list_courses(db, page, size, title_filter=title)
        return data
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to list courses: {str(exc)}",
        )


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await course_svc.get_course(db, course_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to get course: {str(exc)}",
        )


@router.post("", response_model=CourseOut, status_code=201)
async def create_course(
    body: CourseCreate,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await course_svc.create_course(db, body.title, body.code, body.capacity)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"course creation failed: {str(exc)}",
        )


@router.put("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: str,
    body: CourseUpdate,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    try:
        updates = body.model_dump(exclude_unset=True)
        return await course_svc.update_course(db, course_id, **updates)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"course update failed: {str(exc)}",
        )


@router.patch("/{course_id}/activate", response_model=CourseOut)
async def activate_course(
    course_id: str,
    active: bool = Query(...),
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await course_svc.toggle_active(db, course_id, active)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"activation toggle failed: {str(exc)}",
        )


@router.delete("/{course_id}", response_model=Msg)
async def delete_course(
    course_id: str,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    try:
        await course_svc.soft_delete(db, course_id)
        return Msg(detail="course deleted")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"course deletion failed: {str(exc)}",
        )
