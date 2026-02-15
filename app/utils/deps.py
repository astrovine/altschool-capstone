from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.utils.security import decode_token

_bearer = HTTPBearer()


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token_data = decode_token(creds.credentials)
    if token_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token")

    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed token")

    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account deactivated")

    return user


def require_role(needed: str):
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != needed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"requires {needed} role",
            )
        return current_user
    return _checker
