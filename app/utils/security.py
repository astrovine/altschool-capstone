from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from app.config import settings

_hasher = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pw(raw: str) -> str:
    return _hasher.hash(raw)


def check_pw(raw: str, hashed: str) -> bool:
    return _hasher.verify(raw, hashed)


def mint_token(subject: str, expires_minutes: int | None = None) -> str:
    ttl = expires_minutes or settings.access_token_ttl_minutes
    exp = datetime.now(timezone.utc) + timedelta(minutes=ttl)
    payload = {"sub": subject, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return data
    except JWTError:
        return None
