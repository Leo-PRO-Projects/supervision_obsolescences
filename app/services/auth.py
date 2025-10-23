from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User, UserRole
from app.schemas.auth import AuthenticatedUser, LoginRequest, Token
from app.utils.security import create_access_token, get_password_hash, verify_password


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, credentials: LoginRequest) -> Token:
        user = self.db.query(User).filter(User.email == credentials.email).one_or_none()
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur désactivé")

        token, expires_at = create_access_token(str(user.id))
        user.last_login = datetime.now(timezone.utc)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return Token(access_token=token, expires_at=expires_at)

    def create_user(self, name: str, email: str, password: str, role: UserRole = UserRole.reader) -> User:
        existing = self.db.query(User).filter(User.email == email).one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail déjà enregistré")
        user = User(name=name, email=email, password_hash=get_password_hash(password), role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe actuel incorrect")
        user.password_hash = get_password_hash(new_password)
        self.db.add(user)
        self.db.commit()


async def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_current_active_user(user: User = Depends(get_current_user)) -> AuthenticatedUser:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur désactivé")
    return AuthenticatedUser.from_orm(user)
