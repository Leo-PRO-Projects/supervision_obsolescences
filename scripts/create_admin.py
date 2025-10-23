from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.models.entities import User, UserRole
from app.utils.security import get_password_hash


def create_admin(name: str, email: str, password: str) -> None:
    with SessionLocal() as session:
        existing = session.query(User).filter(User.email == email).one_or_none()
        if existing:
            raise SystemExit("Un utilisateur avec cet e-mail existe déjà")
        user = User(name=name, email=email, role=UserRole.admin, password_hash=get_password_hash(password))
        session.add(user)
        session.commit()
        print(f"Administrateur créé: {email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Créer un utilisateur administrateur")
    parser.add_argument("--name", required=True, help="Nom complet")
    parser.add_argument("--email", required=True, help="Adresse e-mail")
    parser.add_argument("--password", required=True, help="Mot de passe")
    args = parser.parse_args()
    create_admin(args.name, args.email, args.password)
