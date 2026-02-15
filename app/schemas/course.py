from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class CourseCreate(BaseModel):
    title: str
    code: str
    capacity: int

    @field_validator("capacity")
    @classmethod
    def cap_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("capacity must be greater than zero")
        return v


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    code: Optional[str] = None
    capacity: Optional[int] = None

    @field_validator("capacity")
    @classmethod
    def cap_positive_if_given(cls, v):
        if v is not None and v <= 0:
            raise ValueError("capacity must be greater than zero")
        return v


class CourseOut(BaseModel):
    id: str
    title: str
    code: str
    capacity: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CourseListOut(BaseModel):
    items: list[CourseOut]
    total: int
    page: int
    size: int
