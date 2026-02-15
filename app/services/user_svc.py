from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import RegisterIn
from app.utils.security import hash_pw, check_pw, mint_token


async def register(db: AsyncSession, payload: RegisterIn) -> User:
    try:
        existing = await db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")

        user = User(
            name=payload.name,
            email=payload.email,
            hashed_password=hash_pw(payload.password),
            role=payload.role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"registration failed: {str(exc)}",
        )


async def authenticate(db: AsyncSession, email: str, password: str) -> dict:
    try:
        result = await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()

        if not user or not check_pw(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account is deactivated")

        token = mint_token(user.id)
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"authentication error: {str(exc)}",
        )


async def fetch_profile(db: AsyncSession, user_id: str) -> User:
    try:
        result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        return user

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to retrieve profile: {str(exc)}",
        )
