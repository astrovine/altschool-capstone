import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student = relationship("User", back_populates="enrollments", lazy="selectin")
    course = relationship("Course", back_populates="enrollments", lazy="selectin")
