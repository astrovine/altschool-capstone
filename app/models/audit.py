import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[str] = mapped_column(String(36))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
