import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id: Mapped[str | None] = mapped_column(ForeignKey("components.id", ondelete="SET NULL"), nullable=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "pending_analysis", "analysis_complete", "pending_review", "approved", "rejected", name="change_status_enum"),
        default="draft",
        nullable=False,
    )
    diff_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="change_requests")  # type: ignore[name-defined]
    author: Mapped["User"] = relationship()  # type: ignore[name-defined]
    impacts: Mapped[list["ChangeImpact"]] = relationship(back_populates="change_request", cascade="all, delete-orphan")


class ChangeImpact(Base):
    __tablename__ = "change_impacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    change_request_id: Mapped[str] = mapped_column(ForeignKey("change_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), nullable=False)
    contributor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    detection_method: Mapped[str] = mapped_column(String(50), default="parser", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    affected_lines: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    llm_annotation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    change_request: Mapped["ChangeRequest"] = relationship(back_populates="impacts")
    component: Mapped["Component"] = relationship()  # type: ignore[name-defined]
    contributor: Mapped["User"] = relationship()  # type: ignore[name-defined]


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(
        Enum("change", "approved", "alert", "invite", name="notification_type_enum"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # e.g. { project_id, change_id }
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="notifications")  # type: ignore[name-defined]


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id: Mapped[str | None] = mapped_column(ForeignKey("components.id", ondelete="SET NULL"), nullable=True)
    invited_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invited_email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="contributor", nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "accepted", "declined", name="invite_status_enum"),
        default="pending",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped["Project"] = relationship(back_populates="invites")  # type: ignore[name-defined]
    component: Mapped["Component | None"] = relationship()  # type: ignore[name-defined]
    inviter: Mapped["User"] = relationship()  # type: ignore[name-defined]
