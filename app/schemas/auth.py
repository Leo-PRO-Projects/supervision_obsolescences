from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenPayload(BaseModel):
    sub: str
    exp: int


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Adresse e-mail de connexion")
    password: str = Field(..., min_length=8, description="Mot de passe utilisateur")


class AuthenticatedUser(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
