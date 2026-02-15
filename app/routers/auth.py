from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import RegisterIn, UserOut, LoginIn
from app.schemas.common import TokenResponse
from app.services import user_svc
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterIn, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_svc.register(db, body)
        return user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"unexpected error during registration: {str(exc)}",
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginIn, db: AsyncSession = Depends(get_db)):
    try:
        result = await user_svc.authenticate(db, body.email, body.password)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"unexpected error during login: {str(exc)}",
        )
