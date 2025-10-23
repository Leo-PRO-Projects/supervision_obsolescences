from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.entities import GlobalSetting, UserRole
from app.schemas.entities import GlobalSetting as GlobalSettingSchema
from app.schemas.entities import GlobalSettingCreate, GlobalSettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=List[GlobalSettingSchema])
async def list_settings(
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> List[GlobalSetting]:
    return db.query(GlobalSetting).order_by(GlobalSetting.key).all()


@router.post("/", response_model=GlobalSettingSchema, status_code=status.HTTP_201_CREATED)
async def create_setting(
    payload: GlobalSettingCreate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> GlobalSetting:
    setting = GlobalSetting(**payload.dict())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


@router.put("/{setting_id}", response_model=GlobalSettingSchema)
async def update_setting(
    setting_id: int,
    payload: GlobalSettingUpdate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> GlobalSetting:
    setting = db.get(GlobalSetting, setting_id)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paramètre introuvable")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(setting, field, value)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


@router.delete(
    "/{setting_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> Response:
    setting = db.get(GlobalSetting, setting_id)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paramètre introuvable")
    db.delete(setting)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
