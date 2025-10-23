from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.entities import Application, TimelineEvent, UserRole, Version
from app.schemas.entities import Version as VersionSchema
from app.schemas.entities import VersionCreate, VersionUpdate

router = APIRouter(prefix="/versions", tags=["versions"])


@router.post("/", response_model=VersionSchema, status_code=status.HTTP_201_CREATED)
async def create_version(
    payload: VersionCreate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Version:
    application = db.get(Application, payload.application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application inconnue")
    version = Version(**payload.dict())
    db.add(version)
    db.commit()
    db.refresh(version)
    event = TimelineEvent(
        application_id=version.application_id,
        entity_type="version",
        entity_id=version.id,
        event_type="create",
        description=f"Version {version.number} créée",
    )
    db.add(event)
    db.commit()
    return version


@router.put("/{version_id}", response_model=VersionSchema)
async def update_version(
    version_id: int,
    payload: VersionUpdate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Version:
    version = db.get(Version, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version introuvable")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(version, field, value)
    db.add(version)
    db.commit()
    db.refresh(version)
    event = TimelineEvent(
        application_id=version.application_id,
        entity_type="version",
        entity_id=version.id,
        event_type="update",
        description=f"Version {version.number} mise à jour",
    )
    db.add(event)
    db.commit()
    return version


@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> None:
    version = db.get(Version, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version introuvable")
    version_number = version.number
    application_id = version.application_id
    db.delete(version)
    db.commit()
    event = TimelineEvent(
        application_id=application_id,
        entity_type="version",
        entity_id=version_id,
        event_type="delete",
        description=f"Version {version_number} supprimée",
    )
    db.add(event)
    db.commit()
