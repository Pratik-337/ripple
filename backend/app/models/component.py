import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Component(Base):
    __tablename__ = "components"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    color: Mapped[str] = mapped_column(String(100), default="from-violet-500 to-purple-600")
    status: Mapped[str] = mapped_column(
        Enum("stable", "flagged", "pending", "locked", name="component_status_enum"),
        default="stable",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped["Project"] = relationship(back_populates="components")  # type: ignore[name-defined]
    files: Mapped[list["ProjectFile"]] = relationship(back_populates="component")
    contributors: Mapped[list["ComponentContributor"]] = relationship(back_populates="component", cascade="all, delete-orphan")
    source_dependencies: Mapped[list["ComponentDependency"]] = relationship(
        foreign_keys="ComponentDependency.source_component_id",
        back_populates="source_component",
        cascade="all, delete-orphan",
    )
    target_dependencies: Mapped[list["ComponentDependency"]] = relationship(
        foreign_keys="ComponentDependency.target_component_id",
        back_populates="target_component",
        cascade="all, delete-orphan",
    )


class ComponentContributor(Base):
    __tablename__ = "component_contributors"

    component_id: Mapped[str] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(
        Enum("owner", "contributor", "read_only", name="contributor_role_enum"),
        default="contributor",
        nullable=False,
    )

    component: Mapped["Component"] = relationship(back_populates="contributors")
    user: Mapped["User"] = relationship()  # type: ignore[name-defined]


class ComponentDependency(Base):
    __tablename__ = "component_dependencies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_component_id: Mapped[str] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), nullable=False)
    target_component_id: Mapped[str] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), nullable=False)

    source_component: Mapped["Component"] = relationship(foreign_keys=[source_component_id], back_populates="source_dependencies")
    target_component: Mapped["Component"] = relationship(foreign_keys=[target_component_id], back_populates="target_dependencies")


class ProjectFile(Base):
    __tablename__ = "project_files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id: Mapped[str | None] = mapped_column(ForeignKey("components.id", ondelete="SET NULL"), nullable=True, index=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="TypeScript")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_symbols: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped["Project"] = relationship(back_populates="files")  # type: ignore[name-defined]
    component: Mapped["Component | None"] = relationship(back_populates="files")
    drafts: Mapped[list["FileDraft"]] = relationship(back_populates="file", cascade="all, delete-orphan")


class FileDraft(Base):
    __tablename__ = "file_drafts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id: Mapped[str] = mapped_column(ForeignKey("project_files.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    s3_draft_key: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    file: Mapped["ProjectFile"] = relationship(back_populates="drafts")
    author: Mapped["User"] = relationship()  # type: ignore[name-defined]


class ProjectSnapshot(Base):
    __tablename__ = "project_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    s3_manifest_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped["Project"] = relationship(back_populates="snapshots")  # type: ignore[name-defined]
