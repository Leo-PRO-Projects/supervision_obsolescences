from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.entities import Application, Dependency, TechnologyLifecycle, TimelineEvent, UserRole
from app.schemas.entities import Dependency as DependencySchema
from app.schemas.entities import DependencyCreate, DependencyUpdate

router = APIRouter(prefix="/dependencies", tags=["dependencies"])


@router.post("/", response_model=DependencySchema, status_code=status.HTTP_201_CREATED)
async def create_dependency(
    payload: DependencyCreate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Dependency:
    application = db.get(Application, payload.application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application inconnue")
    dependency = Dependency(**payload.dict())
    if not dependency.normalized_name and dependency.name:
        catalog = (
            db.query(TechnologyLifecycle)
            .filter(TechnologyLifecycle.name.ilike(dependency.name))
            .one_or_none()
        )
        if catalog:
            dependency.normalized_name = catalog.name
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    event = TimelineEvent(
        application_id=dependency.application_id,
        entity_type="dependency",
        entity_id=dependency.id,
        event_type="create",
        description=f"Dépendance {dependency.name} ajoutée",
    )
    db.add(event)
    db.commit()
    return dependency


@router.put("/{dependency_id}", response_model=DependencySchema)
async def update_dependency(
    dependency_id: int,
    payload: DependencyUpdate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Dependency:
    dependency = db.get(Dependency, dependency_id)
    if not dependency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dépendance introuvable")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(dependency, field, value)
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    event = TimelineEvent(
        application_id=dependency.application_id,
        entity_type="dependency",
        entity_id=dependency.id,
        event_type="update",
        description=f"Dépendance {dependency.name} mise à jour",
    )
    db.add(event)
    db.commit()
    return dependency


@router.delete(
    "/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_dependency(
    dependency_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Response:
    dependency = db.get(Dependency, dependency_id)
    if not dependency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dépendance introuvable")
    dependency_name = dependency.name
    application_id = dependency.application_id
    db.delete(dependency)
    db.commit()
    event = TimelineEvent(
        application_id=application_id,
        entity_type="dependency",
        entity_id=dependency_id,
        event_type="delete",
        description=f"Dépendance {dependency_name} supprimée",
    )
    db.add(event)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
