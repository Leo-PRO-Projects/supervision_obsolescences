from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.entities import User, UserRole
from app.schemas.entities import User as UserSchema
from app.schemas.entities import UserCreate, UserUpdate
from app.utils.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserSchema])
async def list_users(
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> List[User]:
    return db.query(User).order_by(User.email).all()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> User:
    existing = db.query(User).filter(User.email == payload.email).one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail déjà enregistré")
    user = User(
        name=payload.name,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    updates = payload.dict(exclude_unset=True)
    if "password" in updates:
        user.password_hash = get_password_hash(updates.pop("password"))
    for field, value in updates.items():
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.admin)),
) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
