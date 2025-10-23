from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.entities import (
    ActionPlanStatus,
    ApplicationStatus,
    CriticityLevel,
    DependencyCategory,
    NotificationType,
    RemediationStatus,
    UserRole,
)


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    name: str
    team: Optional[str]
    contact: Optional[str]


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str]
    team: Optional[str]
    contact: Optional[str]


class Project(ProjectBase, TimestampMixin):
    id: int


class ApplicationBase(BaseModel):
    name: str
    description: Optional[str]
    project_id: int
    owner: Optional[str]
    criticity: CriticityLevel = CriticityLevel.medium
    status: ApplicationStatus = ApplicationStatus.active


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    project_id: Optional[int]
    owner: Optional[str]
    criticity: Optional[CriticityLevel]
    status: Optional[ApplicationStatus]


class Application(ApplicationBase, TimestampMixin):
    id: int


class ApplicationDetail(Application):
    versions: List[Version]
    dependencies: List[Dependency]
    action_plans: List[ActionPlan]
    comments: List[Comment]


class VersionBase(BaseModel):
    application_id: int
    number: str
    end_of_support: Optional[date]
    end_of_contract: Optional[date]
    vendor_eos: Optional[date]
    remediation_status: RemediationStatus = RemediationStatus.not_planned
    comment: Optional[str]


class VersionCreate(VersionBase):
    pass


class VersionUpdate(BaseModel):
    application_id: Optional[int]
    number: Optional[str]
    end_of_support: Optional[date]
    end_of_contract: Optional[date]
    vendor_eos: Optional[date]
    remediation_status: Optional[RemediationStatus]
    comment: Optional[str]


class Version(VersionBase, TimestampMixin):
    id: int


class DependencyBase(BaseModel):
    application_id: int
    category: DependencyCategory
    name: str
    version: Optional[str]
    vendor: Optional[str]
    end_of_support: Optional[date]
    normalized_name: Optional[str]


class DependencyCreate(DependencyBase):
    pass


class DependencyUpdate(BaseModel):
    application_id: Optional[int]
    category: Optional[DependencyCategory]
    name: Optional[str]
    version: Optional[str]
    vendor: Optional[str]
    end_of_support: Optional[date]
    normalized_name: Optional[str]


class Dependency(DependencyBase, TimestampMixin):
    id: int


class NotificationBase(BaseModel):
    target_type: str
    target_id: int
    type: NotificationType
    recipients: List[EmailStr | str]
    status: str
    message: Optional[str]


class NotificationCreate(NotificationBase):
    pass


class Notification(NotificationBase, TimestampMixin):
    id: int
    sent_at: datetime

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.reader
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    role: Optional[UserRole]
    password: Optional[str]
    is_active: Optional[bool]


class User(UserBase, TimestampMixin):
    id: int
    last_login: Optional[datetime]


class TechnologyLifecycleBase(BaseModel):
    type: str
    name: str
    vendor: Optional[str]
    lifecycle: Optional[str]
    url: Optional[str]


class TechnologyLifecycleCreate(TechnologyLifecycleBase):
    pass


class TechnologyLifecycleUpdate(BaseModel):
    type: Optional[str]
    name: Optional[str]
    vendor: Optional[str]
    lifecycle: Optional[str]
    url: Optional[str]


class TechnologyLifecycle(TechnologyLifecycleBase, TimestampMixin):
    id: int


class ActionPlanBase(BaseModel):
    application_id: int
    title: str
    owner_id: Optional[int]
    due_date: Optional[date]
    status: ActionPlanStatus = ActionPlanStatus.planned
    notes: Optional[str]


class ActionPlanCreate(ActionPlanBase):
    pass


class ActionPlanUpdate(BaseModel):
    application_id: Optional[int]
    title: Optional[str]
    owner_id: Optional[int]
    due_date: Optional[date]
    status: Optional[ActionPlanStatus]
    notes: Optional[str]


class ActionPlan(ActionPlanBase, TimestampMixin):
    id: int


class CommentBase(BaseModel):
    application_id: int
    author_id: int
    content: str
    external_reference: Optional[str]


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: Optional[str]
    external_reference: Optional[str]


class Comment(CommentBase, TimestampMixin):
    id: int


class TimelineEventBase(BaseModel):
    application_id: int
    entity_type: str
    entity_id: int
    event_type: str
    description: str
    performed_by_id: Optional[int]


class TimelineEventCreate(TimelineEventBase):
    pass


class TimelineEvent(TimelineEventBase, TimestampMixin):
    id: int


class GlobalSettingBase(BaseModel):
    key: str
    value: str


class GlobalSettingCreate(GlobalSettingBase):
    pass


class GlobalSettingUpdate(BaseModel):
    value: Optional[str]


class GlobalSetting(GlobalSettingBase, TimestampMixin):
    id: int


class CorrectiveActionBase(BaseModel):
    application_id: int
    label: str
    reference: Optional[str]


class CorrectiveActionCreate(CorrectiveActionBase):
    pass


class CorrectiveActionUpdate(BaseModel):
    application_id: Optional[int]
    label: Optional[str]
    reference: Optional[str]


class CorrectiveAction(CorrectiveActionBase, TimestampMixin):
    id: int
