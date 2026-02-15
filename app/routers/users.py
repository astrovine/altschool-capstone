from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import ProfileOut
from app.services import user_svc
from app.utils.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ProfileOut)
async def my_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        profile = await user_svc.fetch_profile(db, current_user.id)
        return profile
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to load profile: {str(exc)}",
        )
