from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.entities import User
from app.schemas.auth import AuthenticatedUser, ChangePasswordRequest, LoginRequest, Token
from app.services.auth import AuthService, get_auth_service, get_current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login(credentials: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> Token:
    return auth_service.authenticate(credentials)


@router.get("/me", response_model=AuthenticatedUser)
async def read_users_me(current_user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
    return current_user


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    auth_service.change_password(current_user, payload.current_password, payload.new_password)
    return {"status": "password_updated"}
