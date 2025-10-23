from __future__ import annotations

from typing import Iterable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_role
from app.core.database import get_db
from app.models.entities import Application, Notification, UserRole
from app.schemas.entities import Notification as NotificationSchema
from app.services.notifications import NotificationService, format_notification_html

router = APIRouter(prefix="/notifications", tags=["notifications"])


class EmailNotificationRequest(BaseModel):
    application_id: int
    version_id: Optional[int]
    dependency_id: Optional[int]
    recipients: List[EmailStr]
    subject: str


class TeamsNotificationRequest(BaseModel):
    application_id: int
    version_id: Optional[int]
    dependency_id: Optional[int]
    summary: str


@router.get("/", response_model=List[NotificationSchema])
async def list_notifications(
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> List[Notification]:
    return db.query(Notification).order_by(Notification.sent_at.desc()).all()


@router.post("/email", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED)
async def send_email_notification(
    payload: EmailNotificationRequest,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Notification:
    service = NotificationService(db)
    application = (
        db.query(Application)
        .options(joinedload(Application.project), joinedload(Application.versions), joinedload(Application.dependencies))
        .filter(Application.id == payload.application_id)
        .one_or_none()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application introuvable")

    version = None
    dependency = None
    if payload.version_id:
        version = next((v for v in application.versions if v.id == payload.version_id), None)
    if payload.dependency_id:
        dependency = next((d for d in application.dependencies if d.id == payload.dependency_id), None)

    body = format_notification_html(application, version, dependency)
    return service.send_email_notification("application", application.id, payload.recipients, payload.subject, body)


@router.post("/teams", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED)
async def send_teams_notification(
    payload: TeamsNotificationRequest,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Notification:
    service = NotificationService(db)
    application = (
        db.query(Application)
        .options(joinedload(Application.project))
        .filter(Application.id == payload.application_id)
        .one_or_none()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application introuvable")

    summary = payload.summary or f"Alerte obsolescence - {application.name}"
    return service.send_teams_notification("application", application.id, summary)
