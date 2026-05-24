from datetime import datetime
from sqlalchemy import String, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("permission IN (0, 1, 2)", name="ck_users_permission"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    permission: Mapped[int] = mapped_column(default=0, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    personal_profile: Mapped[str | None] = mapped_column(nullable=True)