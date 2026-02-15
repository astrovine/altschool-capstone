from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("student", "admin"):
            raise ValueError("role must be student or admin")
        return v

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("password too short, need at least 6 characters")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileOut(UserOut):
    updated_at: Optional[datetime] = None
