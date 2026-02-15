from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.enrollment import EnrollRequest, EnrollmentOut, EnrollmentListOut
from app.schemas.common import Msg
from app.services import enrollment_svc
from app.utils.deps import get_current_user, require_role

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentOut, status_code=201)
async def enroll(
    body: EnrollRequest,
    student: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    try:
        enrollment = await enrollment_svc.enroll(db, student.id, body.course_id)
        return EnrollmentOut(
            id=enrollment.id,
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            student_name=enrollment.student.name if enrollment.student else None,
            course_title=enrollment.course.title if enrollment.course else None,
            created_at=enrollment.created_at,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"enrollment failed: {str(exc)}",
        )


@router.delete("/{enrollment_id}", response_model=Msg)
async def remove_enrollment(
    enrollment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        if current_user.role == "admin":
            await enrollment_svc.admin_remove(db, current_user.id, enrollment_id)
        else:
            await enrollment_svc.deregister(db, current_user.id, enrollment_id)
        return Msg(detail="enrollment removed")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"enrollment removal failed: {str(exc)}",
        )


@router.get("", response_model=EnrollmentListOut)
async def list_enrollments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await enrollment_svc.list_all(db, page, size)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to list enrollments: {str(exc)}",
        )


@router.get("/course/{course_id}", response_model=EnrollmentListOut)
async def enrollments_for_course(
    course_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await enrollment_svc.list_by_course(db, course_id, page, size)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to list course enrollments: {str(exc)}",
        )
