from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EnrollRequest(BaseModel):
    course_id: str


class EnrollmentOut(BaseModel):
    id: str
    user_id: str
    course_id: str
    student_name: Optional[str] = None
    course_title: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EnrollmentListOut(BaseModel):
    items: list[EnrollmentOut]
    total: int
    page: int
    size: int
