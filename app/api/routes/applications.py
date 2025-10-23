from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.entities import Application, ApplicationStatus, CriticityLevel, Project, TimelineEvent, UserRole
from app.schemas.entities import Application as ApplicationSchema
from app.schemas.entities import ApplicationCreate, ApplicationDetail, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"])


def apply_filters(
    query,
    project_id: Optional[int] = None,
    criticity: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
):
    if project_id:
        query = query.filter(Application.project_id == project_id)
    if criticity:
        try:
            criticity_enum = CriticityLevel(criticity)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Criticité inconnue")
        query = query.filter(Application.criticity == criticity_enum)
    if status_filter:
        try:
            status_enum = ApplicationStatus(status_filter)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut inconnu")
        query = query.filter(Application.status == status_enum)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Application.name.ilike(like),
                Application.description.ilike(like),
                Application.owner.ilike(like),
            )
        )
    return query


@router.get("/", response_model=List[ApplicationSchema])
async def list_applications(
    project_id: Optional[int] = None,
    criticity: Optional[str] = Query(default=None, description="Criticité à filtrer"),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    search: Optional[str] = Query(default=None, description="Recherche plein texte"),
    db: Session = Depends(get_db),
    __: None = Depends(get_current_user),
) -> List[Application]:
    query = db.query(Application)
    query = apply_filters(query, project_id, criticity, status_filter, search)
    return query.order_by(Application.name).all()


@router.post("/", response_model=ApplicationSchema, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Application:
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Projet inconnu")
    application = Application(**payload.dict())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(get_current_user),
) -> Application:
    application = (
        db.query(Application)
        .options(
            joinedload(Application.versions),
            joinedload(Application.dependencies),
            joinedload(Application.action_plans),
            joinedload(Application.comments),
        )
        .filter(Application.id == application_id)
        .one_or_none()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application introuvable")
    return application


@router.put("/{application_id}", response_model=ApplicationSchema)
async def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Application:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application introuvable")

    changes = payload.dict(exclude_unset=True)
    for field, value in changes.items():
        setattr(application, field, value)

    db.add(application)
    db.commit()
    db.refresh(application)

    if changes:
        event = TimelineEvent(
            application_id=application.id,
            entity_type="application",
            entity_id=application.id,
            event_type="update",
            description=", ".join(f"{field} mis à jour" for field in changes.keys()),
        )
        db.add(event)
        db.commit()

    return application


@router.delete(
    "/{application_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> Response:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application introuvable")
    db.delete(application)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
