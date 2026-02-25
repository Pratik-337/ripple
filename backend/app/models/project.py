import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    strictness_mode: Mapped[str] = mapped_column(
        Enum("visibility", "soft", "full", name="strictness_mode_enum"),
        default="visibility",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("draft", "active", "archived", name="project_status_enum"),
        default="draft",
        nullable=False,
    )
    source_type: Mapped[str | None] = mapped_column(
        Enum("github", "folder", name="source_type_enum"),
        nullable=True,
    )
    github_repo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner: Mapped["User"] = relationship(back_populates="projects")  # type: ignore[name-defined]
    components: Mapped[list["Component"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    files: Mapped[list["ProjectFile"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    change_requests: Mapped[list["ChangeRequest"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    invites: Mapped[list["Invite"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    snapshots: Mapped[list["ProjectSnapshot"]] = relationship(back_populates="project", cascade="all, delete-orphan")
