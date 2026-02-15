from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.audit import AuditLog
