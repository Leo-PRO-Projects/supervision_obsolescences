from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class CriticityLevel(str, Enum):
    low = "faible"
    medium = "moyenne"
    high = "haute"
    critical = "critique"


class RemediationStatus(str, Enum):
    not_planned = "non_planifie"
    planned = "planifie"
    in_progress = "en_cours"
    done = "termine"


class UserRole(str, Enum):
    reader = "reader"
    contributor = "contributor"
    admin = "admin"


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    team: Mapped[Optional[str]] = mapped_column(String(255))
    contact: Mapped[Optional[str]] = mapped_column(String(255))

    applications: Mapped[List["Application"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ApplicationStatus(str, Enum):
    active = "active"
    deprecated = "obsolète"
    retired = "retirée"


class Application(TimestampMixin, Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    owner: Mapped[Optional[str]] = mapped_column(String(255))
    criticity: Mapped[CriticityLevel] = mapped_column(SQLEnum(CriticityLevel), default=CriticityLevel.medium)
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus), default=ApplicationStatus.active, nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="applications")
    versions: Mapped[List["Version"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    dependencies: Mapped[List["Dependency"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    timelines: Mapped[List["TimelineEvent"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    action_plans: Mapped[List["ActionPlan"]] = relationship(back_populates="application", cascade="all, delete-orphan")


class Version(TimestampMixin, Base):
    __tablename__ = "versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    number: Mapped[str] = mapped_column(String(100), nullable=False)
    end_of_support: Mapped[Optional[date]] = mapped_column(Date)
    end_of_contract: Mapped[Optional[date]] = mapped_column(Date)
    vendor_eos: Mapped[Optional[date]] = mapped_column(Date)
    remediation_status: Mapped[RemediationStatus] = mapped_column(
        SQLEnum(RemediationStatus), default=RemediationStatus.not_planned, nullable=False
    )
    comment: Mapped[Optional[str]] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="versions")


class DependencyCategory(str, Enum):
    language = "langage"
    runtime = "runtime"
    os = "os"
    middleware = "middleware"
    library = "librairie"
    other = "autre"


class Dependency(TimestampMixin, Base):
    __tablename__ = "dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[DependencyCategory] = mapped_column(SQLEnum(DependencyCategory), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(255))
    vendor: Mapped[Optional[str]] = mapped_column(String(255))
    end_of_support: Mapped[Optional[date]] = mapped_column(Date)
    normalized_name: Mapped[Optional[str]] = mapped_column(String(255))

    application: Mapped[Application] = relationship(back_populates="dependencies")


class NotificationType(str, Enum):
    email = "email"
    teams = "teams"


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), nullable=False)
    recipients: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.reader, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    comments: Mapped[List["Comment"]] = relationship(back_populates="author")
    action_plans: Mapped[List["ActionPlan"]] = relationship(back_populates="owner")


class TechnologyLifecycle(TimestampMixin, Base):
    __tablename__ = "techno_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    vendor: Mapped[Optional[str]] = mapped_column(String(255))
    lifecycle: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(255))


class ActionPlanStatus(str, Enum):
    planned = "planifie"
    in_progress = "en_cours"
    done = "termine"
    blocked = "bloque"


class ActionPlan(TimestampMixin, Base):
    __tablename__ = "action_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[ActionPlanStatus] = mapped_column(
        SQLEnum(ActionPlanStatus), default=ActionPlanStatus.planned, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="action_plans")
    owner: Mapped[Optional[User]] = relationship(back_populates="action_plans")


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    external_reference: Mapped[Optional[str]] = mapped_column(String(255))

    application: Mapped[Application] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(back_populates="comments")


class TimelineEvent(TimestampMixin, Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    performed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    application: Mapped[Application] = relationship(back_populates="timelines")
    performed_by: Mapped[Optional[User]] = relationship("User")


class GlobalSetting(TimestampMixin, Base):
    __tablename__ = "global_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class CorrectiveAction(TimestampMixin, Base):
    __tablename__ = "actions_correctives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(255))

    application: Mapped[Application] = relationship("Application")
