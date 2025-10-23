from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.entities import TechnologyLifecycle, UserRole
from app.schemas.entities import TechnologyLifecycle as TechnologyLifecycleSchema
from app.schemas.entities import TechnologyLifecycleCreate, TechnologyLifecycleUpdate

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/", response_model=List[TechnologyLifecycleSchema])
async def list_catalog(db: Session = Depends(get_db)) -> List[TechnologyLifecycle]:
    return db.query(TechnologyLifecycle).order_by(TechnologyLifecycle.name).all()


@router.post("/", response_model=TechnologyLifecycleSchema, status_code=status.HTTP_201_CREATED)
async def create_catalog_entry(
    payload: TechnologyLifecycleCreate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> TechnologyLifecycle:
    entry = TechnologyLifecycle(**payload.dict())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{entry_id}", response_model=TechnologyLifecycleSchema)
async def update_catalog_entry(
    entry_id: int,
    payload: TechnologyLifecycleUpdate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> TechnologyLifecycle:
    entry = db.get(TechnologyLifecycle, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(entry, field, value)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete(
    "/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_catalog_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Response:
    entry = db.get(TechnologyLifecycle, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")
    db.delete(entry)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
