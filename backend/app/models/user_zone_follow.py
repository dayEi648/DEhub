from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, Integer, UniqueConstraint, Index, desc
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserZoneFollow(Base):
    __tablename__ = "user_zone_follows"

    __table_args__ = (
        UniqueConstraint("user_id", "zone_id", name="uq_user_zone_follows"),
        Index("idx_uzf_user", "user_id", desc("created_at")),
        Index("idx_uzf_zone", "zone_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("forum_zones.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
