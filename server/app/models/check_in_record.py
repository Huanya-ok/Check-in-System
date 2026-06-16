from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

if TYPE_CHECKING:
    from app.models.face_profile import FaceProfile


class CheckInRecord(Base):
    __tablename__ = "check_in_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    face_profile_id: Mapped[int] = mapped_column(ForeignKey("face_profiles.id"))
    check_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    similarity_score: Mapped[float] = mapped_column(Float)
    photo_path: Mapped[str] = mapped_column(String(512))

    face_profile: Mapped[FaceProfile] = relationship(back_populates="check_in_records")
